from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('student/dashboard/', views.user_login, name='student_dashboard'), # Placeholder
]