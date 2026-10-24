from django.urls import path, include
from rest_framework.routers import DefaultRouter
from academy.api import (
    CourseViewSet, DepartmentViewSet, TrainerViewSet,
    StudentViewSet, AttendanceViewSet, LeaveRequestViewSet,
    SalaryRecordViewSet,
    notification_list_api, notification_poll_api,
    notification_mark_read_api, notification_mark_all_read_api
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='api-course')
router.register(r'departments', DepartmentViewSet, basename='api-department')
router.register(r'trainers', TrainerViewSet, basename='api-trainer')
router.register(r'students', StudentViewSet, basename='api-student')
router.register(r'attendance', AttendanceViewSet, basename='api-attendance')
router.register(r'leaves', LeaveRequestViewSet, basename='api-leave')
router.register(r'salary', SalaryRecordViewSet, basename='api-salary')

urlpatterns = [
    path('notifications/', notification_list_api, name='api-notifications-list'),
    path('notifications/poll/', notification_poll_api, name='api-notifications-poll'),
    path('notifications/<int:pk>/mark-read/', notification_mark_read_api, name='api-notifications-mark-read'),
    path('notifications/mark-all-read/', notification_mark_all_read_api, name='api-notifications-mark-all-read'),
    path('', include(router.urls)),
]
