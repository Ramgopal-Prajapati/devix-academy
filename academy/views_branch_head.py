from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta, time
from decimal import Decimal
import calendar
import json

from accounts.decorators import branch_head_required
from accounts.models import User
from academy.models import Department, Course, TrainerProfile, StudentProfile
from academy.notifications import send_notification
from academy.excel_utils import (
    export_students_detail_excel_response,
    export_monthly_student_attendance_excel_response
)
from attendance.models import Attendance, TrainerAttendance, LeaveRequest
from attendance.calendar_utils import build_month_calendar_grid
from payroll.models import SalaryRecord
from academy.forms import (
    TrainerCreationForm, TrainerUpdateForm,
    StudentBranchHeadUpdateForm, CourseForm, DepartmentForm
)
from attendance.forms import LeaveReviewForm
from payroll.forms import SalaryGenerationForm


@branch_head_required
def dashboard(request):
    """Branch Head Overview Dashboard with summary metric cards and Chart.js analytics."""
    today = date.today()

    # Metrics
    total_students = StudentProfile.objects.filter(is_active=True).count()
    total_trainers = TrainerProfile.objects.count()
    total_courses = Course.objects.filter(is_active=True).count()
    trainers_present_today = TrainerAttendance.objects.filter(date=today, status='Present').count()
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()

    # Chart.js Data: Students enrolled per course
    courses_qs = Course.objects.filter(is_active=True).annotate(
        student_count=Count('students', filter=Q(students__is_active=True))
    ).order_by('-student_count')[:8]

    course_labels = [c.name for c in courses_qs]
    course_counts = [c.student_count for c in courses_qs]

    # Department distribution
    dept_qs = Department.objects.annotate(
        student_count=Count('students', filter=Q(students__is_active=True))
    )
    dept_labels = [d.name for d in dept_qs]
    dept_counts = [d.student_count for d in dept_qs]

    recent_leaves = LeaveRequest.objects.select_related('trainer', 'trainer__user').order_by('-applied_on')[:5]

    context = {
        'total_students': total_students,
        'total_trainers': total_trainers,
        'total_courses': total_courses,
        'trainers_present_today': trainers_present_today,
        'pending_leaves': pending_leaves,
        'course_labels_json': json.dumps(course_labels),
        'course_counts_json': json.dumps(course_counts),
        'dept_labels_json': json.dumps(dept_labels),
        'dept_counts_json': json.dumps(dept_counts),
        'recent_leaves': recent_leaves,
        'today': today,
    }
    return render(request, 'branch_head/dashboard.html', context)


# ------------------- TRAINER MANAGEMENT -------------------

@branch_head_required
def trainer_list(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()

    trainers = TrainerProfile.objects.select_related('user', 'department').all()

    if query:
        trainers = trainers.filter(
            Q(trainer_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(technologies__icontains=query)
        )
    if dept_id:
        trainers = trainers.filter(department_id=dept_id)

    departments = Department.objects.filter(is_active=True)
    return render(request, 'branch_head/trainer_list.html', {
        'trainers': trainers,
        'departments': departments,
        'query': query,
        'selected_dept': dept_id,
    })


@branch_head_required
def trainer_add(request):
    if request.method == 'POST':
        form = TrainerCreationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            user = User(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=User.Role.TRAINER,
                phone=data['phone'],
                must_change_password=True
            )
            user.set_password(data['password'])
            user.save()

            trainer = TrainerProfile(
                user=user,
                trainer_id=data['trainer_id'],
                phone=data['phone'],
                email=data['email'],
                department=data.get('department'),
                profile_picture=data.get('profile_picture'),
                monthly_salary=data.get('monthly_salary') or Decimal('0.00'),
                daily_working_hours=data.get('daily_working_hours') or Decimal('4.0'),
                expected_start_time=data.get('expected_start_time') or time(9, 0),
                technologies=data.get('technologies', ''),
                experience_years=data.get('experience_years') or Decimal('0.0'),
                experience_details=data.get('experience_details', ''),
                bio=data.get('bio', ''),
                linkedin=data.get('linkedin', ''),
                github=data.get('github', ''),
                instagram=data.get('instagram', ''),
                youtube=data.get('youtube', ''),
                twitter=data.get('twitter', ''),
                website=data.get('website', '')
            )
            trainer.save()
            messages.success(request, f"Trainer '{trainer.full_name}' ({trainer.trainer_id}) added successfully!")
            return redirect('branch_head:trainer_list')
    else:
        form = TrainerCreationForm()
    return render(request, 'branch_head/trainer_form.html', {'form': form, 'title': 'Add New Trainer'})


@branch_head_required
def trainer_view(request, pk):
    trainer = get_object_or_404(TrainerProfile.objects.select_related('user', 'department'), pk=pk)
    students = trainer.students.filter(is_active=True).select_related('course')
    recent_attendance = trainer.attendances.order_by('-date')[:15]
    salary_records = trainer.salary_records.order_by('-year', '-month')[:6]
    return render(request, 'branch_head/trainer_detail.html', {
        'trainer': trainer,
        'students': students,
        'recent_attendance': recent_attendance,
        'salary_records': salary_records,
    })


@branch_head_required
def trainer_edit(request, pk):
    trainer = get_object_or_404(TrainerProfile, pk=pk)
    if request.method == 'POST':
        form = TrainerUpdateForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            trainer = form.save()
            # Update user names
            trainer.user.first_name = form.cleaned_data['first_name']
            trainer.user.last_name = form.cleaned_data['last_name']
            trainer.user.email = trainer.email
            trainer.user.phone = trainer.phone
            trainer.user.save()
            messages.success(request, f"Trainer details for '{trainer.full_name}' updated successfully!")
            return redirect('branch_head:trainer_view', pk=trainer.pk)
    else:
        form = TrainerUpdateForm(instance=trainer)
    return render(request, 'branch_head/trainer_form.html', {
        'form': form,
        'trainer': trainer,
        'title': f'Edit Trainer: {trainer.full_name}'
    })


@branch_head_required
def trainer_delete(request, pk):
    trainer = get_object_or_404(TrainerProfile, pk=pk)
    if request.method == 'POST':
        name = trainer.full_name
        user = trainer.user
        trainer.delete()
        user.delete()
        messages.success(request, f"Trainer '{name}' and associated account were deleted successfully.")
        return redirect('branch_head:trainer_list')
    return redirect('branch_head:trainer_view', pk=pk)


@branch_head_required
def trainer_reset_password(request, pk):
    trainer = get_object_or_404(TrainerProfile, pk=pk)
    if request.method == 'POST':
        new_pass = request.POST.get('new_password', '').strip()
        if len(new_pass) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            trainer.user.set_password(new_pass)
            trainer.user.must_change_password = True
            trainer.user.save()
            messages.success(request, f"Password reset for {trainer.full_name}. Next login will prompt password change.")
    return redirect('branch_head:trainer_view', pk=pk)


# ------------------- STUDENT MANAGEMENT -------------------

@branch_head_required
def student_list(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()
    course_id = request.GET.get('course', '').strip()
    trainer_id = request.GET.get('trainer', '').strip()

    students = StudentProfile.objects.select_related('user', 'department', 'course', 'trainer', 'trainer__user').all()

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    if dept_id:
        students = students.filter(department_id=dept_id)
    if course_id:
        students = students.filter(course_id=course_id)
    if trainer_id:
        students = students.filter(trainer_id=trainer_id)

    departments = Department.objects.filter(is_active=True)
    courses = Course.objects.filter(is_active=True)
    trainers = TrainerProfile.objects.all()

    return render(request, 'branch_head/student_list.html', {
        'students': students,
        'departments': departments,
        'courses': courses,
        'trainers': trainers,
        'query': query,
        'selected_dept': dept_id,
        'selected_course': course_id,
        'selected_trainer': trainer_id,
    })


@branch_head_required
def export_students_excel(request):
    """Export all students or filtered students list to an Excel (.xlsx) spreadsheet."""
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '').strip()
    course_id = request.GET.get('course', '').strip()
    trainer_id = request.GET.get('trainer', '').strip()

    students = StudentProfile.objects.select_related('user', 'department', 'course', 'trainer', 'trainer__user').all()

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    if dept_id:
        students = students.filter(department_id=dept_id)
    if course_id:
        students = students.filter(course_id=course_id)
    if trainer_id:
        students = students.filter(trainer_id=trainer_id)

    return export_students_detail_excel_response(students, filename="DeviX_Students_Directory.xlsx")


@branch_head_required
def student_view(request, pk):
    student = get_object_or_404(StudentProfile.objects.select_related('user', 'department', 'course', 'trainer', 'trainer__user'), pk=pk)
    stats = student.get_attendance_stats()
    attendance_records = student.attendances.order_by('-date')
    return render(request, 'branch_head/student_detail.html', {
        'student': student,
        'stats': stats,
        'attendance_records': attendance_records,
    })


@branch_head_required
def student_edit(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        form = StudentBranchHeadUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            student.user.first_name = student.name.split()[0]
            student.user.last_name = " ".join(student.name.split()[1:]) if len(student.name.split()) > 1 else ""
            student.user.email = student.email
            student.user.phone = student.phone
            student.user.save()

            # Activity Notification for Course / Trainer assignment
            if student.user:
                send_notification(
                    recipient=student.user,
                    title="Profile & Course Updated",
                    message=f"Your course details have been updated to {student.course.name if student.course else 'Course'} by Branch Head.",
                    link_url="/student/dashboard/",
                    notification_type='COURSE_ASSIGNED'
                )

            messages.success(request, f"Student '{student.name}' details updated successfully!")
            return redirect('branch_head:student_view', pk=student.pk)
    else:
        form = StudentBranchHeadUpdateForm(instance=student)
    return render(request, 'branch_head/student_form.html', {
        'form': form,
        'student': student,
        'title': f'Edit Student: {student.name} ({student.student_id})'
    })


@branch_head_required
def student_delete(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        name = student.name
        user = student.user
        student.delete()
        user.delete()
        messages.success(request, f"Student '{name}' and user account were deleted.")
        return redirect('branch_head:student_list')
    return redirect('branch_head:student_view', pk=pk)


# ------------------- COURSE & DEPARTMENT CRUD -------------------

@branch_head_required
def course_list(request):
    courses = Course.objects.select_related('department').annotate(
        student_count=Count('students')
    ).order_by('department__name', 'name')
    return render(request, 'branch_head/course_list.html', {'courses': courses})


@branch_head_required
def course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.name}' created successfully!")
            return redirect('branch_head:course_list')
    else:
        form = CourseForm()
    return render(request, 'branch_head/course_form.html', {'form': form, 'title': 'Create New Course'})


@branch_head_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.name}' updated successfully!")
            return redirect('branch_head:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'branch_head/course_form.html', {'form': form, 'title': f'Edit Course: {course.name}'})


@branch_head_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        messages.success(request, f"Course '{name}' has been deleted.")
    return redirect('branch_head:course_list')


@branch_head_required
def department_list(request):
    departments = Department.objects.annotate(
        course_count=Count('courses'),
        student_count=Count('students')
    ).order_by('name')
    return render(request, 'branch_head/department_list.html', {'departments': departments})


@branch_head_required
def department_add(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' added successfully!")
            return redirect('branch_head:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'branch_head/department_form.html', {'form': form, 'title': 'Add Department'})


@branch_head_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' updated successfully!")
            return redirect('branch_head:department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'branch_head/department_form.html', {'form': form, 'title': f'Edit Department: {dept.name}'})


@branch_head_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = dept.name
        dept.delete()
        messages.success(request, f"Department '{name}' has been deleted.")
    return redirect('branch_head:department_list')


# ------------------- LEAVE MANAGEMENT -------------------

@branch_head_required
def leave_list(request):
    status_filter = request.GET.get('status', '').strip()
    leaves = LeaveRequest.objects.select_related('trainer', 'trainer__user', 'reviewed_by').all()
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    leaves = leaves.order_by('-applied_on')
    return render(request, 'branch_head/leave_list.html', {
        'leaves': leaves,
        'selected_status': status_filter
    })


@branch_head_required
def leave_action(request, pk):
    leave_req = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        remark = request.POST.get('remark', '').strip()

        if status in ['Approved', 'Rejected']:
            leave_req.status = status
            leave_req.remark = remark
            leave_req.reviewed_by = request.user
            leave_req.save()

            # If approved, record trainer attendance as Leave for the requested range
            if status == 'Approved':
                cur = leave_req.from_date
                while cur <= leave_req.to_date:
                    TrainerAttendance.objects.update_or_create(
                        trainer=leave_req.trainer,
                        date=cur,
                        defaults={'status': 'Leave', 'check_in': None}
                    )
                    cur += timedelta(days=1)

            # Send activity notification to Trainer
            if leave_req.trainer and leave_req.trainer.user:
                send_notification(
                    recipient=leave_req.trainer.user,
                    title=f"Leave Request {status}",
                    message=f"Branch Head has {status.lower()} your leave request for {leave_req.from_date} to {leave_req.to_date}. Remark: {remark or 'None'}",
                    link_url="/trainer/leaves/apply/",
                    notification_type='LEAVE_REVIEW'
                )

            messages.success(request, f"Leave request marked as {status}.")
        else:
            messages.error(request, "Invalid status choice.")
    return redirect('branch_head:leave_list')


# ------------------- TRAINER ATTENDANCE REPORT -------------------

@branch_head_required
def trainer_attendance_report(request):
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    selected_trainer_id = request.GET.get('trainer', '').strip()

    trainers = TrainerProfile.objects.select_related('user').all()

    # Calculate days in month
    num_days = calendar.monthrange(selected_year, selected_month)[1]
    days_list = [date(selected_year, selected_month, day) for day in range(1, num_days + 1)]

    # Fetch attendance map
    report_rows = []
    target_trainers = trainers
    if selected_trainer_id:
        target_trainers = trainers.filter(id=selected_trainer_id)

    for trainer in target_trainers:
        att_qs = TrainerAttendance.objects.filter(
            trainer=trainer,
            date__year=selected_year,
            date__month=selected_month
        )
        att_map = {a.date.day: a.status for a in att_qs}

        days_status = []
        present_count = 0
        leave_count = 0
        absent_count = 0

        for d in days_list:
            st = att_map.get(d.day, 'Absent' if d.weekday() < 5 and d <= today else '-')
            days_status.append({'day': d.day, 'status': st, 'is_weekend': d.weekday() >= 5})
            if st == 'Present':
                present_count += 1
            elif st == 'Leave':
                leave_count += 1
            elif st == 'Absent':
                absent_count += 1

        report_rows.append({
            'trainer': trainer,
            'days': days_status,
            'present_count': present_count,
            'leave_count': leave_count,
            'absent_count': absent_count,
        })

    month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]

    return render(request, 'branch_head/attendance_report.html', {
        'report_rows': report_rows,
        'days_list': days_list,
        'trainers': trainers,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_trainer_id': selected_trainer_id,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
    })


@branch_head_required
def student_attendance_report(request):
    """
    Branch Head views Month-wise Day-by-Day Student Attendance Matrix.
    Shows daily status (Present, Absent, Leave, Sunday), totals, and attendance %.
    Allows filtering by Month, Year, Department, Course, and Trainer.
    """
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    dept_id = request.GET.get('department', '').strip()
    course_id = request.GET.get('course', '').strip()
    trainer_id = request.GET.get('trainer', '').strip()

    num_days = calendar.monthrange(selected_year, selected_month)[1]
    days_list = [date(selected_year, selected_month, day) for day in range(1, num_days + 1)]

    students = StudentProfile.objects.filter(is_active=True).select_related('course', 'trainer', 'department')
    if dept_id:
        students = students.filter(department_id=dept_id)
    if course_id:
        students = students.filter(course_id=course_id)
    if trainer_id:
        students = students.filter(trainer_id=trainer_id)

    report_rows = []
    for s in students:
        month_att = Attendance.objects.filter(
            student=s,
            date__year=selected_year,
            date__month=selected_month
        )
        att_map = {a.date.day: a.status for a in month_att}

        days_status = []
        p_count = 0
        l_count = 0
        a_count = 0

        for d in days_list:
            is_weekend = d.weekday() == 6
            st = att_map.get(d.day)
            if not st:
                if is_weekend:
                    st = 'SUN'
                elif d <= today and d.weekday() < 5:
                    st = 'Absent'
                else:
                    st = '-'

            if st == 'Present':
                p_count += 1
            elif st == 'Leave':
                l_count += 1
            elif st == 'Absent':
                a_count += 1

            days_status.append({
                'day': d.day,
                'status': st,
                'is_weekend': is_weekend,
            })

        total_sessions = p_count + l_count + a_count
        pct = round((p_count / total_sessions * 100), 1) if total_sessions > 0 else 0.0

        report_rows.append({
            'student': s,
            'days': days_status,
            'present_count': p_count,
            'leave_count': l_count,
            'absent_count': a_count,
            'total_sessions': total_sessions,
            'percentage': pct,
            'is_eligible': pct >= 75.0,
        })

    month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]
    departments = Department.objects.filter(is_active=True)
    courses = Course.objects.filter(is_active=True)
    trainers = TrainerProfile.objects.all()

    return render(request, 'branch_head/student_attendance_report.html', {
        'report_rows': report_rows,
        'days_list': days_list,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
        'departments': departments,
        'courses': courses,
        'trainers': trainers,
        'selected_dept': dept_id,
        'selected_course': course_id,
        'selected_trainer': trainer_id,
    })


@branch_head_required
def export_student_attendance_excel(request):
    """Exports Branch Head's filtered Monthly Student Attendance Matrix to Excel (.xlsx)."""
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    dept_id = request.GET.get('department', '').strip()
    course_id = request.GET.get('course', '').strip()
    trainer_id = request.GET.get('trainer', '').strip()

    students = StudentProfile.objects.filter(is_active=True).select_related('course', 'trainer')
    if dept_id:
        students = students.filter(department_id=dept_id)
    if course_id:
        students = students.filter(course_id=course_id)
    if trainer_id:
        students = students.filter(trainer_id=trainer_id)

    fname = f"DeviX_Student_Attendance_{selected_year}_{selected_month:02d}.xlsx"
    return export_monthly_student_attendance_excel_response(students, selected_year, selected_month, filename=fname)


@branch_head_required
def attendance_calendar(request):
    """
    Branch Head Visual Attendance Calendar:
    Two separate tabbed sections:
    1. Trainer Attendance Calendar (Present: Green, Half-Day: Amber, Absent: Red, Sunday: Gray, Leave: Blue)
    2. Student Attendance Calendar (Present: Green, Absent: Red, Sunday: Gray)
    """
    today = date.today()
    active_tab = request.GET.get('tab', 'trainer')
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    trainers = TrainerProfile.objects.select_related('user', 'department').all().order_by('trainer_id')
    students = StudentProfile.objects.filter(is_active=True).select_related('course', 'trainer').order_by('name')

    selected_trainer_id = request.GET.get('trainer_id')
    selected_student_id = request.GET.get('student_id')

    # Selected trainer object
    if selected_trainer_id:
        current_trainer = trainers.filter(id=selected_trainer_id).first()
    else:
        current_trainer = trainers.first()

    # Selected student object
    if selected_student_id:
        current_student = students.filter(id=selected_student_id).first()
    else:
        current_student = students.first()

    # Build Trainer calendar grid
    trainer_calendar_data = None
    if current_trainer:
        trainer_records = TrainerAttendance.objects.filter(
            trainer=current_trainer,
            date__year=selected_year,
            date__month=selected_month
        )
        t_records_map = {r.date.day: r for r in trainer_records}

        # Include approved leaves
        trainer_leaves = LeaveRequest.objects.filter(
            trainer=current_trainer,
            status='Approved',
            from_date__year__lte=selected_year,
            to_date__year__gte=selected_year
        )
        for l in trainer_leaves:
            cur = l.from_date
            while cur <= l.to_date:
                if cur.year == selected_year and cur.month == selected_month:
                    if cur.day not in t_records_map:
                        t_records_map[cur.day] = {
                            'status': 'Leave' if l.leave_duration_type == 'FULL_DAY' else 'Half_Day',
                            'remark': f"Approved Leave ({l.get_leave_duration_type_display()}): {l.reason[:30]}"
                        }
                cur += timedelta(days=1)

        trainer_calendar_data = build_month_calendar_grid(selected_year, selected_month, t_records_map, today=today)

    # Build Student calendar grid
    student_calendar_data = None
    if current_student:
        student_records = Attendance.objects.filter(
            student=current_student,
            date__year=selected_year,
            date__month=selected_month
        )
        s_records_map = {r.date.day: r.status for r in student_records}
        student_calendar_data = build_month_calendar_grid(selected_year, selected_month, s_records_map, today=today)

    month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]

    return render(request, 'branch_head/attendance_calendar.html', {
        'active_tab': active_tab,
        'trainers': trainers,
        'students': students,
        'current_trainer': current_trainer,
        'current_student': current_student,
        'trainer_calendar_data': trainer_calendar_data,
        'student_calendar_data': student_calendar_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
        'today': today,
    })


# ------------------- SALARY MANAGEMENT -------------------

@branch_head_required
def salary_calculator(request):
    """
    Auto-calculates salary:
    - Base Monthly Salary
    - Per Day Rate = monthly_salary / working_days
    - Deductions:
        * 1 Full Day Leave = 1.0 day deduction
        * 1 Half Day Leave = 0.5 day deduction
        * 1 Half Day Punch Penalty (>20 min late or early checkout) = 0.5 day deduction
        * 1 Unapproved Absent Day = 1.0 day deduction
    - Itemized breakdown for clear salary slip presentation.
    """
    initial_calc = None
    form = SalaryGenerationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        trainer = form.cleaned_data['trainer']
        month = int(form.cleaned_data['month'])
        year = int(form.cleaned_data['year'])
        working_days = form.cleaned_data['working_days']
        max_paid_leaves = form.cleaned_data.get('max_paid_leaves', 0)
        notes = form.cleaned_data.get('notes', '')

        # Attendance query for the month
        att_qs = TrainerAttendance.objects.filter(
            trainer=trainer,
            date__year=year,
            date__month=month
        )
        present_days = att_qs.filter(status='Present').count()
        half_day_punches = att_qs.filter(status='Half_Day').count()

        # Approved Leaves overlapping the month
        approved_leaves = LeaveRequest.objects.filter(
            trainer=trainer,
            status='Approved',
            from_date__year__lte=year,
            to_date__year__gte=year
        )

        full_day_leaves_count = 0.0
        half_day_leaves_count = 0.0

        num_days_in_month = calendar.monthrange(year, month)[1]
        for day_num in range(1, num_days_in_month + 1):
            check_date = date(year, month, day_num)
            for l in approved_leaves:
                if l.from_date <= check_date <= l.to_date:
                    if l.leave_duration_type == 'HALF_DAY':
                        half_day_leaves_count += 1.0
                    else:
                        full_day_leaves_count += 1.0
                    break

        total_leave_days = Decimal(str(full_day_leaves_count + (half_day_leaves_count * 0.5)))
        
        # Calculate unapproved absent days
        # Accounted days: present_days + leaves + half_day_punches
        accounted_days = Decimal(present_days) + Decimal(str(full_day_leaves_count)) + (Decimal(str(half_day_leaves_count)) * Decimal('0.5')) + (Decimal(half_day_punches) * Decimal('0.5'))
        absent_days = max(Decimal('0.0'), Decimal(working_days) - accounted_days)

        monthly_salary = trainer.monthly_salary
        per_day_salary = (monthly_salary / Decimal(working_days)).quantize(Decimal('0.01')) if working_days > 0 else Decimal('0.00')

        # Total deduction days
        # All leaves and half day penalties incur salary deduction as specified
        total_deduction_days = (
            (Decimal(str(full_day_leaves_count)) * Decimal('1.0')) +
            (Decimal(str(half_day_leaves_count)) * Decimal('0.5')) +
            (Decimal(half_day_punches) * Decimal('0.5')) +
            (absent_days * Decimal('1.0'))
        )

        total_deduction = (total_deduction_days * per_day_salary).quantize(Decimal('0.01'))
        net_salary = max(Decimal('0.00'), (monthly_salary - total_deduction).quantize(Decimal('0.01')))

        # Detailed breakdown amounts for slip display
        full_day_leave_amount = (Decimal(str(full_day_leaves_count)) * per_day_salary).quantize(Decimal('0.01'))
        half_day_leave_amount = ((Decimal(str(half_day_leaves_count)) * Decimal('0.5')) * per_day_salary).quantize(Decimal('0.01'))
        half_day_punch_amount = ((Decimal(half_day_punches) * Decimal('0.5')) * per_day_salary).quantize(Decimal('0.01'))
        absent_amount = (absent_days * per_day_salary).quantize(Decimal('0.01'))

        if 'save_salary' in request.POST:
            record, created = SalaryRecord.objects.update_or_create(
                trainer=trainer,
                month=month,
                year=year,
                defaults={
                    'monthly_salary': monthly_salary,
                    'working_days': working_days,
                    'present_days': Decimal(present_days),
                    'half_day_punches': Decimal(half_day_punches),
                    'full_day_leaves': Decimal(str(full_day_leaves_count)),
                    'half_day_leaves': Decimal(str(half_day_leaves_count)),
                    'leave_days': total_leave_days,
                    'absent_days': absent_days,
                    'total_deduction_days': total_deduction_days,
                    'per_day_salary': per_day_salary,
                    'deduction': total_deduction,
                    'net_salary': net_salary,
                    'generated_by': request.user,
                    'notes': notes,
                }
            )
            messages.success(request, f"Salary record for {trainer.full_name} ({calendar.month_name[month]} {year}) generated successfully!")
            return redirect('branch_head:salary_slip', pk=record.pk)

        initial_calc = {
            'trainer': trainer,
            'month': month,
            'month_name': calendar.month_name[month],
            'year': year,
            'monthly_salary': monthly_salary,
            'working_days': working_days,
            'present_days': present_days,
            'half_day_punches': half_day_punches,
            'full_day_leaves': full_day_leaves_count,
            'half_day_leaves': half_day_leaves_count,
            'total_leave_days': total_leave_days,
            'absent_days': absent_days,
            'total_deduction_days': total_deduction_days,
            'per_day_salary': per_day_salary,
            'full_day_leave_amount': full_day_leave_amount,
            'half_day_leave_amount': half_day_leave_amount,
            'half_day_punch_amount': half_day_punch_amount,
            'absent_amount': absent_amount,
            'deduction': total_deduction,
            'net_salary': net_salary,
        }

    return render(request, 'branch_head/salary_calculator.html', {
        'form': form,
        'calc': initial_calc,
    })

    return render(request, 'branch_head/salary_calculator.html', {
        'form': form,
        'calc': initial_calc,
    })


@branch_head_required
def salary_records_list(request):
    records = SalaryRecord.objects.select_related('trainer', 'trainer__user', 'generated_by').all().order_by('-year', '-month')
    return render(request, 'branch_head/salary_records.html', {'records': records})


@branch_head_required
def salary_slip_view(request, pk):
    record = get_object_or_404(SalaryRecord.objects.select_related('trainer', 'trainer__user', 'trainer__department', 'generated_by'), pk=pk)
    return render(request, 'branch_head/salary_slip.html', {'record': record})
