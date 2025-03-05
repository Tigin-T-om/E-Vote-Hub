from django.urls import path
from .views import home_view, login_view, register_view, about_view, contact_view  # Import login view

urlpatterns = [
    path('', home_view, name='home'),  # Home page
    path('login/', login_view, name='login'),  # Login page
    path('register/', register_view, name='register'),
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
]
