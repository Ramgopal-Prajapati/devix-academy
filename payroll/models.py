from django.db import models
from django.conf import settings
from academy.models import TrainerProfile
import calendar


class SalaryRecord(models.Model):
    MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='salary_records'
    )
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField()
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Trainer's base monthly salary"
    )
    working_days = models.PositiveIntegerField(
        default=30,
        help_text="Total billable / working days in month"
    )
    present_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Days fully present"
    )
    half_day_punches = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Half days caused by >20 mins punch delay/early exit (0.5 day deduction each)"
    )
    full_day_leaves = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Approved Full Day leaves (1.0 day deduction each)"
    )
    half_day_leaves = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Approved Half Day leaves (0.5 day deduction each)"
    )
    leave_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Total leave days (full_day_leaves + 0.5 * half_day_leaves)"
    )
    absent_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Unapproved absent days (1.0 day deduction each)"
    )
    total_deduction_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Total days deducted from salary"
    )
    paid_leave_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0.0,
        help_text="Kept for backward compatibility"
    )
    per_day_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="monthly_salary / working_days"
    )
    deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total deduction amount in INR"
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final payable salary = monthly_salary - deduction"
    )
    generated_on = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_salaries'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-year', '-month', 'trainer']
        unique_together = ('trainer', 'month', 'year')

    def __str__(self):
        return f"{self.trainer.trainer_id} - {self.get_month_display()} {self.year}: ₹{self.net_salary}"

    @property
    def month_name(self):
        return calendar.month_name[self.month]

    @property
    def slip_id(self):
        return f"SLIP-{self.year}{self.month:02d}-{self.trainer.trainer_id}"
