from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudentCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# Create your views here.

def home_view(request):
    return render(request, 'common/home.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check user role and redirect accordingly
            if user.is_superuser:
                return redirect('admin_dashboard')  
            elif hasattr(user, 'student'):  # If user is linked to Student model
                return redirect('student_dashboard')
            else:
                messages.error(request, "Unauthorized role!")
                return redirect('home')

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'common/login.html')

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
            return redirect('admin_dashboard')  # Redirect after success
        else:
            messages.error(request, "Error creating student. Please check the form.")

    else:
        form = StudentCreationForm()

    return render(request, 'admin/create_student.html', {'form': form})


@login_required
def student_dashboard(request):
    return render(request, 'student/dashboard.html')