from django import forms
from academy.models import TrainerProfile
import calendar
import datetime


class SalaryGenerationForm(forms.Form):
    trainer = forms.ModelChoiceField(
        queryset=TrainerProfile.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary_trainer_select'})
    )
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary_month_select'})
    )
    year = forms.IntegerField(
        initial=datetime.date.today().year,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'salary_year_input'})
    )
    working_days = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'working_days_input'})
    )
    max_paid_leaves = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=31,
        help_text="Configurable paid leaves allowance (default 0: all leaves are deducted).",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'max_paid_leaves_input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks/notes on slip...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default month to previous month
        today = datetime.date.today()
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        self.fields['month'].initial = prev_month
        self.fields['year'].initial = prev_year
