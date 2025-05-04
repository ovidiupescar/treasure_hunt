from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('question/', views.question_view, name='question_view'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('group/<int:group_number>/', views.group_detail, name='group_detail'),
    path('clear_data/', views.clear_data, name='clear_data'),
    path('reset_questions/', views.reset_questions, name='reset_questions'),
    path('success/', views.success_page, name='success_page'),
]
