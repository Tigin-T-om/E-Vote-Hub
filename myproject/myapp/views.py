from django.shortcuts import render

# Create your views here.

def home_view(request):
    return render(request, 'common/home.html')


def login_view(request):
    return render(request, 'common/login.html')  # Ensure login.html exists

def register_view(request):
    return render(request, 'common/register.html')

def about_view(request):
    return render(request, 'common/register.html')

def contact_view(request):
    return render(request, 'common/contact.html')