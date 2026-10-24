from django.contrib import admin
from .models import (
    Department, Course, TrainerProfile, StudentProfile,
    TrainerNotice, StudentDirectMessage, CourseResource
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'duration', 'fees', 'is_active', 'created_at']
    list_filter = ['department', 'is_active']
    search_fields = ['name', 'description']


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ['trainer_id', 'full_name', 'department', 'phone', 'email', 'monthly_salary', 'created_at']
    list_filter = ['department']
    search_fields = ['trainer_id', 'user__first_name', 'user__last_name', 'user__username', 'email', 'phone', 'technologies']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'name', 'course', 'trainer', 'department', 'phone', 'is_active', 'start_date']
    list_filter = ['course', 'department', 'is_active']
    search_fields = ['student_id', 'name', 'email', 'phone', 'user__username']


@admin.register(TrainerNotice)
class TrainerNoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'trainer', 'notice_type', 'from_date', 'to_date', 'is_active', 'created_at']
    list_filter = ['notice_type', 'is_active', 'created_at']
    search_fields = ['title', 'message', 'trainer__trainer_id', 'trainer__user__first_name']


@admin.register(StudentDirectMessage)
class StudentDirectMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'trainer', 'student', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'message', 'trainer__trainer_id', 'student__name', 'student__student_id']


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'resource_type', 'trainer', 'created_at']
    list_filter = ['resource_type', 'course', 'created_at']
    search_fields = ['title', 'description', 'notes_content']

