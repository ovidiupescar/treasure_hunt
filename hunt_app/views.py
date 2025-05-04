from django.shortcuts import render, get_object_or_404, redirect
from .models import Group, Question, Answer
from django.utils import timezone
import pytz
from django.db.models import Sum, Max, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.conf import settings  # To access project settings
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import unicodedata

def check_completion(group):
    """
    Check if a group has answered all questions and set completion_order if they have.
    Awards bonus points based on finishing order.
    Licu groups have 19 questions, Explo groups have 45 questions.
    Licu and Explo groups have separate completion order sequences.
    """
    # Get the required question count based on group type
    required_questions = 19 if group.licu else 45
    
    # Count how many unique questions this group has answered
    answered_questions = Answer.objects.filter(group=group).values('question').distinct().count()
    
    # If they've answered all required questions and don't already have a completion order
    if answered_questions >= required_questions and group.completion_order is None:
        # Find the highest current completion order for groups of the same type
        max_order = Group.objects.filter(licu=group.licu).aggregate(Max('completion_order'))['completion_order__max'] or 0
        # Set this group's completion order to the next number
        new_order = max_order + 1
        group.completion_order = new_order
        
        # Award bonus points based on finishing order and group type
        if group.licu:
            # Licu bonus points: 1st place = 30 points, decreasing by 5 points each position
            # Minimum bonus of 5 points
            bonus_points = max(30 - ((new_order - 1) * 5), 5)
        else:
            # Explo bonus points: 1st place = 60 points, decreasing by 10 points each position
            # Minimum bonus of 10 points
            bonus_points = max(60 - ((new_order - 1) * 10), 10)
            
        group.total_points += bonus_points
        
        group.save()
        
    return group.completion_order is not None

def question_view(request):
    def remove_diacritics(text: str) -> str:
        # Normalize the text to remove diacritics
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)
        )

    def check_answer(received, correct):
        if received == '':
            return False
        received_words = set(remove_diacritics(received).split())
        correct_words = set(remove_diacritics(correct).split())

        return received_words.issubset(correct_words)
    
    group_number = request.GET.get('group_number')
    question_number = request.GET.get('question_number')

    if not group_number or not question_number:
        return HttpResponse("Group number and question number are required.", status=400)

    group, created = Group.objects.get_or_create(group_number=group_number)
    
    # Set licu field based on group number
    group_num = int(group_number)
    if group_num <= 17:
        group.licu = True
    else:
        group.licu = False
    group.save()
    
    question = get_object_or_404(Question, question_number=question_number)
    answer = Answer.objects.filter(group=group, question=question).first()

    if question.question_type == 'dropdown':
        options = json.loads(question.options)
    else:
        options = None

    if request.method == 'POST':
        answer_text = request.POST.get('answer')
        is_correct = check_answer(answer_text.strip().lower(), question.correct_answer.strip().lower())

        points_earned = question.points if is_correct else 0

        if answer:
            # Update existing answer
            group.total_points -= answer.points_earned
            answer.answer_text = answer_text
            answer.points_earned = points_earned
            answer.timestamp = timezone.now()
            answer.save()
        else:
            # Create new answer
            answer = Answer.objects.create(
                group=group,
                question=question,
                answer_text=answer_text,
                points_earned=points_earned
            )
            group.answers_provided += 1

        group.total_points += points_earned
        group.save()
        
        # Check if the group has completed all questions
        has_completed = check_completion(group)

        return redirect(request.path + f'?group_number={group_number}&question_number={question_number}')

    context = {
        'group': group,
        'question': question,
        'answer': answer,
        'options': options,
    }
    return render(request, 'hunt_app/question.html', context)

@staff_member_required
def clear_data(request):
    if request.method == 'POST':
        # Check if password confirmation is provided
        confirmation_password = request.POST.get('confirmation_password')
        if confirmation_password == 'narcis':  # Set a secure password here
            Answer.objects.all().delete()
            Group.objects.update(total_points=0, answers_provided=0, completion_order=None)
            return redirect('admin_dashboard')
        else:
            # If password is incorrect, go back to confirmation page with error
            return render(request, 'hunt_app/clear_data.html', {'error': 'Incorrect password. Data not cleared.'})
    return render(request, 'hunt_app/clear_data.html')

def success_page(request):
    return render(request, 'hunt_app/success.html')

@staff_member_required
def reset_questions(request):
    if request.method == 'POST':  # This handles the confirmation
        # If user confirms to reset, do the actual reset
        if 'confirm' in request.POST:
            # Clear existing questions
            Question.objects.all().delete()
            
            # Load the pickle file from the correct path
            pickle_file_path = os.path.join(settings.BASE_DIR, 'hunt_app', 'data', 'intrebari.pkl')

            df = pd.read_pickle(pickle_file_path)

            try:
                df = pd.read_pickle(pickle_file_path)
            except FileNotFoundError:
                return render(request, 'error.html', {'message': 'Pickle file not found!'})

            for index, row in df.iterrows():
                if row['text']:
                    q_type = 'text'
                    opt = ''
                else:
                    q_type = 'dropdown'
                    opt = row['options']
                Question.objects.create(
                    question_location = row['Statie'].strip(),
                    question_text = row['Intrebare'].strip(),
                    question_type = q_type,
                    options = opt,
                    correct_answer = row['Raspuns Corect'].strip(),
                    points = 10
                )

            # Redirect to a success page after reset
            return redirect('success_page')

        else:
            # If user cancels, redirect to some other page (e.g., the home page)
            return redirect('admin_dashboard')

    # GET request - show confirmation page
    return render(request, 'hunt_app/reset_questions_confirmation.html')


@staff_member_required
def admin_dashboard(request):
    
    # Get the Bucharest timezone
    bucharest_tz = pytz.timezone('Europe/Bucharest')

    # Separate groups by type
    licu_groups = Group.objects.filter(licu=True).order_by('-total_points')
    explo_groups = Group.objects.filter(licu=False).order_by('-total_points')
    
    # Retrieve all answers
    all_answers = Answer.objects.order_by('timestamp')
    
    if all_answers.exists():
        # Get event start and end times from the data
        event_start_time = all_answers.first().timestamp.astimezone(bucharest_tz).replace(second=0, microsecond=0)
        event_end_time = all_answers.last().timestamp.astimezone(bucharest_tz).replace(second=0, microsecond=0)
    else:
        # If no answers yet, use current time as start and end time
        event_start_time = timezone.now().astimezone(bucharest_tz).replace(second=0, microsecond=0)
        event_end_time = event_start_time

    # Create time intervals at 1-minute increments
    time_labels = []
    current_time = event_start_time
    while current_time <= event_end_time:
        time_labels.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=1)
    
    # Generate colors dynamically if needed
    import random
    def get_random_color():
        return f'rgba({random.randint(0,255)}, {random.randint(0,255)}, {random.randint(0,255)}, 1)'
    
    # Create chart data for Licu groups
    licu_group_data = {}
    for group in licu_groups:
        # Initialize cumulative points list
        cumulative_answers = []
        total_answers = 0
        # Get all answers for the group, ordered by timestamp
        answers = Answer.objects.filter(group=group).order_by('timestamp')
        answer_index = 0
        num_answers = answers.count()
        
        # Loop through each time interval
        for time_label in time_labels:
            time_point = datetime.strptime(time_label, '%H:%M').replace(
                year=event_start_time.year,
                month=event_start_time.month,
                day=event_start_time.day,
                tzinfo=event_start_time.tzinfo  # Ensure timezone awareness
            )
            # Add points for answers up to the current time_point
            while (answer_index < num_answers and
                   answers[answer_index].timestamp.astimezone(bucharest_tz).replace(second=0, microsecond=0) <= time_point):
                total_answers += 1
                answer_index += 1
            cumulative_answers.append(total_answers)
        licu_group_data[group.group_number] = cumulative_answers
    
    # Create chart data for Explo groups
    explo_group_data = {}
    for group in explo_groups:
        # Initialize cumulative points list
        cumulative_answers = []
        total_answers = 0
        # Get all answers for the group, ordered by timestamp
        answers = Answer.objects.filter(group=group).order_by('timestamp')
        answer_index = 0
        num_answers = answers.count()
        
        # Loop through each time interval
        for time_label in time_labels:
            time_point = datetime.strptime(time_label, '%H:%M').replace(
                year=event_start_time.year,
                month=event_start_time.month,
                day=event_start_time.day,
                tzinfo=event_start_time.tzinfo  # Ensure timezone awareness
            )
            # Add points for answers up to the current time_point
            while (answer_index < num_answers and
                   answers[answer_index].timestamp.astimezone(bucharest_tz).replace(second=0, microsecond=0) <= time_point):
                total_answers += 1
                answer_index += 1
            cumulative_answers.append(total_answers)
        explo_group_data[group.group_number] = cumulative_answers
    
    # Prepare Licu chart data for Chart.js
    licu_chart_data = {
        'labels': time_labels,
        'datasets': []
    }
    
    for group_number, answers in licu_group_data.items():
        dataset = {
            'label': f'Group {group_number}',
            'data': answers,
            'fill': False,
            'borderColor': get_random_color(),
            'tension': 0.1
        }
        licu_chart_data['datasets'].append(dataset)
    
    # Prepare Explo chart data for Chart.js
    explo_chart_data = {
        'labels': time_labels,
        'datasets': []
    }
    
    for group_number, answers in explo_group_data.items():
        dataset = {
            'label': f'Group {group_number}',
            'data': answers,
            'fill': False,
            'borderColor': get_random_color(),
            'tension': 0.1
        }
        explo_chart_data['datasets'].append(dataset)
    
    context = {
        'licu_groups': licu_groups,
        'explo_groups': explo_groups,
        'licu_chart_data': json.dumps(licu_chart_data),
        'explo_chart_data': json.dumps(explo_chart_data),
    }
    return render(request, 'hunt_app/admin_dashboard.html', context)

@staff_member_required
def group_detail(request, group_number):
    """View to show all answers from a specific group."""
    group = get_object_or_404(Group, group_number=group_number)
    answers = Answer.objects.filter(group=group).order_by('question__question_number')
    
    # Get questions that haven't been answered
    answered_question_ids = answers.values_list('question__question_number', flat=True)
    unanswered_questions = Question.objects.exclude(question_number__in=answered_question_ids).order_by('question_number')
    
    context = {
        'group': group,
        'answers': answers,
        'unanswered_questions': unanswered_questions
    }
    return render(request, 'hunt_app/group_detail.html', context)

def home_view(request):
    return render(request, 'hunt_app/home.html')

@staff_member_required
def manage_group_names(request):
    """View to manage group names"""
    groups = Group.objects.all().order_by('group_number')
    
    if request.method == 'POST':
        # Get the group ID and new name from the form
        group_id = request.POST.get('group_id')
        group_name = request.POST.get('group_name')
        
        if group_id and group_name is not None:  # Allow empty names to clear the field
            group = get_object_or_404(Group, group_number=group_id)
            group.group_name = group_name
            group.save()
            return redirect('manage_group_names')
    
    # Separate groups by type
    licu_groups = Group.objects.filter(licu=True).order_by('group_number')
    explo_groups = Group.objects.filter(licu=False).order_by('group_number')
    
    context = {
        'licu_groups': licu_groups,
        'explo_groups': explo_groups,
    }
    return render(request, 'hunt_app/manage_group_names.html', context)