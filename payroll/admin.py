from django.contrib import admin
from .models import SalaryRecord


@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ['slip_id', 'trainer', 'month_name', 'year', 'working_days', 'present_days', 'deduction', 'net_salary', 'generated_on']
    list_filter = ['year', 'month']
    search_fields = ['trainer__trainer_id', 'trainer__user__first_name', 'trainer__user__last_name']
