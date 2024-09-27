from django.shortcuts import render, get_object_or_404, redirect
from .models import Group, Question, Answer
from django.utils import timezone
import pytz
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.conf import settings  # To access project settings
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import unicodedata

def question_view(request):
    def remove_diacritics(text: str) -> str:
        # Normalize the text to remove diacritics
        return ''.join(
            c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)
        )

    def check_answer(received, correct):
        received_words = set(remove_diacritics(received).split())
        correct_words = set(remove_diacritics(correct).split())

        return received_words.issubset(correct_words)
    
    group_number = request.GET.get('group_number')
    question_number = request.GET.get('question_number')

    if not group_number or not question_number:
        return HttpResponse("Group number and question number are required.", status=400)

    group, created = Group.objects.get_or_create(group_number=group_number)
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
        Answer.objects.all().delete()
        Group.objects.update(total_points=0, answers_provided=0, completion_order=None)
        return redirect('admin_dashboard')
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

    groups = Group.objects.order_by('-total_points')
    
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
    
    # Prepare data for each group
    group_data = {}
    for group in groups:
        # Initialize cumulative points list
        cumulative_answers = []
        total_answers  = 0
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
        group_data[group.group_number] = cumulative_answers
    
    # Prepare data for Chart.js
    chart_data = {
        'labels': time_labels,
        'datasets': []
    }
    
    # Generate colors dynamically if needed
    import random
    def get_random_color():
        return f'rgba({random.randint(0,255)}, {random.randint(0,255)}, {random.randint(0,255)}, 1)'
    
    for group_number, answers in group_data.items():
        dataset = {
            'label': f'Group {group_number}',
            'data': answers,
            'fill': False,
            'borderColor': get_random_color(),
            'tension': 0.1
        }
        chart_data['datasets'].append(dataset)
    
    context = {
        'groups': groups,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'hunt_app/admin_dashboard.html', context)