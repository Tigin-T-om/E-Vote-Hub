from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    
    # Admin routes
    path('admin/create-student/', views.create_student, name='create_student'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Student routes
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]
