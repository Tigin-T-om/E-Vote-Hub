from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views.student_management, name='student_management'),
    path('admin/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/departments/', views.department_management, name='department_management'),
    path('admin/departments/delete/<int:department_id>/', views.delete_department, name='delete_department'),
    path('admin/hods/', views.hod_management, name='hod_management'),
    path('admin/hods/delete/<int:hod_id>/', views.delete_hod, name='delete_hod'),
    path('admin/officers/', views.officer_management, name='officer_management'),
    path('student/dashboard/', views.student_home, name='student_home'),
    path('hod/dashboard/', views.hod_home, name='hod_home'),
    # Nomination URLs
    path('student/nomination/', views.student_nomination, name='student_nomination'),
    path('hod/nominations/', views.hod_nominations, name='hod_nominations'),
    path('hod/nominations/<int:nomination_id>/review/', views.review_nomination, name='review_nomination'),
    # Officer URLs
    path('officer/dashboard/', views.officer_home, name='officer_home'),
    path('officer/nominations/', views.officer_nominations, name='officer_nominations'),
    path('officer/nominations/<int:nomination_id>/review/', views.officer_review_nomination, name='officer_review_nomination'),
    path('officer/nominations/<int:nomination_id>/finalize/', views.officer_finalize_nomination, name='officer_finalize_nomination'),
    path('officer/nominations/<int:nomination_id>/remove-finalized/', views.officer_remove_finalized, name='officer_remove_finalized'),
    path('officer/voting/', views.officer_voting_management, name='officer_voting_management'),
    path('student/voting/', views.student_voting, name='student_voting'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('api/eligible-students/<int:department_id>/', views.get_eligible_students, name='get_eligible_students'),
    path('officer/voting/results/', views.officer_voting_results, name='officer_voting_results'),
    path('hod/voting/results/', views.hod_voting_results, name='hod_voting_results'),
    path('hod/voting/results/<int:session_id>/', views.hod_view_session_results, name='hod_view_session_results'),
    path('student/voting/results/', views.student_voting_results, name='student_voting_results'),
    path('student/voting/results/<int:session_id>/', views.student_view_session_results, name='student_view_session_results'),
]