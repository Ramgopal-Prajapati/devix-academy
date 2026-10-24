from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import User
from academy.models import TrainerProfile, StudentProfile, Department


class AccountsSecurityAndRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Tech")
        self.bh_user = User.objects.create_user(
            username='head_ram',
            email='ram@devixacademy.com',
            password='TestPassword123!',
            role=User.Role.BRANCH_HEAD
        )
        self.trainer_user = User.objects.create_user(
            username='trainer_bob',
            email='bob@devixacademy.com',
            password='TestPassword123!',
            role=User.Role.TRAINER
        )
        self.trainer = TrainerProfile.objects.create(
            user=self.trainer_user,
            trainer_id='TRN-101',
            phone='9811111111',
            email='bob@devixacademy.com',
            department=self.dept,
            monthly_salary=Decimal('50000.00')
        )
        self.student_user = User.objects.create_user(
            username='student_alice',
            email='alice@gmail.com',
            password='TestPassword123!',
            role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            student_id='DVX-2026-1001',
            name='Alice Smith',
            email='alice@gmail.com',
            phone='9822222222',
            department=self.dept,
            trainer=self.trainer,
            start_date=date.today()
        )

    def test_single_branch_head_rule_enforced(self):
        """Verify that attempting to create a second Branch Head raises ValidationError."""
        second_bh = User(
            username='head_duplicate',
            email='dup@devixacademy.com',
            role=User.Role.BRANCH_HEAD
        )
        with self.assertRaises(ValidationError):
            second_bh.save()

    def test_role_based_redirects(self):
        """Verify authenticated users are routed to their role dashboards."""
        # Branch Head
        self.client.login(username='head_ram', password='TestPassword123!')
        res_bh = self.client.get(reverse('accounts:role_redirect'))
        self.assertRedirects(res_bh, reverse('branch_head:dashboard'))
        self.client.logout()

        # Trainer
        self.client.login(username='trainer_bob', password='TestPassword123!')
        res_trn = self.client.get(reverse('accounts:role_redirect'))
        self.assertRedirects(res_trn, reverse('trainer:dashboard'))
        self.client.logout()

        # Student
        self.client.login(username='student_alice', password='TestPassword123!')
        res_std = self.client.get(reverse('accounts:role_redirect'))
        self.assertRedirects(res_std, reverse('student:dashboard'))
        self.client.logout()

    def test_role_access_restriction_returns_403(self):
        """Verify a user attempting to open another role's views gets 403 Forbidden."""
        # Trainer trying to access Branch Head dashboard -> 403
        self.client.login(username='trainer_bob', password='TestPassword123!')
        res = self.client.get(reverse('branch_head:dashboard'))
        self.assertEqual(res.status_code, 403)
        self.client.logout()

        # Student trying to access Trainer dashboard -> 403
        self.client.login(username='student_alice', password='TestPassword123!')
        res = self.client.get(reverse('trainer:dashboard'))
        self.assertEqual(res.status_code, 403)
        self.client.logout()
