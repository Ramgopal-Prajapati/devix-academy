from django.urls import path
from . import views_trainer as views

app_name = 'trainer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.my_profile, name='my_profile'),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/export-excel/', views.export_my_students_excel, name='export_my_students_excel'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),

    # Attendance & Punch In / Punch Out
    path('attendance/students/', views.mark_student_attendance, name='mark_student_attendance'),
    path('attendance/students-report/', views.student_attendance_report, name='student_attendance_report'),
    path('attendance/students-report/export-excel/', views.export_student_attendance_excel, name='export_student_attendance_excel'),
    path('attendance/mark-self/', views.mark_my_attendance, name='mark_my_attendance'),
    path('attendance/punch-out/', views.punch_out, name='punch_out'),
    path('attendance/summary/', views.my_attendance_summary, name='my_attendance_summary'),

    # Leaves
    path('leaves/apply/', views.apply_leave, name='apply_leave'),

    # Student Leave Requests Management
    path('student-leaves/', views.student_leave_list, name='student_leaves'),
    path('student-leaves/<int:pk>/action/', views.student_leave_action, name='student_leave_action'),

    # Leave & Holiday Notices for Assigned Students
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),

    # Direct Individual Student Messages & 1-on-1 Chat
    path('messages/send/', views.message_student, name='message_student'),
    path('messages/history/', views.message_history, name='message_history'),
    path('messages/student/<int:student_id>/', views.student_conversation, name='student_conversation'),

    # Learning Resources (Materials & Notes by Course)
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/create/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),
]
