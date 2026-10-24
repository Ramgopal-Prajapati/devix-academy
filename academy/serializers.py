from rest_framework import serializers
from .models import Department, Course, TrainerProfile, StudentProfile


class DepartmentSerializer(serializers.ModelSerializer):
    course_count = serializers.IntegerField(source='courses.count', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'course_count', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'department', 'department_name', 'description', 'duration', 'fees', 'is_active', 'created_at']


class TrainerProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    photo_url = serializers.CharField(source='profile_picture_url', read_only=True)
    technologies_list = serializers.ListField(source='get_technologies_list', read_only=True)

    class Meta:
        model = TrainerProfile
        fields = [
            'id', 'trainer_id', 'username', 'full_name', 'phone', 'email',
            'department', 'department_name', 'photo_url', 'bio',
            'experience_years', 'experience_details', 'technologies',
            'technologies_list', 'linkedin', 'github', 'instagram',
            'youtube', 'twitter', 'website', 'monthly_salary', 'created_at'
        ]
        read_only_fields = ['trainer_id', 'monthly_salary']


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    trainer_name = serializers.CharField(source='trainer.full_name', read_only=True)
    photo_url = serializers.CharField(source='profile_picture_url', read_only=True)
    attendance_stats = serializers.DictField(source='get_attendance_stats', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student_id', 'username', 'name', 'email', 'phone',
            'photo_url', 'department', 'department_name', 'course',
            'course_name', 'trainer', 'trainer_name', 'course_duration',
            'start_date', 'end_date', 'student_class', 'linkedin', 'github',
            'instagram', 'twitter', 'website', 'is_active', 'attendance_stats', 'created_at'
        ]
        read_only_fields = ['student_id']
