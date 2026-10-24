from django.test import TestCase
from decimal import Decimal
from accounts.models import User
from academy.models import TrainerProfile, Department
from payroll.models import SalaryRecord


class PayrollCalculationTests(TestCase):
    def setUp(self):
        dept = Department.objects.create(name="Tech")
        self.user = User.objects.create_user(
            username='trainer_steve',
            email='steve@devix.com',
            password='Password123!',
            role=User.Role.TRAINER
        )
        self.trainer = TrainerProfile.objects.create(
            user=self.user,
            trainer_id="TRN-501",
            phone="9876540000",
            email="steve@devix.com",
            department=dept,
            monthly_salary=Decimal("60000.00")
        )

    def test_salary_formula(self):
        """
        Verify salary calculation formula:
        working_days = 30
        per_day = 60000 / 30 = 2000
        present = 25, paid_leave = 2, total_paid = 27
        absent = 30 - 27 = 3
        deduction = 3 * 2000 = 6000
        net = 60000 - 6000 = 54000
        """
        monthly = self.trainer.monthly_salary
        working_days = 30
        present_days = 25
        paid_leaves = 2
        payable_days = present_days + paid_leaves
        absent_days = working_days - payable_days

        per_day = monthly / Decimal(working_days)
        deduction = Decimal(absent_days) * per_day
        net_salary = monthly - deduction

        self.assertEqual(per_day, Decimal("2000.00"))
        self.assertEqual(deduction, Decimal("6000.00"))
        self.assertEqual(net_salary, Decimal("54000.00"))

        record = SalaryRecord.objects.create(
            trainer=self.trainer,
            month=9,
            year=2026,
            monthly_salary=monthly,
            working_days=working_days,
            present_days=present_days,
            leave_days=2,
            paid_leave_days=paid_leaves,
            absent_days=absent_days,
            per_day_salary=per_day,
            deduction=deduction,
            net_salary=net_salary
        )

        self.assertEqual(record.slip_id, "SLIP-202609-TRN-501")
        self.assertEqual(record.net_salary, Decimal("54000.00"))
