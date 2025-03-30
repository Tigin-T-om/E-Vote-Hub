from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Student, Department, HOD, ClassLeaderNomination, Officer, VotingSession, Candidate, Vote
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
                # Must be a student
                return redirect('student_home')

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
                    # Regular student user
                    messages.info(request, 'Welcome back!')
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('student_home')
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
        student.user.delete()  # This will also delete the student due to CASCADE
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
    
    context = {
        'student': student,
        'active_elections': 3,  # Replace with actual count
        'votes_cast': 5,        # Replace with actual count
        'pending_votes': 2,     # Replace with actual count
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
        
        if request.method == 'POST':
            nomination_text = request.POST.get('nomination_text')
            
            if existing_nomination:
                messages.error(request, 'You have already submitted a nomination.')
            else:
                try:
                    nomination = ClassLeaderNomination.objects.create(
                        student=student,
                        department=student.department,  # Explicitly set the department
                        nomination_text=nomination_text
                    )
                    messages.success(request, 'Your nomination has been submitted successfully!')
                    return redirect('student_nomination')
                except Exception as e:
                    messages.error(request, f'Error submitting nomination: {str(e)}')
        
        context = {
            'existing_nomination': existing_nomination,
            'student': student
        }
        return render(request, 'students/nomination.html', context)
    
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('student_home')

@login_required
def hod_nominations(request):
    # Check if user is HOD
    try:
        hod = request.user.hod
    except HOD.DoesNotExist:
        messages.error(request, 'Access denied. You are not authorized as a Head of Department.')
        return redirect('home')
    
    nominations = ClassLeaderNomination.objects.filter(
        department=hod.department
    ).select_related('student__user').order_by('-created_at')
    
    context = {
        'nominations': nominations,
        'department': hod.department
    }
    return render(request, 'hod/nominations.html', context)

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
    sort_by = request.GET.get('sort', 'date')
    
    # Base queryset
    nominations = ClassLeaderNomination.objects.filter(
        status='approved'
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
    
    # Apply sorting
    if sort_by == 'name':
        nominations = nominations.order_by('student__user__first_name', 'student__user__last_name')
    elif sort_by == 'department':
        nominations = nominations.order_by('department__name')
    else:  # default: date
        nominations = nominations.order_by('-reviewed_at')
    
    # Get all departments for filter dropdown
    departments = Department.objects.all()
    
    context = {
        'nominations': nominations,
        'departments': departments,
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
                
                # Create voting session with active status
                session = VotingSession.objects.create(
                    department_id=department_id,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=officer,
                    status='active'  # Set status to active when creating
                )
                
                # Add finalized candidates to the session
                finalized_nominations = ClassLeaderNomination.objects.filter(
                    department_id=department_id,
                    status='finalized'
                )
                
                for nomination in finalized_nominations:
                    # Determine gender based on student data
                    student_gender = nomination.student.gender
                    gender = 'male' if student_gender == 'M' else 'female'
                    
                    Candidate.objects.create(
                        nomination=nomination,
                        voting_session=session,
                        gender=gender
                    )
                
                messages.success(request, 'Voting session created successfully!')
                
            except Exception as e:
                messages.error(request, f'Error creating voting session: {str(e)}')
        
        elif action == 'verify_results':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                session.results_verified = True
                session.save()
                messages.success(request, 'Results verified successfully!')
            except Exception as e:
                messages.error(request, f'Error verifying results: {str(e)}')
        
        elif action == 'publish_results':
            try:
                session = VotingSession.objects.get(id=request.POST.get('session_id'))
                session.status = 'published'
                session.save()
                messages.success(request, 'Results published successfully!')
            except Exception as e:
                messages.error(request, f'Error publishing results: {str(e)}')
        
        elif action == 'remove_session':
            try:
                session_id = request.POST.get('session_id')
                session = VotingSession.objects.get(id=session_id)
                
                if session.can_be_removed():
                    session.status = 'cancelled'
                    session.save()
                    messages.success(request, 'Voting session has been removed successfully.')
                else:
                    messages.error(request, 'This session cannot be removed.')
                    
            except VotingSession.DoesNotExist:
                messages.error(request, 'Voting session not found.')
            except Exception as e:
                messages.error(request, f'Error removing session: {str(e)}')

    # Get active and completed sessions
    active_sessions = VotingSession.objects.filter(status='active')
    completed_sessions = VotingSession.objects.filter(
        status__in=['completed', 'published']
    ).order_by('-end_date')
    
    # Get departments for dropdown
    departments = Department.objects.all()

    context = {
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
    
    # Debug information
    current_time = timezone.now()
    
    # Get active voting session for student's department with debug checks
    active_session = VotingSession.objects.filter(
        department=student.department,
        status='active'
    ).first()
    
    if active_session:
        # Check time constraints
        if current_time < active_session.start_date:
            messages.info(request, 'Voting session exists but has not started yet.')
        elif current_time > active_session.end_date:
            messages.info(request, 'Voting session has ended.')
        else:
            messages.success(request, 'Voting session is currently active.')
    else:
        # Debug information about why no session was found
        all_sessions = VotingSession.objects.all()
        if all_sessions.exists():
            for session in all_sessions:
                if session.department != student.department:
                    messages.info(request, f'Found session for department: {session.department.name}')
                if session.status != 'active':
                    messages.info(request, f'Found session with status: {session.status}')
        else:
            messages.info(request, 'No voting sessions exist in the database.')

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
    if active_session:
        male_candidates = Candidate.objects.filter(
            voting_session=active_session,
            gender='male'
        ).select_related('nomination__student__user')
        female_candidates = Candidate.objects.filter(
            voting_session=active_session,
            gender='female'
        ).select_related('nomination__student__user')
    
    # Get published results
    published_results = VotingSession.objects.filter(
        department=student.department,
        status='published'
    ).order_by('-end_date')
    
    context = {
        'active_session': active_session,
        'has_voted': has_voted,
        'male_candidates': male_candidates,
        'female_candidates': female_candidates,
        'published_results': published_results,
        'student_department': student.department.name,  # Added for debugging
        'current_time': current_time,  # Added for debugging
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
                messages.success(request, 'Password changed successfully!')
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
                    student.profile_picture.delete()
                    student.profile_picture = None
                    student.save()
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