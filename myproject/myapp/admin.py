from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Student
from django import forms

class StudentAdminForm(forms.ModelForm):
    username = forms.CharField(max_length=50, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Student
        fields = ['username', 'password', 'roll_number', 'name', 'email', 'is_nominated', 'has_voted']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email']
        )
        student = super().save(commit=False)
        student.user = user  # Link Student to User
        if commit:
            student.save()
        return student

class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('name', 'roll_number', 'email', 'has_voted', 'is_nominated')
    search_fields = ('name', 'roll_number', 'email')

admin.site.register(Student, StudentAdmin)
