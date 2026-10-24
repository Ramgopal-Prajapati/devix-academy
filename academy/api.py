from rest_framework import viewsets, permissions, filters
from academy.models import Department, Course, TrainerProfile, StudentProfile
from attendance.models import Attendance, TrainerAttendance, LeaveRequest
from payroll.models import SalaryRecord
from .serializers import (
    DepartmentSerializer, CourseSerializer,
    TrainerProfileSerializer, StudentProfileSerializer
)
from attendance.serializers import (
    AttendanceSerializer, TrainerAttendanceSerializer, LeaveRequestSerializer
)
from payroll.serializers import SalaryRecordSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Courses.
    Supports filtering by department e.g. /api/courses/?department=1
    """
    queryset = Course.objects.filter(is_active=True).select_related('department')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]  # Allow dropdown fetch

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        return qs


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]


class TrainerViewSet(viewsets.ModelViewSet):
    queryset = TrainerProfile.objects.select_related('user', 'department')
    serializer_class = TrainerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_branch_head:
            return self.queryset.all()
        if user.is_trainer and hasattr(user, 'trainer_profile'):
            return self.queryset.filter(user=user)
        return self.queryset.none()


class StudentViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user', 'department', 'course', 'trainer', 'trainer__user')
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_branch_head:
            return self.queryset.all()
        if user.is_trainer and hasattr(user, 'trainer_profile'):
            return self.queryset.filter(trainer=user.trainer_profile)
        if user.is_student and hasattr(user, 'student_profile'):
            return self.queryset.filter(user=user)
        return self.queryset.none()


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('student', 'marked_by')
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_branch_head:
            return self.queryset.all()
        if user.is_trainer and hasattr(user, 'trainer_profile'):
            return self.queryset.filter(student__trainer=user.trainer_profile)
        if user.is_student and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)
        return self.queryset.none()


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('trainer', 'trainer__user', 'reviewed_by')
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_branch_head:
            return self.queryset.all()
        if user.is_trainer and hasattr(user, 'trainer_profile'):
            return self.queryset.filter(trainer=user.trainer_profile)
        return self.queryset.none()


class SalaryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalaryRecord.objects.select_related('trainer', 'trainer__user', 'generated_by')
    serializer_class = SalaryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_branch_head:
            return self.queryset.all()
        if user.is_trainer and hasattr(user, 'trainer_profile'):
            return self.queryset.filter(trainer=user.trainer_profile)
        return self.queryset.none()


# ------------------- NOTIFICATIONS API -------------------
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from academy.models import Notification


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list_api(request):
    """Returns recent notifications and unread count for current user."""
    notifs = Notification.objects.filter(recipient=request.user)[:15]
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link_url': n.link_url,
            'type': n.notification_type,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d %b, %I:%M %p'),
        }
        for n in notifs
    ]
    return Response({
        'unread_count': unread_count,
        'notifications': data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_read_api(request, pk):
    """Marks a single notification as read."""
    Notification.objects.filter(id=pk, recipient=request.user).update(is_read=True)
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({'success': True, 'unread_count': unread_count})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_all_read_api(request):
    """Marks all notifications as read for current user."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({'success': True, 'unread_count': 0})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def notification_poll_api(request):
    """
    Polls for new unread notifications since last_id.
    Safely returns empty response if visitor is not logged in (prevents 403 Forbidden).
    """
    if not request.user.is_authenticated:
        return Response({
            'has_new': False,
            'total_unread': 0,
            'notifications': []
        })

    last_id = int(request.query_params.get('last_id', 0))
    qs = Notification.objects.filter(recipient=request.user, is_read=False)
    if last_id > 0:
        qs = qs.filter(id__gt=last_id)

    new_notifs = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link_url': n.link_url,
            'type': n.notification_type,
            'created_at': n.created_at.strftime('%I:%M %p'),
        }
        for n in qs[:5]
    ]

    total_unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({
        'has_new': len(new_notifs) > 0,
        'total_unread': total_unread,
        'notifications': new_notifs
    })
