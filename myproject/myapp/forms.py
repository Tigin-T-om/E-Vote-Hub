from django import forms
from django.contrib.auth.models import User
from .models import Student

class StudentCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=50, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Student
        fields = ['roll_number', 'name', 'email']

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
