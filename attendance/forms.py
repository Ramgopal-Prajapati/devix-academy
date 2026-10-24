from django import forms
from django.core.exceptions import ValidationError
from .models import LeaveRequest, StudentLeaveRequest
import datetime


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_duration_type', 'half_day_period', 'from_date', 'to_date', 'reason']
        widgets = {
            'leave_duration_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_leave_duration_type'}),
            'half_day_period': forms.Select(attrs={'class': 'form-select', 'id': 'id_half_day_period'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Reason for leave application...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        leave_duration_type = cleaned_data.get('leave_duration_type')
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if leave_duration_type == 'HALF_DAY':
            # For half day, to_date equals from_date
            if from_date:
                cleaned_data['to_date'] = from_date
                to_date = from_date
            if not cleaned_data.get('half_day_period'):
                cleaned_data['half_day_period'] = 'FIRST_HALF'
        elif from_date and to_date:
            if to_date < from_date:
                raise ValidationError("End date cannot be earlier than start date.")
        return cleaned_data


class LeaveReviewForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['status', 'remark']
        widgets = {
            'status': forms.Select(
                choices=[('Approved', 'Approve Leave'), ('Rejected', 'Reject Leave')],
                attrs={'class': 'form-select'}
            ),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks or instructions...'}),
        }


class StudentLeaveRequestForm(forms.ModelForm):
    class Meta:
        model = StudentLeaveRequest
        fields = ['leave_type', 'from_date', 'to_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe reason for absence/leave...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')

        if from_date and to_date:
            if to_date < from_date:
                raise ValidationError("End date cannot be earlier than start date.")
        return cleaned_data


class StudentLeaveReviewForm(forms.ModelForm):
    class Meta:
        model = StudentLeaveRequest
        fields = ['status', 'trainer_remark']
        widgets = {
            'status': forms.Select(
                choices=[
                    ('Approved', 'Approve Leave (Will mark "Leave" in student attendance)'),
                    ('Rejected', 'Reject Leave (Will mark "Absent" if student does not attend)')
                ],
                attrs={'class': 'form-select'}
            ),
            'trainer_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional feedback or advice for student...'}),
        }
