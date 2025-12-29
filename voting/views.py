from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def user_login(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            login(request, user)
            # Redirect based on role (We will build these pages later)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'hod':
                return redirect('admin:index') # Temp send HOD to admin panel
            else:
                return redirect('admin:index')
        else:
            messages.error(request, "Invalid Username or Password")
            
    return render(request, 'voting/login.html')