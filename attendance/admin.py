from django.contrib import admin
from .models import Attendance, TrainerAttendance, LeaveRequest


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'marked_by', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['student__name', 'student__student_id', 'marked_by__username']


@admin.register(TrainerAttendance)
class TrainerAttendanceAdmin(admin.ModelAdmin):
    list_display = ['trainer', 'date', 'status', 'check_in', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['trainer__trainer_id', 'trainer__user__first_name', 'trainer__user__last_name']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['trainer', 'from_date', 'to_date', 'total_days', 'status', 'reviewed_by', 'applied_on']
    list_filter = ['status', 'from_date']
    search_fields = ['trainer__trainer_id', 'trainer__user__first_name', 'reason', 'remark']
