from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Tech, Non-Tech")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField()
    duration = models.CharField(max_length=50, help_text="e.g. 6 Months, 90 Days")
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Course fees in INR")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class TrainerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trainer_profile'
    )
    trainer_id = models.CharField(max_length=30, unique=True, help_text="e.g. TRN-001")
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainers'
    )
    profile_picture = models.ImageField(upload_to='trainers/', null=True, blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    experience_details = models.TextField(blank=True)
    technologies = models.TextField(
        blank=True,
        help_text="Comma-separated technologies e.g. Java Full Stack, Data Science, Web Development"
    )
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)
    monthly_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Monthly gross salary set by Branch Head."
    )
    daily_working_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=4.0,
        help_text="Scheduled daily working hours (e.g. 2, 3, 5, 5.5 hours)."
    )
    expected_start_time = models.TimeField(
        default=datetime.time(9, 0),
        help_text="Scheduled morning check-in time (e.g. 09:00 AM)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['trainer_id']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.trainer_id})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_technologies_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(',') if t.strip()]

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-trainer.svg'

    @property
    def unread_messages_count(self):
        return self.sent_student_messages.filter(is_read=False, sender_role='STUDENT').count()


def generate_student_id():
    """Generates sequential student ID like DVX-2026-0001."""
    current_year = timezone.now().year
    prefix = f"DVX-{current_year}-"
    last_student = StudentProfile.objects.filter(
        student_id__startswith=prefix
    ).order_by('-student_id').first()

    if last_student:
        try:
            last_num_str = last_student.student_id.split('-')[-1]
            last_num = int(last_num_str)
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = StudentProfile.objects.filter(student_id__startswith=prefix).count() + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:04d}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=30, unique=True, default=generate_student_id)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    profile_picture = models.ImageField(upload_to='students/', null=True, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    course_duration = models.CharField(max_length=50, blank=True)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(null=True, blank=True)
    student_class = models.CharField(max_length=100, blank=True, help_text="e.g. Batch A, Morning")
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    @property
    def profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-student.svg'

    def get_attendance_stats(self):
        from attendance.models import Attendance
        records = Attendance.objects.filter(student=self)
        total = records.count()
        present = records.filter(status='Present').count()
        absent = records.filter(status='Absent').count()
        leave = records.filter(status='Leave').count()
        pct = round((present / total * 100), 1) if total > 0 else 0.0
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'leave': leave,
            'percentage': pct,
            'is_eligible': pct >= 75.0,
        }

    @property
    def unread_notices_count(self):
        if not self.trainer:
            return 0
        return TrainerNotice.objects.filter(
            trainer=self.trainer,
            is_active=True
        ).exclude(read_by=self).count()

    @property
    def unread_messages_count(self):
        return self.received_trainer_messages.filter(is_read=False, sender_role='TRAINER').count()


class TrainerNotice(models.Model):
    """
    Leave & Holiday Notices posted by a Trainer.
    Visible ONLY to students assigned to this trainer (and related department).
    """
    NOTICE_TYPES = [
        ('LEAVE', 'Trainer On Leave'),
        ('HOLIDAY', 'Institute / Batch Holiday'),
        ('NOTICE', 'Important Class Announcement'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='notices'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainer_notices'
    )
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPES, default='LEAVE')
    title = models.CharField(max_length=200)
    message = models.TextField()
    from_date = models.DateField(null=True, blank=True, help_text="Start date of leave or holiday")
    to_date = models.DateField(null=True, blank=True, help_text="End date of leave or holiday")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(StudentProfile, related_name='read_notices', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_notice_type_display()}] {self.title} - {self.trainer.full_name}"


class StudentDirectMessage(models.Model):
    """
    Individual direct message sent between Trainer and a particular student.
    Can include PDF/files, course materials, URLs/links, and notes.
    Supports 2-way 1-on-1 private messaging (Trainer <-> Student).
    """
    SENDER_ROLES = [
        ('TRAINER', 'Trainer'),
        ('STUDENT', 'Student'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='sent_student_messages'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='received_trainer_messages'
    )
    sender_role = models.CharField(max_length=10, choices=SENDER_ROLES, default='TRAINER')
    subject = models.CharField(max_length=200, default='Direct Message')
    message = models.TextField()
    attachment = models.FileField(upload_to='student_materials/', null=True, blank=True)
    link_url = models.URLField(blank=True, null=True, help_text="Optional external link (docs, videos, repo)")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.trainer.full_name} to {self.student.name}: {self.subject}"

    @property
    def attachment_filename(self):
        if self.attachment:
            import os
            return os.path.basename(self.attachment.name)
        return ""


class CourseResource(models.Model):
    """
    Learning Resources tab for students, filtered strictly according to their enrolled course.
    Trainers can add resources in File (PDF/docs), Link, or Code/Notes format.
    """
    RESOURCE_TYPES = [
        ('FILE', 'PDF / Document / File'),
        ('LINK', 'External Link / Video / Repo'),
        ('NOTES', 'Lecture Notes / Code Snippet'),
    ]

    trainer = models.ForeignKey(
        TrainerProfile,
        on_delete=models.CASCADE,
        related_name='uploaded_resources'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES, default='FILE')
    file = models.FileField(upload_to='course_resources/', null=True, blank=True)
    link_url = models.URLField(blank=True, null=True)
    notes_content = models.TextField(blank=True, help_text="Code snippet or markdown/text notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.course.name}) - {self.get_resource_type_display()}"

    @property
    def file_filename(self):
        if self.file:
            import os
            return os.path.basename(self.file.name)
        return ""


class Notification(models.Model):
    """
    In-App and Mobile System notification record.
    Generated automatically whenever activities happen:
    - Student leave request submitted / reviewed
    - Trainer leave request submitted / reviewed
    - New learning resource uploaded
    - Notice / Holiday announcement
    - Direct 1-on-1 messages and replies
    - Student enrollment and course assignment
    """
    NOTIFICATION_TYPES = [
        ('LEAVE_REQUEST', 'Leave Request'),
        ('LEAVE_REVIEW', 'Leave Review'),
        ('MESSAGE', 'Direct Message'),
        ('RESOURCE', 'Learning Resource'),
        ('NOTICE', 'Notice / Holiday'),
        ('STUDENT_ENROLLED', 'Student Enrolled'),
        ('COURSE_ASSIGNED', 'Course Assigned'),
        ('SYSTEM', 'System Alert'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link_url = models.CharField(max_length=255, blank=True, default='')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='SYSTEM')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] To: {self.recipient.username} - {self.title}"


