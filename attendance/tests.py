from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import User
from academy.models import Department, Course, TrainerProfile, StudentProfile, Notification, TrainerNotice, CourseResource, StudentDirectMessage
from attendance.models import Attendance, StudentLeaveRequest
from attendance.forms import StudentLeaveRequestForm


class StudentLeaveWorkflowTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Tech")
        self.course = Course.objects.create(
            name="Python Full Stack Development",
            department=self.dept,
            duration="6 Months",
            fees=Decimal("35000.00")
        )

        # Trainer
        self.trainer_user = User.objects.create_user(
            username="trainer_vikas",
            email="vikas@devix.com",
            password="TrainerPassword123!",
            role=User.Role.TRAINER
        )
        self.trainer = TrainerProfile.objects.create(
            user=self.trainer_user,
            trainer_id="TRN-901",
            phone="9876543210",
            email="vikas@devix.com",
            department=self.dept,
            monthly_salary=Decimal("50000.00")
        )

        # Student
        self.student_user = User.objects.create_user(
            username="student_manish",
            email="manish@devix.com",
            password="StudentPassword123!",
            role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            student_id="DVX-2026-0901",
            name="Manish Sharma",
            email="manish@devix.com",
            phone="9876543211",
            department=self.dept,
            course=self.course,
            trainer=self.trainer,
            start_date=date.today() - timedelta(days=20),
            is_active=True
        )

        self.client = Client()

    def test_student_leave_form_validation(self):
        """End date cannot be earlier than start date."""
        today = date.today()
        invalid_data = {
            'leave_type': 'Medical',
            'from_date': today,
            'to_date': today - timedelta(days=1),
            'reason': 'Medical emergency'
        }
        form = StudentLeaveRequestForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("End date cannot be earlier than start date.", form.non_field_errors())

        valid_data = {
            'leave_type': 'Medical',
            'from_date': today,
            'to_date': today + timedelta(days=2),
            'reason': 'Medical surgery and bed rest'
        }
        form = StudentLeaveRequestForm(data=valid_data)
        self.assertTrue(form.is_valid())

    def test_student_apply_leave_creates_request_and_notifies_trainer(self):
        """Student applies for leave; verify StudentLeaveRequest created & notification sent to trainer."""
        self.client.login(username="student_manish", password="StudentPassword123!")
        today = date.today()

        response = self.client.post(reverse('student:leave_apply'), {
            'leave_type': 'Academic',
            'from_date': today + timedelta(days=1),
            'to_date': today + timedelta(days=3),
            'reason': 'Semester theory exams'
        })
        self.assertEqual(response.status_code, 302)

        # Verify StudentLeaveRequest exists
        leave = StudentLeaveRequest.objects.filter(student=self.student).first()
        self.assertIsNotNone(leave)
        self.assertEqual(leave.status, 'Pending')
        self.assertEqual(leave.total_days, 3)

        # Verify Trainer received Notification
        notif = Notification.objects.filter(recipient=self.trainer_user, notification_type='LEAVE_REQUEST').first()
        self.assertIsNotNone(notif)
        self.assertIn("Manish Sharma", notif.title)
        self.assertEqual(notif.is_read, False)

    def test_trainer_approve_student_leave_marks_leave_in_attendance(self):
        """When trainer approves, attendance on those dates is marked 'Leave', not Absent."""
        today = date.today()
        d1 = today + timedelta(days=1)
        d2 = today + timedelta(days=2)

        leave = StudentLeaveRequest.objects.create(
            student=self.student,
            leave_type='Medical',
            from_date=d1,
            to_date=d2,
            reason='Fever and doctor rest',
            status='Pending'
        )

        self.client.login(username="trainer_vikas", password="TrainerPassword123!")
        response = self.client.post(reverse('trainer:student_leave_action', args=[leave.id]), {
            'status': 'Approved',
            'trainer_remark': 'Approved. Take care and get well soon.'
        })
        self.assertEqual(response.status_code, 302)

        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Approved')
        self.assertEqual(leave.trainer_remark, 'Approved. Take care and get well soon.')

        # Verify Attendance is created with status='Leave' for each day
        att1 = Attendance.objects.get(student=self.student, date=d1)
        att2 = Attendance.objects.get(student=self.student, date=d2)
        self.assertEqual(att1.status, 'Leave')
        self.assertEqual(att2.status, 'Leave')

        # Verify Student received approval Notification
        student_notif = Notification.objects.filter(recipient=self.student_user, notification_type='LEAVE_REVIEW').first()
        self.assertIsNotNone(student_notif)
        self.assertIn("Approved", student_notif.title)

    def test_trainer_reject_student_leave_reverts_leave_to_absent(self):
        """When trainer rejects, any marked leave is reverted to 'Absent'."""
        today = date.today()
        d1 = today + timedelta(days=1)

        # Pre-seed with Leave status
        Attendance.objects.create(student=self.student, date=d1, status='Leave', marked_by=self.trainer_user)

        leave = StudentLeaveRequest.objects.create(
            student=self.student,
            leave_type='Personal',
            from_date=d1,
            to_date=d1,
            reason='Family trip',
            status='Pending'
        )

        self.client.login(username="trainer_vikas", password="TrainerPassword123!")
        response = self.client.post(reverse('trainer:student_leave_action', args=[leave.id]), {
            'status': 'Rejected',
            'trainer_remark': 'Trip during exam revision is not permitted.'
        })
        self.assertEqual(response.status_code, 302)

        leave.refresh_from_db()
        self.assertEqual(leave.status, 'Rejected')

        att1 = Attendance.objects.get(student=self.student, date=d1)
        self.assertEqual(att1.status, 'Absent')

        # Verify Student received rejection Notification
        student_notif = Notification.objects.filter(recipient=self.student_user, notification_type='LEAVE_REVIEW').first()
        self.assertIsNotNone(student_notif)
        self.assertIn("Rejected", student_notif.title)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_notif_user",
            email="notif@devix.com",
            password="Password123!",
            role=User.Role.STUDENT
        )
        self.client = Client()
        self.client.login(username="test_notif_user", password="Password123!")

        self.n1 = Notification.objects.create(
            recipient=self.user,
            title="Class Rescheduled",
            message="Class starts at 11 AM tomorrow.",
            link_url="/student/dashboard/",
            notification_type="NOTICE",
            is_read=False
        )
        self.n2 = Notification.objects.create(
            recipient=self.user,
            title="New Study PDF",
            message="Django Cheatsheet PDF available.",
            link_url="/student/resources/",
            notification_type="RESOURCE",
            is_read=False
        )

    def test_notification_list_api(self):
        response = self.client.get(reverse('api-notifications-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 2)
        self.assertEqual(len(data['notifications']), 2)

    def test_notification_poll_api(self):
        # Poll since id 0
        response = self.client.get(reverse('api-notifications-poll') + '?last_id=0')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['has_new'])
        self.assertEqual(data['total_unread'], 2)

        # Poll since n2.id (no new notifications)
        response2 = self.client.get(reverse('api-notifications-poll') + f'?last_id={self.n2.id}')
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertFalse(data2['has_new'])

    def test_notification_mark_read_and_mark_all_read(self):
        # Mark single read
        resp = self.client.post(reverse('api-notifications-mark-read', args=[self.n1.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['unread_count'], 1)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

        # Mark all read
        resp2 = self.client.post(reverse('api-notifications-mark-all-read'))
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()['unread_count'], 0)
        self.n2.refresh_from_db()
        self.assertTrue(self.n2.is_read)
