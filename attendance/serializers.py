from rest_framework import serializers
from .models import Attendance, TrainerAttendance, LeaveRequest


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.username', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_id', 'student_name', 'date', 'status', 'marked_by', 'marked_by_name', 'created_at']


class TrainerAttendanceSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.full_name', read_only=True)
    trainer_id = serializers.CharField(source='trainer.trainer_id', read_only=True)

    class Meta:
        model = TrainerAttendance
        fields = ['id', 'trainer', 'trainer_id', 'trainer_name', 'date', 'status', 'check_in', 'created_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.full_name', read_only=True)
    trainer_id = serializers.CharField(source='trainer.trainer_id', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    total_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'trainer', 'trainer_id', 'trainer_name', 'from_date',
            'to_date', 'total_days', 'reason', 'status', 'applied_on',
            'reviewed_by', 'reviewed_by_name', 'remark'
        ]
        read_only_fields = ['status', 'reviewed_by', 'remark']
