from django.shortcuts import render, get_object_or_404, redirect
from .models import Group, Question, Answer
from django.utils import timezone
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import json

def question_view(request):
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
        is_correct = (answer_text.strip().lower() == question.correct_answer.strip().lower())
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
def admin_dashboard(request):
    groups = Group.objects.all()
    context = {
        'groups': groups,
    }
    return render(request, 'hunt_app/admin_dashboard.html', context)

@staff_member_required
def clear_data(request):
    if request.method == 'POST':
        Answer.objects.all().delete()
        Group.objects.update(total_points=0, answers_provided=0, completion_order=None)
        return redirect('admin_dashboard')
    return render(request, 'hunt_app/clear_data.html')
