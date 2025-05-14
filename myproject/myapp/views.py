from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Student, Department, HOD, ClassLeaderNomination, Officer, VotingSession, Candidate, Vote, Notification
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from django.conf import settings
import random
import string
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import PasswordChangeForm
import os

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'contact.html')

def login_view(request):
    if request.user.is_authenticated:
        # Check user type and redirect accordingly
        if request.user.is_superuser or request.user.is_staff:
            return redirect('admin_dashboard')
        try:
            # Check if user is an officer
            officer = request.user.officer
            return redirect('officer_home')
        except Officer.DoesNotExist:
            try:
                # Check if user is HOD
                hod = request.user.hod
                return redirect('hod_home')
            except HOD.DoesNotExist:
                try:
                    # Check if user is a student
                    student = request.user.student
                    return redirect('student_home')
                except Student.DoesNotExist:
                    # If no profile exists, log them out and show error
                    logout(request)
                    messages.error(request, 'Your account is not properly set up. Please contact the administrator.')
                    return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            
            # Check user type and redirect accordingly
            if user.is_superuser:
                messages.info(request, 'Welcome back, Administrator!')
                return redirect('admin_dashboard')
            
            try:
                # Check if user is an officer
                officer = user.officer
                messages.info(request, 'Welcome back, Officer!')
                return redirect('officer_home')
            except Officer.DoesNotExist:
                try:
                    # Check if user is HOD
                    hod = user.hod
                    messages.info(request, f'Welcome back, Head of {hod.department.name} Department!')
                    return redirect('hod_home')
                except HOD.DoesNotExist:
                    try:
                        # Check if user is a student
                        student = user.student
                        messages.info(request, 'Welcome back!')
                        next_url = request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        return redirect('student_home')
                    except Student.DoesNotExist:
                        # If no profile exists, log them out and show error
                        logout(request)
                        messages.error(request, 'Your account is not properly set up. Please contact the administrator.')
                        return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_voters': 1234,  # Replace with actual count from database
        'active_elections': 5,  # Replace with actual count from database
        'total_votes': 8567,    # Replace with actual count from database
        'pending_actions': 3,   # Replace with actual count from database
        'recent_elections': [   # Replace with actual data from database
            {
                'title': 'Student Council Election 2024',
                'status': 'Active',
                'votes_cast': 1234,
                'time_ago': '3 days ago'
            },
            {
                'title': 'Class Representative Selection',
                'status': 'Completed',
                'votes_cast': 856,
                'time_ago': '1 week ago'
            }
        ],
        'recent_voters': [      # Replace with actual data from database
            {
                'name': 'John Doe',
                'action': 'Voted in Student Council Election',
                'time_ago': '2 hours ago'
            },
            {
                'name': 'Jane Smith',
                'action': 'Voted in Class Representative Selection',
                'time_ago': '5 hours ago'
            }
        ]
    }
    return render(request, 'admin/index.html', context)


@login_required
@user_passes_test(is_admin)
def student_management(request):
    students = Student.objects.all().select_related('user', 'department')
    departments = Department.objects.all()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        student_id = request.POST.get('student_id')
        department_id = request.POST.get('department')
        username = request.POST.get('username')
        gender = request.POST.get('gender')

        # Generate a secure random password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))

        try:
            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=temp_password  # Set the temporary password
            )
            
            # Get department
            department = get_object_or_404(Department, id=department_id)

            # Create Student
            student = Student.objects.create(
                user=user,
                student_id=student_id,
                department=department,
                gender=gender
            )

            # Send welcome email with credentials
            try:
                subject = 'Welcome to EVoteHub - Your Account Details'
                html_message = render_to_string('emails/welcome_email.html', {
                    'student': student,
                    'username': username,
                    'password': temp_password,  # Temporary password
                    'department': department.name
                })
                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in settings.py
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )

                logger.info(f"Welcome email sent successfully to {email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email to {email}: {str(e)}")
                messages.warning(request, f'Student account created, but email sending failed: {str(e)}')

            messages.success(request, f'Student account created successfully! Username: {username}')
        except Exception as e:
            messages.error(request, f'Error creating student account: {str(e)}')

        return redirect('student_management')

    context = {
        'students': students,
        'departments': departments
    }
    return render(request, 'admin/student_management.html', context)

@login_required
@user_passes_test(is_admin)
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    try:
        # Get the username before deleting
        username = student.user.username
        # Delete the student (this will cascade delete the user)
        student.delete()
        # Also delete any user with the same username to ensure complete cleanup
        User.objects.filter(username=username).delete()
        messages.success(request, 'Student deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
    return redirect('student_management')

@login_required
@user_passes_test(is_admin)
def department_management(request):
    departments = Department.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        
        try:
            Department.objects.create(
                name=name,
                code=code
            )
            messages.success(request, 'Department added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding department: {str(e)}')
        
        return redirect('department_management')
    
    context = {
        'departments': departments
    }
    return render(request, 'admin/department_management.html', context)

@login_required
@user_passes_test(is_admin)
def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    try:
        # Check if department has any students
        if department.student_set.exists():
            messages.error(request, 'Cannot delete department with existing students.')
        else:
            department.delete()
            messages.success(request, 'Department deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting department: {str(e)}')
    return redirect('department_management')

@login_required
def student_home(request):
    # Check if user is admin
    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin_dashboard')
    
    # Get student information
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('logout')
    
    # Get active voting sessions for student's department
    active_sessions = VotingSession.objects.filter(
        department=student.department,
        status__in=['scheduled', 'active']
    )
    
    # Count active elections
    active_elections = active_sessions.count()
    
    # Count votes cast by the student
    votes_cast = Vote.objects.filter(student=student).count()
    
    # Count pending votes (active sessions where student hasn't voted)
    pending_votes = 0
    for session in active_sessions:
        if session.status == 'active' and not Vote.objects.filter(student=student, voting_session=session).exists():
            pending_votes += 1
    
    # Get active sessions for display
    active_sessions_list = []
    for session in active_sessions:
        session.update_status_based_on_time()
        if session.status == 'active':
            active_sessions_list.append(session)
    
    # Get recent votes
    recent_votes = Vote.objects.filter(student=student).select_related('voting_session').order_by('-timestamp')[:5]
    
    # Get upcoming elections
    upcoming_sessions = VotingSession.objects.filter(
        department=student.department,
        status='scheduled',
        start_date__gt=timezone.now()
    ).order_by('start_date')[:5]
    
    context = {
        'student': student,
        'active_elections': active_elections,
        'votes_cast': votes_cast,
        'pending_votes': pending_votes,
        'active_sessions': active_sessions_list,
        'recent_votes': recent_votes,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'students/student_home.html', context)

@login_required
@user_passes_test(is_admin)
def hod_management(request):
    hods = HOD.objects.all().select_related('user', 'department')
    departments = Department.objects.filter(hod=None)  # Only show departments without HODs
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department_id = request.POST.get('department')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Create User with username and password
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Create HOD
            department = Department.objects.get(id=department_id)
            HOD.objects.create(
                user=user,
                department=department
            )
            
            messages.success(request, f'HOD account created successfully! Username: {username}')
        except Exception as e:
            messages.error(request, f'Error creating HOD account: {str(e)}')
        
        return redirect('hod_management')
    
    context = {
        'hods': hods,
        'departments': departments
    }
    return render(request, 'admin/hod_management.html', context)

@login_required
@user_passes_test(is_admin)
def delete_hod(request, hod_id):
    hod = get_object_or_404(HOD, id=hod_id)
    try:
        hod.user.delete()  # This will also delete the HOD due to CASCADE
        messages.success(request, 'HOD deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting HOD: {str(e)}')
    return redirect('hod_management')

@login_required
def hod_home(request):
    # Check if user is HOD
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')
    
    # Get department students
    department_students = Student.objects.filter(department=hod.department).select_related('user')
    
    context = {
        'hod': hod,
        'department': hod.department,
        'total_students': department_students.count(),
        'recent_students': department_students.order_by('-created_at')[:5],
        'active_elections': 2,  # Replace with actual count
        'completed_elections': 3,  # Replace with actual count
    }
    return render(request, 'hod/hod_home.html', context)

@login_required
def student_nomination(request):
    try:
        student = request.user.student
        existing_nomination = ClassLeaderNomination.objects.filter(student=student).first()
        
        # Check for active voting session
        active_session = VotingSession.objects.filter(
            department=student.department,
            status='active'
        ).first()
        
        if active_session:
            messages.warning(request, 'Nominations are currently closed as there is an active voting session.')
            return redirect('student_home')
        
        if request.method == 'POST':
            nomination_text = request.POST.get('nomination_text')
            marks = request.POST.get('marks')
            achievements = request.POST.get('achievements', '')
            
            if existing_nomination:
                messages.error(request, 'You have already submitted a nomination.')
            else:
                try:
                    # Validate marks
                    marks = float(marks)
                    if marks < 0 or marks > 10:
                        raise ValueError("Marks must be between 0 and 10")
                    
                    # Get the latest voting session for the department
                    latest_session = VotingSession.objects.filter(
                        department=student.department,
                        status='scheduled'
                    ).order_by('-start_date').first()
                    
                    nomination = ClassLeaderNomination.objects.create(
                        student=student,
                        department=student.department,
                        nomination_text=nomination_text,
                        marks=marks,
                        achievements=achievements,
                        election_cycle=latest_session
                    )
                    messages.success(request, 'Your nomination has been submitted successfully!')
                    return redirect('student_nomination')
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f'Error submitting nomination: {str(e)}')
        
        context = {
            'existing_nomination': existing_nomination,
            'student': student,
            'active_session': active_session
        }
        return render(request, 'students/nomination.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_home')

@login_required
def hod_nominations(request):
    """View for HOD to manage nominations"""
    if not hasattr(request.user, 'hod'):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    department = request.user.hod.department
    nominations = ClassLeaderNomination.objects.filter(student__department=department).order_by('-created_at')
    
    if request.method == 'POST':
        nomination_id = request.POST.get('nomination_id')
        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '')
        
        try:
            nomination = ClassLeaderNomination.objects.get(id=nomination_id)
            
            if action == 'approve':
                nomination.status = 'approved'
                message = f"Your nomination has been approved by the HOD. Feedback: {feedback}"
            elif action == 'reject':
                nomination.status = 'rejected'
                message = f"Your nomination has been rejected by the HOD. Feedback: {feedback}"
            
            nomination.save()
            
            # Create notification
            Notification.objects.create(
                student=nomination.student,
                nomination=nomination,
                message=message
            )
            
            messages.success(request, f'Nomination {action}d successfully!')
        except Exception as e:
            messages.error(request, f'Error processing nomination: {str(e)}')
        
        return redirect('hod_nominations')
    
    # Count statistics
    total_nominations = nominations.count()
    approved_nominations = nominations.filter(status='approved').count()
    rejected_nominations = nominations.filter(status='rejected').count()
    
    context = {
        'department': department,
        'nominations': nominations,
        'total_nominations': total_nominations,
        'approved_nominations': approved_nominations,
        'rejected_nominations': rejected_nominations,
    }
    
    return render(request, 'hod/nominations.html', context)

@login_required
def hod_approve_nomination(request, nomination_id):
    """View for HOD to approve a nomination"""
    if not hasattr(request.user, 'hod'):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    try:
        nomination = ClassLeaderNomination.objects.get(id=nomination_id)
        
        # Check if the nomination belongs to the HOD's department
        if nomination.student.department != request.user.hod.department:
            messages.error(request, 'You do not have permission to approve this nomination.')
            return redirect('hod_nominations')
        
        # Check if the nomination is already processed
        if nomination.status != 'pending':
            messages.warning(request, 'This nomination has already been processed.')
            return redirect('hod_nominations')
        
        # Process the approval
        if request.method == 'POST':
            feedback = request.POST.get('feedback', '')
            
            # Update the nomination
            nomination.status = 'approved'
            nomination.feedback = feedback
            nomination.reviewed_by = request.user.hod
            nomination.reviewed_at = timezone.now()
            nomination.save()
            
            # Create notification for student
            Notification.objects.create(
                student=nomination.student,
                nomination=nomination,
                message=f"Your nomination has been approved by the HOD. Feedback: {feedback}"
            )
            
            # Send notification to student
            messages.success(request, f'Nomination for {nomination.student.user.get_full_name()} has been approved and forwarded to the officer.')
            
            # Redirect back to HOD nominations page
            return redirect('hod_nominations')
        
    except ClassLeaderNomination.DoesNotExist:
        messages.error(request, 'Nomination not found.')
    
    return redirect('hod_nominations')

@login_required
def hod_reject_nomination(request, nomination_id):
    """View for HOD to reject a nomination"""
    if not hasattr(request.user, 'hod'):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    try:
        nomination = ClassLeaderNomination.objects.get(id=nomination_id)
        
        # Check if the nomination belongs to the HOD's department
        if nomination.student.department != request.user.hod.department:
            messages.error(request, 'You do not have permission to reject this nomination.')
            return redirect('hod_nominations')
        
        # Check if the nomination is already processed
        if nomination.status != 'pending':
            messages.warning(request, 'This nomination has already been processed.')
            return redirect('hod_nominations')
        
        # Process the rejection
        if request.method == 'POST':
            feedback = request.POST.get('feedback', '')
            
            if not feedback:
                messages.error(request, 'Feedback is required for rejection.')
                return redirect('hod_nominations')
            
            # Update the nomination
            nomination.status = 'rejected'
            nomination.feedback = feedback
            nomination.reviewed_by = request.user.hod
            nomination.reviewed_at = timezone.now()
            nomination.save()
            
            # Create notification for student
            Notification.objects.create(
                student=nomination.student,
                nomination=nomination,
                message=f"Your nomination has been rejected by the HOD. Feedback: {feedback}"
            )
            
            # Send notification to student
            messages.success(request, f'Nomination for {nomination.student.user.get_full_name()} has been rejected.')
            
            # Redirect back to nominations page
            return redirect('hod_nominations')
        
    except ClassLeaderNomination.DoesNotExist:
        messages.error(request, 'Nomination not found.')
    
    return redirect('hod_nominations')

@login_required
def review_nomination(request, nomination_id):
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')
    
    nomination = get_object_or_404(ClassLeaderNomination, id=nomination_id, department=hod.department)
    
    if nomination.status != 'pending':
        messages.warning(request, 'This nomination has already been reviewed.')
        return redirect('hod_nominations')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        feedback = request.POST.get('feedback')
        
        try:
            nomination.status = status
            nomination.feedback = feedback
            nomination.reviewed_by = hod
            nomination.reviewed_at = timezone.now()
            nomination.save()
            
            messages.success(request, 'Nomination has been reviewed successfully!')
            
            # If approved, notify officers (you can implement notification system later)
            if status == 'approved':
                messages.info(request, 'Nomination has been forwarded to officers for finalization.')
            
            return redirect('hod_nominations')
        except Exception as e:
            messages.error(request, f'Error reviewing nomination: {str(e)}')
    
    context = {
        'nomination': nomination
    }
    return render(request, 'hod/review_nomination.html', context)

@login_required
def officer_home(request):
    # Check if user is officer
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')
    
    # Get statistics
    pending_nominations = ClassLeaderNomination.objects.filter(status='approved').count()
    finalized_nominations = ClassLeaderNomination.objects.filter(status='finalized').count()
    total_departments = Department.objects.count()
    
    # Get recent nominations
    recent_nominations = ClassLeaderNomination.objects.filter(
        status__in=['approved', 'finalized']
    ).select_related('student__user', 'department').order_by('-updated_at')[:5]
    
    # Get department summary
    department_summary = []
    for department in Department.objects.all():
        summary = {
            'name': department.name,
            'pending_count': ClassLeaderNomination.objects.filter(
                department=department,
                status='approved'
            ).count(),
            'finalized_count': ClassLeaderNomination.objects.filter(
                department=department,
                status='finalized'
            ).count()
        }
        department_summary.append(summary)
    
    context = {
        'officer': officer,
        'pending_nominations': pending_nominations,
        'finalized_nominations': finalized_nominations,
        'total_departments': total_departments,
        'recent_nominations': recent_nominations,
        'department_summary': department_summary
    }
    return render(request, 'officer/officer_home.html', context)

@login_required
def officer_nominations(request):
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status_filter = request.GET.get('status', 'all')  # Add status filter
    sort_by = request.GET.get('sort', 'date')
    
    # Base queryset - include both approved and finalized nominations
    nominations = ClassLeaderNomination.objects.filter(
        status__in=['approved', 'finalized']
    ).select_related(
        'student__user',
        'department',
        'reviewed_by__user'
    )
    
    # Apply search
    if search_query:
        nominations = nominations.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query)
        )
    
    # Apply department filter
    if department_id:
        nominations = nominations.filter(department_id=department_id)
    
    # Apply status filter
    if status_filter != 'all':
        nominations = nominations.filter(status=status_filter)
    
    # Apply sorting
    if sort_by == 'name':
        nominations = nominations.order_by('student__user__first_name', 'student__user__last_name')
    elif sort_by == 'department':
        nominations = nominations.order_by('department__name')
    else:  # default: date
        nominations = nominations.order_by('-updated_at')
    
    # Get all departments for filter dropdown
    departments = Department.objects.all()
    
    context = {
        'nominations': nominations,
        'departments': departments,
        'search_query': search_query,
        'department_id': department_id,
        'status_filter': status_filter,
        'sort_by': sort_by
    }
    return render(request, 'officer/nominations.html', context)

@login_required
def officer_review_nomination(request, nomination_id):
    # Check if user is officer
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')
    
    # Get nomination
    nomination = get_object_or_404(ClassLeaderNomination, id=nomination_id)
    
    if nomination.status != 'approved':
        messages.warning(request, 'This nomination is not ready for finalization.')
        return redirect('officer_nominations')
    
    if request.method == 'POST':
        finalization_notes = request.POST.get('finalization_notes')
        
        try:
            nomination.status = 'finalized'
            nomination.finalization_notes = finalization_notes
            nomination.finalized_by = officer
            nomination.finalized_at = timezone.now()
            nomination.save()
            
            messages.success(request, 'Nomination has been finalized successfully!')
            return redirect('officer_nominations')
        except Exception as e:
            messages.error(request, f'Error finalizing nomination: {str(e)}')
    
    context = {
        'nomination': nomination
    }
    return render(request, 'officer/review_nomination.html', context)

@login_required
@user_passes_test(is_admin)
def officer_management(request):
    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Base queryset
    officers = Officer.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if search_query:
        officers = officers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if status_filter:
        is_active = status_filter == 'active'
        officers = officers.filter(user__is_active=is_active)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_officer':
            try:
                # Create user account
                user = User.objects.create_user(
                    username=request.POST.get('username'),
                    email=request.POST.get('email'),
                    password=request.POST.get('password'),
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name')
                )
                user.is_staff = True
                user.save()
                
                # Create officer profile
                Officer.objects.create(user=user)
                
                messages.success(request, 'Officer account created successfully!')
            except Exception as e:
                messages.error(request, f'Error creating officer account: {str(e)}')
        
        elif action == 'edit_officer':
            try:
                officer = Officer.objects.get(id=request.POST.get('officer_id'))
                user = officer.user
                
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.email = request.POST.get('email')
                user.save()
                
                messages.success(request, 'Officer details updated successfully!')
            except Officer.DoesNotExist:
                messages.error(request, 'Officer not found.')
            except Exception as e:
                messages.error(request, f'Error updating officer details: {str(e)}')
        
        elif action == 'toggle_status':
            try:
                officer = Officer.objects.get(id=request.POST.get('officer_id'))
                user = officer.user
                user.is_active = not user.is_active
                user.save()
                
                status = 'activated' if user.is_active else 'deactivated'
                messages.success(request, f'Officer account {status} successfully!')
            except Officer.DoesNotExist:
                messages.error(request, 'Officer not found.')
            except Exception as e:
                messages.error(request, f'Error changing officer status: {str(e)}')
    
    context = {
        'officers': officers,
        'search_query': search_query,
        'status_filter': status_filter
    }
    return render(request, 'admin/officer_management.html', context)

@login_required
def officer_finalize_nomination(request, nomination_id):
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')
    
    nomination = get_object_or_404(ClassLeaderNomination, id=nomination_id, status='approved')
    
    if request.method == 'POST':
        try:
            nomination.status = 'finalized'
            nomination.finalization_notes = request.POST.get('finalization_notes', '')
            nomination.finalized_by = officer
            nomination.finalized_at = timezone.now()
            nomination.save()
            
            messages.success(request, 'Nomination has been finalized successfully!')
        except Exception as e:
            messages.error(request, f'Error finalizing nomination: {str(e)}')
    
    return redirect('officer_nominations')

@login_required
def officer_voting_management(request):
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_session':
            try:
                department_id = request.POST.get('department')
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')
                
                # Get the department
                department = Department.objects.get(id=department_id)
                
                # Update status of existing sessions
                existing_sessions = VotingSession.objects.filter(
                    department=department,
                    status__in=['scheduled', 'active']
                )
                for session in existing_sessions:
                    session.update_status_based_on_time()
                
                # Check again after updating statuses
                existing_active = VotingSession.objects.filter(
                    department=department,
                    status__in=['scheduled', 'active']
                ).first()
                
                if existing_active:
                    messages.error(request, f'There is already a {existing_active.status} session for {department.name}.')
                    return redirect('officer_voting_management')
                
                # Create voting session with scheduled status
                session = VotingSession.objects.create(
                    department=department,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=officer,
                    status='scheduled',
                    election_cycle=None  # Explicitly set to None since it's nullable
                )
                
                # Get finalized nominations
                finalized_nominations = ClassLeaderNomination.objects.filter(
                    department=department,
                    status='finalized'
                ).select_related('student__user')
                
                candidates_created = 0
                for nomination in finalized_nominations:
                    try:
                        # Determine gender based on student data
                        student_gender = nomination.student.gender
                        gender = 'male' if student_gender == 'M' else 'female'
                        
                        # Create candidate for the session
                        Candidate.objects.create(
                            nomination=nomination,
                            voting_session=session,
                            gender=gender
                        )
                        candidates_created += 1
                    except Exception as e:
                        messages.warning(request, f'Error creating candidate for {nomination.student.user.get_full_name()}: {str(e)}')
                
                messages.success(request, f'Voting session scheduled successfully with {candidates_created} candidates!')
                
            except Exception as e:
                messages.error(request, f'Error creating voting session: {str(e)}')
        
        elif action == 'cancel_session':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                if session.status in ['scheduled', 'active']:
                    # Delete associated candidates first
                    Candidate.objects.filter(voting_session=session).delete()
                    session.status = 'cancelled'
                    session.save()
                    messages.success(request, 'Voting session has been cancelled successfully.')
                else:
                    messages.error(request, 'Only scheduled or active sessions can be cancelled.')
            except Exception as e:
                messages.error(request, f'Error cancelling session: {str(e)}')
        
        elif action == 'verify_results':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                if session.get_current_status() == 'completed':
                    session.status = 'verified'
                    session.save()
                    messages.success(request, 'Results verified successfully!')
                else:
                    messages.error(request, 'Only completed sessions can be verified.')
            except Exception as e:
                messages.error(request, f'Error verifying results: {str(e)}')
        
        elif action == 'publish_results':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                if session.status == 'verified':
                    session.status = 'published'
                    session.save()
                    messages.success(request, 'Results published successfully!')
                else:
                    messages.error(request, 'Only verified sessions can be published.')
            except Exception as e:
                messages.error(request, f'Error publishing results: {str(e)}')
        
        elif action == 'delete_session':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                if session.status in ['completed', 'published', 'cancelled']:
                    # Delete associated votes and candidates first
                    Vote.objects.filter(voting_session=session).delete()
                    Candidate.objects.filter(voting_session=session).delete()
                    session.delete()
                    messages.success(request, 'Voting session has been deleted successfully.')
                else:
                    messages.error(request, 'Only completed, published, or cancelled sessions can be deleted.')
            except Exception as e:
                messages.error(request, f'Error deleting session: {str(e)}')

    # Update status of all sessions based on current time
    all_sessions = VotingSession.objects.exclude(status__in=['verified', 'published', 'cancelled'])
    for session in all_sessions:
        session.update_status_based_on_time()

    # Get sessions by status with candidate counts
    scheduled_sessions = []
    for session in VotingSession.objects.filter(status='scheduled'):
        male_count = session.candidate_set.filter(gender='male').count()
        female_count = session.candidate_set.filter(gender='female').count()
        scheduled_sessions.append({
            'session': session,
            'male_count': male_count,
            'female_count': female_count
        })

    active_sessions = VotingSession.objects.filter(status='active').prefetch_related('candidate_set')
    completed_sessions = VotingSession.objects.filter(
        status__in=['completed', 'verified', 'published', 'cancelled']
    ).order_by('-end_date')
    
    # Get departments for dropdown
    departments = Department.objects.all()

    context = {
        'scheduled_sessions': scheduled_sessions,
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions,
        'departments': departments,
    }
    return render(request, 'officer/voting_management.html', context)

@login_required
def student_voting(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a student.')
        return redirect('home')
    
    # Get active voting session for student's department
    active_session = VotingSession.objects.filter(
        department=student.department,
        status__in=['scheduled', 'active']
    ).first()

    if active_session:
        # Update session status based on current time
        active_session.update_status_based_on_time()
        
        # Get current time in UTC
        current_time = timezone.now()
        
        # Check session status and display appropriate message
        if current_time < active_session.start_date:
            messages.info(request, f'Voting will start at {timezone.localtime(active_session.start_date).strftime("%B %d, %Y %I:%M %p")}')
            return redirect('student_home')
        elif current_time > active_session.end_date:
            messages.info(request, 'This voting session has ended.')
            return redirect('student_home')
    
    if request.method == 'POST' and active_session and active_session.status == 'active':
        # Check if student has already voted
        if Vote.objects.filter(student=student, voting_session=active_session).exists():
            messages.error(request, 'You have already voted in this session.')
            return redirect('student_voting')
            
        # Get selected candidates
        male_candidate_id = request.POST.get('male_candidate')
        female_candidate_id = request.POST.get('female_candidate')
        
        if not male_candidate_id or not female_candidate_id:
            messages.error(request, 'Please select both male and female representatives.')
            return redirect('student_voting')
            
        try:
            # Get candidate objects
            male_candidate = Candidate.objects.get(id=male_candidate_id, voting_session=active_session, gender='male')
            female_candidate = Candidate.objects.get(id=female_candidate_id, voting_session=active_session, gender='female')
            
            # Create vote
            Vote.objects.create(
                student=student,
                voting_session=active_session,
                male_candidate=male_candidate,
                female_candidate=female_candidate
            )
            
            messages.success(request, 'Your vote has been recorded successfully!')
            return redirect('student_voting')
            
        except Candidate.DoesNotExist:
            messages.error(request, 'Invalid candidate selection.')
        except Exception as e:
            messages.error(request, f'Error recording vote: {str(e)}')
    
    # Check if student has already voted
    has_voted = False
    if active_session:
        has_voted = Vote.objects.filter(
            student=student,
            voting_session=active_session
        ).exists()
    
    # Get candidates for active session
    male_candidates = []
    female_candidates = []
    if active_session and active_session.status == 'active':
        male_candidates = Candidate.objects.filter(
            voting_session=active_session,
            gender='male'
        ).select_related('nomination__student__user')
        female_candidates = Candidate.objects.filter(
            voting_session=active_session,
            gender='female'
        ).select_related('nomination__student__user')
    
    context = {
        'active_session': active_session,
        'has_voted': has_voted,
        'male_candidates': male_candidates,
        'female_candidates': female_candidates,
    }
    return render(request, 'students/voting.html', context)

@login_required
def student_profile(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_home')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Verify current password
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                # Change password
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('student_profile')
        
        elif 'profile_picture' in request.FILES:
            try:
                # Delete old profile picture if it exists
                if student.profile_picture:
                    student.profile_picture.delete()
                
                # Save new profile picture
                student.profile_picture = request.FILES['profile_picture']
                student.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'image_url': student.profile_picture.url
                    })
                else:
                    messages.success(request, 'Profile picture updated successfully!')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'Error updating profile picture: {str(e)}')
        
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest' and action == 'remove_profile_picture':
            try:
                if student.profile_picture:
                    # Store the file path before deletion
                    file_path = student.profile_picture.path
                    # Delete the file from storage
                    student.profile_picture.delete(save=False)
                    # Set the field to None
                    student.profile_picture = None
                    student.save()
                    
                    # Try to delete the file from the filesystem if it still exists
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass  # Ignore errors if file can't be deleted
                            
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        
        else:
            # Update profile details
            try:
                # Update user details
                request.user.first_name = request.POST.get('first_name')
                request.user.last_name = request.POST.get('last_name')
                request.user.email = request.POST.get('email')
                request.user.save()
                
                # Update student details
                student.gender = request.POST.get('gender')
                student.save()
                
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('student_profile')

    context = {
        'student': student
    }
    return render(request, 'students/profile.html', context)

@require_http_methods(["GET"])
def get_eligible_students(request, department_id):
    try:
        # Get finalized nominations for the department
        finalized_nominations = ClassLeaderNomination.objects.filter(
            department_id=department_id,
            status='finalized'
        )
        
        # Count male and female candidates
        male_count = finalized_nominations.filter(student__gender='M').count()
        female_count = finalized_nominations.filter(student__gender='F').count()
        
        return JsonResponse({
            'count': finalized_nominations.count(),
            'male_count': male_count,
            'female_count': female_count
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@login_required
def officer_remove_finalized(request, nomination_id):
    """View for officer to remove a finalized nomination"""
    if not hasattr(request.user, 'officer'):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    try:
        nomination = ClassLeaderNomination.objects.get(id=nomination_id)
        
        # Check if the nomination is finalized
        if nomination.status != 'finalized':
            messages.warning(request, 'Only finalized nominations can be removed.')
            return redirect('officer_nominations')
        
        # Process the removal
        if request.method == 'POST':
            removal_reason = request.POST.get('removal_reason', '')
            
            if not removal_reason:
                messages.error(request, 'Please provide a reason for removal.')
                return redirect('officer_nominations')
            
            # Store the student and department for notification
            student = nomination.student
            department = nomination.department
            
            # Delete the nomination
            nomination.delete()
            
            # Send notification to student
            messages.success(request, f'Nomination for {student.user.get_full_name()} has been removed.')
            
            # Redirect back to nominations page
            return redirect('officer_nominations')
        
    except ClassLeaderNomination.DoesNotExist:
        messages.error(request, 'Nomination not found.')
    
    return redirect('officer_nominations')

@login_required
def officer_voting_results(request):
    try:
        officer = request.user.officer
    except Officer.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as an Officer.')
        return redirect('home')

    # Get filter parameters
    department_id = request.GET.get('department')
    session_id = request.GET.get('session')

    # Get all departments for dropdown
    departments = Department.objects.all()

    # Initialize variables
    selected_department = None
    selected_session = None
    total_votes = 0
    male_candidates = []
    female_candidates = []

    if department_id:
        try:
            selected_department = Department.objects.get(id=department_id)
            # Get all completed and published sessions for the selected department
            sessions = VotingSession.objects.filter(
                department=selected_department,
                status__in=['completed', 'verified', 'published']
            ).order_by('-end_date')
        except Department.DoesNotExist:
            messages.error(request, 'Invalid department selected.')
            return redirect('officer_voting_results')
    else:
        # If no department selected, show all completed and published sessions
        sessions = VotingSession.objects.filter(
            status__in=['completed', 'verified', 'published']
        ).order_by('-end_date')

    if session_id:
        try:
            selected_session = VotingSession.objects.get(id=session_id)
            if selected_session.status not in ['completed', 'verified', 'published']:
                messages.error(request, 'Only completed, verified, or published sessions can be viewed.')
                return redirect('officer_voting_results')
            
            # Get all candidates for the session
            candidates = Candidate.objects.filter(
                voting_session=selected_session
            ).select_related(
                'nomination__student__user'
            )

            # Calculate total votes
            total_votes = Vote.objects.filter(voting_session=selected_session).count()

            # Calculate vote counts for each candidate
            for candidate in candidates:
                # Count votes where this candidate is either the male or female candidate
                vote_count = Vote.objects.filter(
                    Q(voting_session=selected_session) &
                    (Q(male_candidate=candidate) | Q(female_candidate=candidate))
                ).count()
                candidate.vote_count = vote_count

            # Order candidates by vote count
            candidates = sorted(candidates, key=lambda x: x.vote_count, reverse=True)

            # Separate male and female candidates
            male_candidates = [c for c in candidates if c.gender == 'male']
            female_candidates = [c for c in candidates if c.gender == 'female']

            # Calculate percentages for each candidate
            for candidate in candidates:
                if total_votes > 0:
                    candidate.percentage = (candidate.vote_count / total_votes) * 100
                else:
                    candidate.percentage = 0

        except VotingSession.DoesNotExist:
            messages.error(request, 'Invalid session selected.')
            return redirect('officer_voting_results')

    context = {
        'departments': departments,
        'sessions': sessions,
        'selected_department': selected_department.id if selected_department else None,
        'selected_session': selected_session.id if selected_session else None,
        'total_votes': total_votes,
        'male_candidates': male_candidates,
        'female_candidates': female_candidates,
    }
    return render(request, 'officer/voting_results.html', context)

@login_required
def hod_voting_results(request):
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')

    # Get published sessions for the HOD's department
    published_sessions = VotingSession.objects.filter(
        department=hod.department,
        status='published'
    ).order_by('-end_date')

    # Add vote counts and winners to each session
    for session in published_sessions:
        session.total_votes = Vote.objects.filter(voting_session=session).count()
        
        # Get male candidates with vote counts and marks
        male_candidates = list(Candidate.objects.filter(
            voting_session=session,
            gender='male'
        ).select_related('nomination__student__user', 'nomination'))
        
        for candidate in male_candidates:
            candidate.vote_count = Vote.objects.filter(
                voting_session=session,
                male_candidate=candidate
            ).count()
            candidate.marks = candidate.nomination.marks
        
        # Get female candidates with vote counts and marks
        female_candidates = list(Candidate.objects.filter(
            voting_session=session,
            gender='female'
        ).select_related('nomination__student__user', 'nomination'))
        
        for candidate in female_candidates:
            candidate.vote_count = Vote.objects.filter(
                voting_session=session,
                female_candidate=candidate
            ).count()
            candidate.marks = candidate.nomination.marks

        # Determine male winner
        if male_candidates:
            male_candidates.sort(key=lambda x: (-x.vote_count, -x.marks))
            session.male_winner = male_candidates[0]
            # Check for ties
            if len(male_candidates) > 1 and male_candidates[0].vote_count == male_candidates[1].vote_count:
                session.male_winner.tied = True

        # Determine female winner
        if female_candidates:
            female_candidates.sort(key=lambda x: (-x.vote_count, -x.marks))
            session.female_winner = female_candidates[0]
            # Check for ties
            if len(female_candidates) > 1 and female_candidates[0].vote_count == female_candidates[1].vote_count:
                session.female_winner.tied = True

    context = {
        'published_sessions': published_sessions,
        'department': hod.department
    }
    return render(request, 'hod/voting_results.html', context)

@login_required
def hod_view_session_results(request, session_id):
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')

    try:
        session = VotingSession.objects.get(
            id=session_id,
            department=hod.department,
            status='published'
        )
    except VotingSession.DoesNotExist:
        messages.error(request, 'Session not found or not published.')
        return redirect('hod_voting_results')

    # Get all candidates for the session
    candidates = Candidate.objects.filter(
        voting_session=session
    ).select_related(
        'nomination__student__user'
    )

    # Calculate total votes
    total_votes = Vote.objects.filter(voting_session=session).count()

    # Calculate vote counts for each candidate
    for candidate in candidates:
        vote_count = Vote.objects.filter(
            Q(voting_session=session) &
            (Q(male_candidate=candidate) | Q(female_candidate=candidate))
        ).count()
        candidate.vote_count = vote_count
        if total_votes > 0:
            candidate.percentage = (vote_count / total_votes) * 100
        else:
            candidate.percentage = 0

    # Order candidates by vote count
    candidates = sorted(candidates, key=lambda x: x.vote_count, reverse=True)

    # Separate male and female candidates
    male_candidates = [c for c in candidates if c.gender == 'male']
    female_candidates = [c for c in candidates if c.gender == 'female']

    context = {
        'session': session,
        'total_votes': total_votes,
        'male_candidates': male_candidates,
        'female_candidates': female_candidates
    }
    return render(request, 'hod/session_results.html', context)

@login_required
def student_voting_results(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a student.')
        return redirect('home')

    # Get published sessions for the student's department
    published_sessions = VotingSession.objects.filter(
        department=student.department,
        status='published'
    ).order_by('-end_date')

    # Add vote counts and winners to each session
    for session in published_sessions:
        session.total_votes = Vote.objects.filter(voting_session=session).count()
        
        # Get male candidates with vote counts and marks
        male_candidates = list(Candidate.objects.filter(
            voting_session=session,
            gender='male'
        ).select_related('nomination__student__user', 'nomination'))
        
        for candidate in male_candidates:
            candidate.vote_count = Vote.objects.filter(
                voting_session=session,
                male_candidate=candidate
            ).count()
            candidate.marks = candidate.nomination.marks
        
        # Get female candidates with vote counts and marks
        female_candidates = list(Candidate.objects.filter(
            voting_session=session,
            gender='female'
        ).select_related('nomination__student__user', 'nomination'))
        
        for candidate in female_candidates:
            candidate.vote_count = Vote.objects.filter(
                voting_session=session,
                female_candidate=candidate
            ).count()
            candidate.marks = candidate.nomination.marks
        
        # Find winners considering votes, marks, and alphabetical order
        if male_candidates:
            # Sort by votes first, then by marks, then alphabetically by name
            male_candidates.sort(key=lambda c: (-c.vote_count, -c.marks, c.full_name))
            session.male_winner = male_candidates[0]
            # Check if there's a tie in votes
            tied_votes = [c for c in male_candidates if c.vote_count == session.male_winner.vote_count]
            if len(tied_votes) > 1:
                # If there's a tie in votes, check marks
                tied_marks = [c for c in tied_votes if c.marks == session.male_winner.marks]
                if len(tied_marks) > 1:
                    # If there's a tie in both votes and marks, winner is determined by alphabetical order
                    session.male_winner.tied = True
                else:
                    session.male_winner.tied = False
            else:
                session.male_winner.tied = False
            
        if female_candidates:
            # Sort by votes first, then by marks, then alphabetically by name
            female_candidates.sort(key=lambda c: (-c.vote_count, -c.marks, c.full_name))
            session.female_winner = female_candidates[0]
            # Check if there's a tie in votes
            tied_votes = [c for c in female_candidates if c.vote_count == session.female_winner.vote_count]
            if len(tied_votes) > 1:
                # If there's a tie in votes, check marks
                tied_marks = [c for c in tied_votes if c.marks == session.female_winner.marks]
                if len(tied_marks) > 1:
                    # If there's a tie in both votes and marks, winner is determined by alphabetical order
                    session.female_winner.tied = True
                else:
                    session.female_winner.tied = False
            else:
                session.female_winner.tied = False

    context = {
        'published_sessions': published_sessions,
        'department': student.department
    }
    return render(request, 'students/voting_results.html', context)

@login_required
def student_view_session_results(request, session_id):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a student.')
        return redirect('home')

    try:
        session = VotingSession.objects.get(
            id=session_id,
            department=student.department,
            status='published'
        )
    except VotingSession.DoesNotExist:
        messages.error(request, 'Session not found or not published.')
        return redirect('student_voting_results')

    # Get all candidates for the session
    candidates = Candidate.objects.filter(
        voting_session=session
    ).select_related(
        'nomination__student__user',
        'nomination'  # Add this to include nomination details
    )

    # Calculate total votes
    total_votes = Vote.objects.filter(voting_session=session).count()

    # Calculate vote counts and prepare candidate data
    candidate_data = []
    for candidate in candidates:
        vote_count = Vote.objects.filter(
            Q(voting_session=session) &
            (Q(male_candidate=candidate) | Q(female_candidate=candidate))
        ).count()
        
        candidate_data.append({
            'candidate': candidate,
            'vote_count': vote_count,
            'marks': candidate.nomination.marks,  # Include marks for tiebreaker
            'percentage': (vote_count / total_votes * 100) if total_votes > 0 else 0
        })

    # Sort candidates by votes (primary) and marks (secondary for tiebreaker)
    candidate_data.sort(key=lambda x: (-x['vote_count'], -x['marks']))

    # Group candidates by gender
    male_candidates = [data for data in candidate_data if data['candidate'].gender == 'male']
    female_candidates = [data for data in candidate_data if data['candidate'].gender == 'female']

    # Add ranking and tie information
    def add_ranking_info(candidates_list):
        current_rank = 1
        current_votes = None
        current_marks = None
        
        for i, data in enumerate(candidates_list):
            if current_votes != data['vote_count']:
                # Different vote count means new rank
                current_rank = i + 1
                current_votes = data['vote_count']
                current_marks = data['marks']
                data['tied'] = False
            elif current_votes == data['vote_count']:
                # Same vote count, check marks
                if current_marks == data['marks']:
                    # True tie (same votes and marks)
                    data['tied'] = True
                else:
                    # Different marks breaks the tie
                    data['tied'] = False
                    current_rank = i + 1
                    current_marks = data['marks']
            data['rank'] = current_rank

    add_ranking_info(male_candidates)
    add_ranking_info(female_candidates)

    context = {
        'session': session,
        'total_votes': total_votes,
        'male_candidates': male_candidates,
        'female_candidates': female_candidates
    }
    return render(request, 'students/session_results.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            # Redirect based on user type
            if hasattr(request.user, 'student'):
                return redirect('student_home')
            elif hasattr(request.user, 'officer'):
                return redirect('officer_home')
            elif hasattr(request.user, 'hod'):
                return redirect('hod_home')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Determine the base template based on user type
    if hasattr(request.user, 'student'):
        base_template = 'students/base_student.html'
    elif hasattr(request.user, 'officer'):
        base_template = 'officer/base_officer.html'
    elif hasattr(request.user, 'hod'):
        base_template = 'hod/base_hod.html'
    else:
        base_template = 'base.html'
    
    return render(request, 'change_password.html', {
        'form': form,
        'base_template': base_template
    })

@login_required
def hod_department_students(request):
    """View for HOD to see all students in their department"""
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')
    
    # Get all students in the HOD's department
    students = Student.objects.filter(
        department=hod.department
    ).select_related('user').order_by('user__first_name', 'user__last_name')
    
    context = {
        'students': students,
        'department': hod.department
    }
    return render(request, 'hod/department_students.html', context)

@login_required
def hod_profile(request):
    """View for HOD to manage their profile"""
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')

    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            try:
                # Delete old profile picture if it exists
                if hod.profile_picture:
                    hod.profile_picture.delete()
                
                # Save new profile picture
                hod.profile_picture = request.FILES['profile_picture']
                hod.save()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'image_url': hod.profile_picture.url
                    })
                else:
                    messages.success(request, 'Profile picture updated successfully!')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'Error updating profile picture: {str(e)}')
        
        # Handle profile information update
        elif 'first_name' in request.POST:
            try:
                # Update user details
                request.user.first_name = request.POST.get('first_name')
                request.user.last_name = request.POST.get('last_name')
                request.user.email = request.POST.get('email')
                request.user.save()
                
                if is_ajax:
                    return JsonResponse({'success': True})
                else:
                    messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'Error updating profile: {str(e)}')
        
        # Handle password change
        elif 'current_password' in request.POST:
            try:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Verify current password
                if not request.user.check_password(current_password):
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'error': 'Current password is incorrect'
                        })
                    else:
                        messages.error(request, 'Current password is incorrect')
                        return redirect('hod_profile')
                
                # Verify new passwords match
                if new_password != confirm_password:
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'error': 'New passwords do not match'
                        })
                    else:
                        messages.error(request, 'New passwords do not match')
                        return redirect('hod_profile')
                
                # Change password
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                
                if is_ajax:
                    return JsonResponse({'success': True})
                else:
                    messages.success(request, 'Password changed successfully!')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'Error changing password: {str(e)}')
        
        if not is_ajax:
            return redirect('hod_profile')
    
    context = {
        'hod': hod
    }
    return render(request, 'hod/profile.html', context)

@login_required
def hod_remove_nomination(request, nomination_id):
    """View for HOD to remove a rejected nomination"""
    if not hasattr(request.user, 'hod'):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    try:
        nomination = ClassLeaderNomination.objects.get(id=nomination_id)
        
        # Check if the nomination belongs to the HOD's department
        if nomination.student.department != request.user.hod.department:
            messages.error(request, 'You do not have permission to remove this nomination.')
            return redirect('hod_nominations')
        
        # Check if the nomination is rejected
        if nomination.status != 'rejected':
            messages.warning(request, 'Only rejected nominations can be removed.')
            return redirect('hod_nominations')
        
        # Delete the nomination
        nomination.delete()
        messages.success(request, f'Nomination for {nomination.student.user.get_full_name()} has been removed. The student can now reapply.')
        
    except ClassLeaderNomination.DoesNotExist:
        messages.error(request, 'Nomination not found.')
    
    return redirect('hod_nominations')

@login_required
def student_notifications(request):
    """View for students to see their notifications"""
    if not hasattr(request.user, 'student'):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    student = request.user.student
    notifications = Notification.objects.filter(student=student).select_related('nomination')
    
    # Mark notifications as read when viewing
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'students/notifications.html', context)

@login_required
def withdraw_nomination(request):
    """View for students to withdraw their nomination before HOD review"""
    if not hasattr(request.user, 'student'):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    try:
        nomination = ClassLeaderNomination.objects.get(student=request.user.student)
        
        # Check if the nomination is still pending
        if nomination.status != 'pending':
            messages.error(request, 'You can only withdraw nominations that are pending HOD review.')
            return redirect('student_nomination')
        
        # Delete the nomination
        nomination.delete()
        messages.success(request, 'Your nomination has been withdrawn successfully. You can submit a new nomination if you wish.')
        
    except ClassLeaderNomination.DoesNotExist:
        messages.error(request, 'No nomination found to withdraw.')
    
    return redirect('student_nomination')

@login_required
@user_passes_test(is_admin)
def bulk_delete_students(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        if not year:
            messages.error(request, 'Please select a year to delete students.')
            return redirect('student_management')
        
        try:
            # Get all students created in the selected year
            students = Student.objects.filter(created_at__year=year)
            count = students.count()
            
            if count == 0:
                messages.warning(request, f'No students found created in {year}.')
                return redirect('student_management')
            
            # Get all usernames before deletion
            usernames = [student.user.username for student in students]
            
            # Delete all students (this will cascade delete their user accounts)
            students.delete()
            
            # Also delete any remaining users with the same usernames
            User.objects.filter(username__in=usernames).delete()
            
            messages.success(request, f'Successfully deleted {count} students created in {year}.')
        except Exception as e:
            messages.error(request, f'Error deleting students: {str(e)}')
    
    return redirect('student_management')