from rest_framework import serializers
from .models import SalaryRecord


class SalaryRecordSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.full_name', read_only=True)
    trainer_id = serializers.CharField(source='trainer.trainer_id', read_only=True)
    month_name = serializers.CharField(read_only=True)
    slip_id = serializers.CharField(read_only=True)

    class Meta:
        model = SalaryRecord
        fields = [
            'id', 'slip_id', 'trainer', 'trainer_id', 'trainer_name',
            'month', 'month_name', 'year', 'monthly_salary', 'working_days',
            'present_days', 'leave_days', 'paid_leave_days', 'absent_days',
            'per_day_salary', 'deduction', 'net_salary', 'generated_on', 'notes'
        ]
