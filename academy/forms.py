from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import (
    Department, Course, TrainerProfile, StudentProfile,
    TrainerNotice, StudentDirectMessage, CourseResource,
    generate_student_id
)
import secrets
import string

User = get_user_model()


def validate_image_file(file):
    """Ensure uploaded file is an image and <= 5MB."""
    if not file:
        return file
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError("File size exceeds 5MB limit. Please upload a smaller image.")
    valid_mime_prefixes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
    if hasattr(file, 'content_type') and file.content_type not in valid_mime_prefixes:
        raise ValidationError("Unsupported file type. Please upload a JPEG, PNG, or WEBP image.")
    return file


def generate_secure_password(length=10):
    """Generates a secure random password like 'Dvx#83921'"""
    digits = ''.join(secrets.choice(string.digits) for _ in range(4))
    letters = ''.join(secrets.choice(string.ascii_letters) for _ in range(length - 5))
    special = secrets.choice('@#$%&*')
    return f"Dvx{special}{digits}{letters[:3]}"


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tech or Non-Tech'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Department overview'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'department', 'description', 'duration', 'fees', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Curriculum highlights'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6 Months or 90 Days'}),
            'fees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Course Fees in INR'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TrainerCreationForm(forms.Form):
    """Form used by Branch Head to create a new Trainer."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username (login ID)'}))
    password = forms.CharField(max_length=128, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Initial Password'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'trainer@devixacademy.com'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}))
    trainer_id = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TRN-003'}))
    department = forms.ModelChoiceField(queryset=Department.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}))
    monthly_salary = forms.DecimalField(max_digits=10, decimal_places=2, initial=0.00, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000.00'}))
    daily_working_hours = forms.DecimalField(max_digits=4, decimal_places=1, initial=4.0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': 'e.g. 2, 3, 5, 5.5'}))
    expected_start_time = forms.TimeField(initial='09:00', widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))
    technologies = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Java Full Stack, Python, Web Dev'}))
    experience_years = forms.DecimalField(max_digits=4, decimal_places=1, initial=0.0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5.5'}))
    experience_details = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Past companies and project experience'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Short professional bio'}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}))
    github = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}))
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/@...'}))
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or TrainerProfile.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user or trainer with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if TrainerProfile.objects.filter(phone=phone).exists() or User.objects.filter(phone=phone).exists():
            raise ValidationError("A user or trainer with this phone number already exists.")
        return phone

    def clean_trainer_id(self):
        trainer_id = self.cleaned_data['trainer_id'].strip().upper()
        if TrainerProfile.objects.filter(trainer_id=trainer_id).exists():
            raise ValidationError("A trainer with this Trainer ID already exists.")
        return trainer_id

    def clean_profile_picture(self):
        pic = self.cleaned_data.get('profile_picture')
        return validate_image_file(pic)


class TrainerUpdateForm(forms.ModelForm):
    """Branch Head editing Trainer profile and salary."""
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = TrainerProfile
        fields = [
            'department', 'monthly_salary', 'daily_working_hours', 'expected_start_time',
            'phone', 'email', 'profile_picture', 'bio', 'experience_years',
            'experience_details', 'technologies', 'linkedin', 'github',
            'instagram', 'youtube', 'twitter', 'website'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'daily_working_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'expected_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'technologies': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if TrainerProfile.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use by another trainer.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if TrainerProfile.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This phone number is already in use by another trainer.")
        return phone


class TrainerProfileEditForm(forms.ModelForm):
    """Trainer updating their own profile (ID and salary excluded)."""
    class Meta:
        model = TrainerProfile
        fields = [
            'phone', 'profile_picture', 'bio', 'technologies',
            'experience_years', 'experience_details', 'linkedin',
            'github', 'instagram', 'youtube', 'twitter', 'website'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'technologies': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Java, Python, Spring Boot'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class StudentCreationForm(forms.Form):
    """Form used by Trainer to enroll a Student. Auto-generates student ID and random password."""
    name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@gmail.com'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Mobile Number'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course'})
    )
    course_duration = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 6 Months'}))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    student_class = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Morning Batch A'}))
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}))
    github = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}))

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or StudentProfile.objects.filter(email__iexact=email).exists():
            raise ValidationError("A student or user with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if StudentProfile.objects.filter(phone=phone).exists() or User.objects.filter(phone=phone).exists():
            raise ValidationError("A student or user with this phone number already exists.")
        return phone

    def clean_profile_picture(self):
        pic = self.cleaned_data.get('profile_picture')
        return validate_image_file(pic)


class StudentBranchHeadUpdateForm(forms.ModelForm):
    """Branch Head editing student: full permissions including reassigning trainer and course."""
    class Meta:
        model = StudentProfile
        fields = [
            'name', 'email', 'phone', 'department', 'course',
            'trainer', 'course_duration', 'start_date', 'end_date',
            'student_class', 'profile_picture', 'linkedin', 'github',
            'instagram', 'twitter', 'website', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'trainer': forms.Select(attrs={'class': 'form-select'}),
            'course_duration': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StudentProfileEditForm(forms.ModelForm):
    """Student editing own profile (course, trainer, student_id, email, department are read-only)."""
    class Meta:
        model = StudentProfile
        fields = [
            'name', 'student_class', 'profile_picture',
            'linkedin', 'github', 'instagram', 'twitter', 'website'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control avatar-file-input', 'data-preview-target': 'avatarPreview'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class TrainerNoticeForm(forms.ModelForm):
    """Form for trainer to post Leave / Holiday / Class notices to their assigned students."""
    class Meta:
        model = TrainerNotice
        fields = ['notice_type', 'title', 'message', 'from_date', 'to_date']
        widgets = {
            'notice_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Trainer On Leave / Festival Holiday / Batch Notice'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Details regarding leave, backup schedule, or holiday message...'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class StudentDirectMessageForm(forms.ModelForm):
    """Form for trainer to send individual message/PDF/material/link to a specific student."""
    class Meta:
        model = StudentDirectMessage
        fields = ['student', 'subject', 'message', 'attachment', 'link_url']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Week 4 Project PDF / Reference Materials / Assignment'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your message or assignment instructions for this student...'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'link_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/... or https://drive.google.com/...'}),
        }

    def __init__(self, *args, **kwargs):
        trainer = kwargs.pop('trainer', None)
        super().__init__(*args, **kwargs)
        if trainer:
            self.fields['student'].queryset = trainer.students.filter(is_active=True).order_by('name')


class StudentReplyMessageForm(forms.ModelForm):
    """Form for a student to reply directly to their assigned mentor (1-on-1)."""
    class Meta:
        model = StudentDirectMessage
        fields = ['message', 'attachment', 'link_url']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your question, update or doubt directly to your mentor...'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'link_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/... or project link'}),
        }


class CourseResourceForm(forms.ModelForm):
    """Form for trainer to add learning resources (File/PDF, Link, Notes) tagged by Course & Department."""
    class Meta:
        model = CourseResource
        fields = ['department', 'course', 'title', 'description', 'resource_type', 'file', 'link_url', 'notes_content']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Django Complete Cheat Sheet & Architecture'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Brief description of what this material covers...'}),
            'resource_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_resource_type'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'link_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'notes_content': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 6, 'placeholder': 'Paste code snippets, terminal commands, or lecture notes...'}),
        }
