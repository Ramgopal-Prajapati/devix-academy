from django.urls import path
from . import views_branch_head as views

app_name = 'branch_head'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    # Trainers
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainers/add/', views.trainer_add, name='trainer_add'),
    path('trainers/<int:pk>/', views.trainer_view, name='trainer_view'),
    path('trainers/<int:pk>/edit/', views.trainer_edit, name='trainer_edit'),
    path('trainers/<int:pk>/delete/', views.trainer_delete, name='trainer_delete'),
    path('trainers/<int:pk>/reset-password/', views.trainer_reset_password, name='trainer_reset_password'),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/export-excel/', views.export_students_excel, name='export_students_excel'),
    path('students/<int:pk>/', views.student_view, name='student_view'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # Attendance & Leaves
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/<int:pk>/action/', views.leave_action, name='leave_action'),
    path('attendance-calendar/', views.attendance_calendar, name='attendance_calendar'),
    path('trainer-attendance-report/', views.trainer_attendance_report, name='trainer_attendance_report'),
    path('student-attendance-report/', views.student_attendance_report, name='student_attendance_report'),
    path('student-attendance-report/export-excel/', views.export_student_attendance_excel, name='export_student_attendance_excel'),

    # Salary & Payroll
    path('salary/calculate/', views.salary_calculator, name='salary_calculator'),
    path('salary/records/', views.salary_records_list, name='salary_records'),
    path('salary/slip/<int:pk>/', views.salary_slip_view, name='salary_slip'),
]
