from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        BRANCH_HEAD = 'BRANCH_HEAD', 'Branch Head'
        TRAINER = 'TRAINER', 'Trainer'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Role defines the access level and dashboard view."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Contact phone number."
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="If set, user will be prompted to change password on first login."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def clean(self):
        super().clean()
        # Enforce exactly one Branch Head in the system
        if self.role == self.Role.BRANCH_HEAD:
            existing = User.objects.filter(role=self.Role.BRANCH_HEAD)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({
                    'role': 'Only one Branch Head account is permitted in DeviX Academy.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_branch_head(self):
        return self.role == self.Role.BRANCH_HEAD

    @property
    def is_trainer(self):
        return self.role == self.Role.TRAINER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def display_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
