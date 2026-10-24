from django.db import models
from django.conf import settings
from academy.models import StudentProfile, TrainerProfile
import datetime


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.student_id} - {self.date} - {self.status}"


class TrainerAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Half_Day', 'Half Day'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Present')
    check_in = models.TimeField(null=True, blank=True, help_text="Morning punch-in time")
    check_out = models.TimeField(null=True, blank=True, help_text="Evening punch-out time")
    working_hours_recorded = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        help_text="Actual hours logged between punch-in and punch-out"
    )
    remark = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('trainer', 'date')

    def __str__(self):
        return f"{self.trainer.trainer_id} - {self.date} - {self.status}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    LEAVE_DURATION_CHOICES = [
        ('FULL_DAY', 'Full Day (1 Day)'),
        ('HALF_DAY', 'Half Day (0.5 Day)'),
    ]

    HALF_DAY_PERIOD_CHOICES = [
        ('FIRST_HALF', 'First Half (Morning)'),
        ('SECOND_HALF', 'Second Half (Afternoon)'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_duration_type = models.CharField(
        max_length=10,
        choices=LEAVE_DURATION_CHOICES,
        default='FULL_DAY'
    )
    half_day_period = models.CharField(
        max_length=15,
        choices=HALF_DAY_PERIOD_CHOICES,
        blank=True,
        null=True
    )
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leaves'
    )
    remark = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.trainer.trainer_id}: {self.from_date} ({self.get_leave_duration_type_display()}) - {self.status}"

    @property
    def total_days(self):
        if self.leave_duration_type == 'HALF_DAY':
            return 0.5
        if self.from_date and self.to_date:
            return float((self.to_date - self.from_date).days + 1)
        return 0.0


class StudentLeaveRequest(models.Model):
    """
    Leave application submitted by an enrolled Student to their assigned Trainer.
    Trainer can Accept (Approved) or Reject.
    - If Trainer accepts: Attendance on those dates is marked as 'Leave' (NOT Absent).
    - If Trainer rejects: Student is marked 'Absent' if they do not attend.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    LEAVE_TYPE_CHOICES = [
        ('Medical', 'Medical / Sickness'),
        ('Personal', 'Personal / Family'),
        ('Academic', 'College / University Exam'),
        ('Emergency', 'Family Emergency'),
        ('Other', 'Other Reason'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='student_leave_requests'
    )
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES, default='Personal')
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_student_leaves'
    )
    trainer_remark = models.TextField(blank=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.student.student_id} ({self.student.name}): {self.from_date} to {self.to_date} [{self.status}]"

    @property
    def total_days(self):
        if self.from_date and self.to_date:
            return (self.to_date - self.from_date).days + 1
        return 0
