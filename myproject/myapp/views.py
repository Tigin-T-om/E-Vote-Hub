from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudentCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def home_view(request):
    return render(request, 'common/home.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on user role
            if user.is_superuser:  # Redirect all superusers to admin dashboard
                return redirect('admin_dashboard')
            elif hasattr(user, 'student'):
                return redirect('student_dashboard')
            else:
                messages.error(request, "Unauthorized role!")
                return redirect('home_view')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'common/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')  # Redirect to login page

def about_view(request):
    return render(request, 'common/about.html')

def contact_view(request):
    return render(request, 'common/contact.html')

@login_required
def create_student(request):
    if not request.user.is_superuser:  # Only admin can access
        messages.error(request, "Unauthorized access!")
        return redirect('home')

    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student account created successfully!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Error creating student. Please check the form.")

    else:
        form = StudentCreationForm()

    return render(request, 'admin/create_student.html', {'form': form})

@login_required
def student_dashboard(request):
    return render(request, 'student/dashboard.html')

@login_required
def admin_dashboard(request):
    return render(request, "admin/dashboard.html")  # Avoid conflict with Django's admin
