from django.urls import path
from . import views

urlpatterns = [
    path('question/', views.question_view, name='question_view'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('clear_data/', views.clear_data, name='clear_data'),
]
