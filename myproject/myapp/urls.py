from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('admin/create-student/', views.create_student, name='create_student'),    
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]
