from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta, time
from decimal import Decimal
import calendar

from accounts.decorators import trainer_required
from accounts.models import User
from academy.models import (
    Department, Course, TrainerProfile, StudentProfile,
    TrainerNotice, StudentDirectMessage, CourseResource,
    generate_student_id
)
from attendance.models import Attendance, TrainerAttendance, LeaveRequest, StudentLeaveRequest
from attendance.calendar_utils import build_month_calendar_grid
from academy.notifications import send_notification
from academy.excel_utils import (
    export_students_detail_excel_response,
    export_monthly_student_attendance_excel_response
)
from academy.forms import (
    TrainerProfileEditForm, StudentCreationForm,
    TrainerNoticeForm, StudentDirectMessageForm, CourseResourceForm,
    generate_secure_password
)
from attendance.forms import LeaveRequestForm, StudentLeaveReviewForm


@trainer_required
def dashboard(request):
    """Trainer Dashboard overview."""
    if not hasattr(request.user, 'trainer_profile'):
        messages.error(request, "Trainer profile not found. Please contact Branch Head.")
        return redirect('accounts:logout')
    trainer = request.user.trainer_profile
    today = date.today()

    # My students count
    my_students_count = trainer.students.filter(is_active=True).count()

    # Today's attendance status
    today_att = TrainerAttendance.objects.filter(trainer=trainer, date=today).first()

    # Leave balance summary (e.g. approved leaves this month)
    leaves_this_month = LeaveRequest.objects.filter(
        trainer=trainer,
        status='Approved',
        from_date__year=today.year,
        from_date__month=today.month
    )
    approved_leave_days = sum(l.total_days for l in leaves_this_month)
    pending_leaves_count = LeaveRequest.objects.filter(trainer=trainer, status='Pending').count()

    # Recent student attendance marked
    recent_student_att_count = Attendance.objects.filter(
        student__trainer=trainer,
        date=today
    ).count()

    return render(request, 'trainer/dashboard.html', {
        'trainer': trainer,
        'my_students_count': my_students_count,
        'today_att': today_att,
        'approved_leave_days': approved_leave_days,
        'pending_leaves_count': pending_leaves_count,
        'recent_student_att_count': recent_student_att_count,
        'today': today,
    })


@trainer_required
def my_profile(request):
    """Trainer viewing & editing own profile. Cannot edit ID or salary."""
    trainer = request.user.trainer_profile
    if request.method == 'POST':
        form = TrainerProfileEditForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            trainer = form.save()
            trainer.user.phone = trainer.phone
            trainer.user.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('trainer:my_profile')
    else:
        form = TrainerProfileEditForm(instance=trainer)
    return render(request, 'trainer/profile.html', {'form': form, 'trainer': trainer})


@trainer_required
def student_list(request):
    """Trainer views only their assigned students."""
    trainer = request.user.trainer_profile
    query = request.GET.get('q', '').strip()

    students = trainer.students.filter(is_active=True).select_related('course', 'department')
    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(course__name__icontains=query)
        )

    return render(request, 'trainer/student_list.html', {
        'trainer': trainer,
        'students': students,
        'query': query,
    })


@trainer_required
def export_my_students_excel(request):
    """Trainer exports all their assigned students to an Excel (.xlsx) spreadsheet."""
    trainer = request.user.trainer_profile
    query = request.GET.get('q', '').strip()

    students = trainer.students.filter(is_active=True).select_related('user', 'department', 'course')
    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(course__name__icontains=query)
        )

    fname = f"My_Students_{trainer.trainer_id}.xlsx"
    return export_students_detail_excel_response(students, filename=fname)


@trainer_required
def student_add(request):
    """
    Trainer enrolls a new student:
    - Course filtered via AJAX by department
    - Auto-generates student ID (like DVX-2026-0001)
    - Auto-generates random password
    - Displays credential card with copy and print buttons
    """
    trainer = request.user.trainer_profile
    if request.method == 'POST':
        form = StudentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data

            # Generate student ID and secure random password
            student_id = generate_student_id()
            raw_password = generate_secure_password()
            username = f"std_{student_id.lower().replace('-', '_')}"

            # Create User account
            name_parts = data['name'].strip().split()
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            user = User(
                username=username,
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                role=User.Role.STUDENT,
                phone=data['phone'],
                must_change_password=True
            )
            user.set_password(raw_password)
            user.save()

            # Create StudentProfile
            student = StudentProfile(
                user=user,
                student_id=student_id,
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                department=data['department'],
                course=data['course'],
                trainer=trainer,  # Automatically assigned to logged-in trainer
                course_duration=data.get('course_duration') or (data['course'].duration if data['course'] else ''),
                start_date=data['start_date'],
                end_date=data.get('end_date'),
                student_class=data.get('student_class', ''),
                profile_picture=data.get('profile_picture'),
                linkedin=data.get('linkedin', ''),
                github=data.get('github', ''),
                is_active=True
            )
            student.save()

            # Activity Notifications: Welcome student & inform Branch Head
            send_notification(
                recipient=user,
                title="Welcome to DeviX Academy!",
                message=f"You have been enrolled in {student.course.name if student.course else 'your course'} by Trainer {trainer.full_name}. Student ID: {student.student_id}",
                link_url="/student/dashboard/",
                notification_type='STUDENT_ENROLLED'
            )
            branch_heads = User.objects.filter(role='BRANCH_HEAD')
            send_notification(
                recipient=branch_heads,
                title=f"New Student Enrolled: {student.name}",
                message=f"Trainer {trainer.full_name} enrolled {student.name} ({student.student_id}) in {student.course.name if student.course else 'Course'}.",
                link_url=f"/branch-head/students/",
                notification_type='STUDENT_ENROLLED'
            )

            # Render credential display screen
            return render(request, 'trainer/student_created.html', {
                'student': student,
                'username': username,
                'raw_password': raw_password,
                'trainer': trainer,
            })
    else:
        form = StudentCreationForm(initial={'start_date': date.today()})

    return render(request, 'trainer/student_form.html', {
        'form': form,
        'trainer': trainer,
    })


@trainer_required
def student_detail(request, pk):
    """View assigned student profile & attendance."""
    trainer = request.user.trainer_profile
    student = get_object_or_404(trainer.students.select_related('course', 'department'), pk=pk)
    stats = student.get_attendance_stats()
    attendance_records = student.attendances.order_by('-date')[:25]
    return render(request, 'trainer/student_detail.html', {
        'student': student,
        'stats': stats,
        'attendance_records': attendance_records,
    })


@trainer_required
def mark_student_attendance(request):
    """Mark day-wise attendance for assigned students."""
    trainer = request.user.trainer_profile
    selected_date_str = request.GET.get('date', date.today().isoformat())

    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()

    students = trainer.students.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        # Process attendance submissions
        marked_count = 0
        for student in students:
            status_val = request.POST.get(f"attendance_{student.id}")
            if status_val in ['Present', 'Absent', 'Leave']:
                Attendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    defaults={
                        'status': status_val,
                        'marked_by': request.user
                    }
                )
                marked_count += 1
        messages.success(request, f"Attendance for {marked_count} students saved for {selected_date.strftime('%d %b %Y')}.")
        return redirect(f"{request.path}?date={selected_date.isoformat()}")

    # Fetch existing attendances for this date
    existing_records = Attendance.objects.filter(
        student__trainer=trainer,
        date=selected_date
    )
    existing_map = {att.student_id: att.status for att in existing_records}

    student_rows = []
    for s in students:
        student_rows.append({
            'student': s,
            'status': existing_map.get(s.id, 'Present')  # Default to Present for quick marking
        })

    return render(request, 'trainer/attendance_mark.html', {
        'selected_date': selected_date,
        'student_rows': student_rows,
        'today': date.today(),
    })


@trainer_required
def mark_my_attendance(request):
    """
    Punch In: Trainer logs arrival in the morning.
    Grace rule: If punch-in is more than 20 minutes after expected_start_time,
    marked as 'Half_Day' automatically.
    """
    trainer = request.user.trainer_profile
    today = date.today()
    now_time = timezone.localtime().time()

    att, created = TrainerAttendance.objects.get_or_create(
        trainer=trainer,
        date=today,
        defaults={
            'status': 'Present',
            'check_in': now_time
        }
    )

    if not created:
        messages.info(request, f"You have already punched in for today at {att.check_in.strftime('%I:%M %p') if att.check_in else 'N/A'}.")
        return redirect('trainer:dashboard')

    # Calculate arrival delay against scheduled start time
    expected = trainer.expected_start_time or time(9, 0)
    expected_minutes = expected.hour * 60 + expected.minute
    actual_minutes = now_time.hour * 60 + now_time.minute
    late_minutes = actual_minutes - expected_minutes

    if late_minutes > 20:
        att.status = 'Half_Day'
        att.remark = f"Late Punch-In by {late_minutes} mins (Scheduled: {expected.strftime('%I:%M %p')}, Grace: 20m) -> Half Day marked"
        att.save()
        messages.warning(
            request,
            f"Punched In at {now_time.strftime('%I:%M %p')}. You arrived {late_minutes} minutes late (>20 min grace period). Half Day has been marked for today."
        )
    else:
        att.status = 'Present'
        att.remark = f"Punched in on time ({now_time.strftime('%I:%M %p')})"
        att.save()
        messages.success(
            request,
            f"Good morning, {trainer.full_name}! Punched In successfully at {now_time.strftime('%I:%M %p')} on time. Shift target: {trainer.daily_working_hours} hours."
        )

    return redirect('trainer:dashboard')


@trainer_required
def punch_out(request):
    """
    Punch Out: Trainer logs departure in the evening.
    Grace rule: If total hours logged is deficient by > 20 minutes from daily_working_hours,
    marked as 'Half_Day' automatically.
    """
    trainer = request.user.trainer_profile
    today = date.today()
    now_time = timezone.localtime().time()

    att = TrainerAttendance.objects.filter(trainer=trainer, date=today).first()
    if not att or not att.check_in:
        messages.error(request, "You must punch in first before you can punch out.")
        return redirect('trainer:dashboard')

    if att.check_out:
        messages.info(request, f"You have already punched out today at {att.check_out.strftime('%I:%M %p')}.")
        return redirect('trainer:dashboard')

    att.check_out = now_time

    # Calculate duration
    check_in_minutes = att.check_in.hour * 60 + att.check_in.minute
    check_out_minutes = now_time.hour * 60 + now_time.minute
    worked_minutes = max(0, check_out_minutes - check_in_minutes)
    hours_worked = round(Decimal(worked_minutes) / Decimal(60), 2)
    att.working_hours_recorded = hours_worked

    required_minutes = int(float(trainer.daily_working_hours) * 60)
    deficit_minutes = required_minutes - worked_minutes

    if deficit_minutes > 20:
        att.status = 'Half_Day'
        notes = f"Early Punch-Out by {deficit_minutes} mins (Logged: {hours_worked}h of {trainer.daily_working_hours}h required, >20 min short) -> Half Day marked."
        att.remark = f"{att.remark} | {notes}".strip(" |")
        att.save()
        messages.warning(
            request,
            f"Punched Out at {now_time.strftime('%I:%M %p')}. Total logged: {hours_worked} hrs. Shift was short by {deficit_minutes} mins (>20 min grace). Half Day marked."
        )
    else:
        if att.status != 'Half_Day':
            att.status = 'Present'
            notes = f"Completed full shift ({hours_worked} hrs of {trainer.daily_working_hours}h required)."
        else:
            notes = f"Shift concluded. Total logged: {hours_worked} hrs (Half Day retained from late arrival)."
        att.remark = f"{att.remark} | {notes}".strip(" |")
        att.save()
        messages.success(
            request,
            f"Punched Out successfully at {now_time.strftime('%I:%M %p')}. Total logged: {hours_worked} hrs today ({att.status})."
        )

    return redirect('trainer:dashboard')


@trainer_required
def apply_leave(request):
    """Trainer applies for leave and views status history."""
    trainer = request.user.trainer_profile
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.trainer = trainer
            leave.status = 'Pending'
            leave.save()

            # Notify Branch Head about Trainer Leave Request
            branch_heads = User.objects.filter(role='BRANCH_HEAD')
            send_notification(
                recipient=branch_heads,
                title=f"Leave Application from {trainer.full_name}",
                message=f"{trainer.full_name} ({trainer.trainer_id}) applied for {leave.total_days} day(s) leave ({leave.from_date} to {leave.to_date}). Reason: {leave.reason[:70]}",
                link_url="/branch-head/leaves/",
                notification_type='LEAVE_REQUEST'
            )

            messages.success(request, f"Leave application for {leave.total_days} day(s) submitted successfully. Waiting for Branch Head review.")
            return redirect('trainer:apply_leave')
    else:
        form = LeaveRequestForm(initial={'from_date': date.today()})

    leave_history = trainer.leave_requests.order_by('-applied_on')
    return render(request, 'trainer/leave_apply.html', {
        'form': form,
        'leave_history': leave_history,
    })


@trainer_required
def my_attendance_summary(request):
    """Monthly attendance calendar & summary for the trainer."""
    trainer = request.user.trainer_profile
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    records = TrainerAttendance.objects.filter(
        trainer=trainer,
        date__year=selected_year,
        date__month=selected_month
    )
    records_map = {r.date.day: r for r in records}

    # Also map any approved leaves onto the calendar for the trainer
    approved_leaves = LeaveRequest.objects.filter(
        trainer=trainer,
        status='Approved',
        from_date__year__lte=selected_year,
        to_date__year__gte=selected_year
    )
    for l in approved_leaves:
        cur_d = l.from_date
        while cur_d <= l.to_date:
            if cur_d.year == selected_year and cur_d.month == selected_month:
                if cur_d.day not in records_map:
                    records_map[cur_d.day] = {
                        'status': 'Leave' if l.leave_duration_type == 'FULL_DAY' else 'Half_Day',
                        'remark': f"Approved Leave ({l.get_leave_duration_type_display()}): {l.reason[:30]}"
                    }
            cur_d += timedelta(days=1)

    calendar_data = build_month_calendar_grid(selected_year, selected_month, records_map, today=today)

    month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]

    return render(request, 'trainer/attendance_summary.html', {
        'trainer': trainer,
        'calendar_data': calendar_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
        'today': today,
    })


@trainer_required
def student_attendance_report(request):
    """
    Trainer views Month-wise Day-by-Day Student Attendance Matrix for their assigned students.
    Shows daily status (Present, Absent, Leave, Sunday), totals, and attendance %.
    """
    trainer = request.user.trainer_profile
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    course_id = request.GET.get('course', '').strip()

    num_days = calendar.monthrange(selected_year, selected_month)[1]
    days_list = [date(selected_year, selected_month, day) for day in range(1, num_days + 1)]

    students = trainer.students.filter(is_active=True).select_related('course', 'department')
    if course_id:
        students = students.filter(course_id=course_id)

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
    courses = Course.objects.filter(is_active=True)

    return render(request, 'trainer/student_attendance_report.html', {
        'trainer': trainer,
        'report_rows': report_rows,
        'days_list': days_list,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
        'courses': courses,
        'selected_course': course_id,
    })


@trainer_required
def export_student_attendance_excel(request):
    """Exports Trainer's assigned students monthly attendance matrix to Excel (.xlsx)."""
    trainer = request.user.trainer_profile
    today = date.today()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))
    course_id = request.GET.get('course', '').strip()

    students = trainer.students.filter(is_active=True).select_related('course')
    if course_id:
        students = students.filter(course_id=course_id)

    fname = f"My_Students_Attendance_{trainer.trainer_id}_{selected_year}_{selected_month:02d}.xlsx"
    return export_monthly_student_attendance_excel_response(students, selected_year, selected_month, filename=fname)


# ------------------- TRAINER LEAVE / HOLIDAY NOTICES -------------------

@trainer_required
def notice_list(request):
    """List notices posted by this trainer for their assigned students."""
    trainer = request.user.trainer_profile
    notices = trainer.notices.all().order_by('-created_at')
    form = TrainerNoticeForm()
    return render(request, 'trainer/notice_list.html', {
        'trainer': trainer,
        'notices': notices,
        'form': form,
    })


@trainer_required
def notice_create(request):
    """Trainer posts a Leave, Holiday, or Class Announcement for assigned students."""
    trainer = request.user.trainer_profile
    if request.method == 'POST':
        form = TrainerNoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.trainer = trainer
            notice.department = trainer.department
            notice.save()

            # Activity Notification: Alert all assigned students
            assigned_students = trainer.students.filter(is_active=True).select_related('user')
            recipients = [s.user for s in assigned_students if s.user]
            send_notification(
                recipient=recipients,
                title=f"Notice: {notice.title}",
                message=f"Trainer {trainer.full_name}: {notice.message[:90]}",
                link_url="/student/notices/",
                notification_type='NOTICE'
            )

            messages.success(request, f"Notice '{notice.title}' published successfully! All your assigned students will see this in their Leave & Holiday section.")
            return redirect('trainer:notice_list')
    else:
        form = TrainerNoticeForm()
    return render(request, 'trainer/notice_form.html', {'form': form, 'trainer': trainer})


@trainer_required
def notice_delete(request, pk):
    """Delete a notice."""
    trainer = request.user.trainer_profile
    notice = get_object_or_404(trainer.notices, pk=pk)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, "Notice deleted successfully.")
    return redirect('trainer:notice_list')


# ------------------- DIRECT STUDENT MESSAGES & 1-ON-1 CHAT -------------------

@trainer_required
def message_student(request):
    """Trainer sends a direct message, PDF, learning material, or link to a specific student."""
    trainer = request.user.trainer_profile
    initial_student_id = request.GET.get('student')

    if request.method == 'POST':
        form = StudentDirectMessageForm(request.POST, request.FILES, trainer=trainer)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.trainer = trainer
            msg.sender_role = 'TRAINER'
            msg.save()

            if msg.student and msg.student.user:
                send_notification(
                    recipient=msg.student.user,
                    title=f"Message from {trainer.full_name}",
                    message=f"{msg.subject}: {msg.message[:80]}",
                    link_url="/student/messages/",
                    notification_type='MESSAGE'
                )

            messages.success(request, f"Message sent successfully to {msg.student.name}!")
            return redirect('trainer:student_conversation', student_id=msg.student.id)
    else:
        initial = {}
        if initial_student_id:
            initial['student'] = initial_student_id
        form = StudentDirectMessageForm(initial=initial, trainer=trainer)

    return render(request, 'trainer/message_form.html', {
        'form': form,
        'trainer': trainer,
    })


@trainer_required
def message_history(request):
    """Trainer views overview of individual 1-on-1 conversations with assigned students."""
    trainer = request.user.trainer_profile
    students = trainer.students.filter(is_active=True).order_by('name')
    
    # Get latest message per student
    conversation_list = []
    for s in students:
        thread = StudentDirectMessage.objects.filter(trainer=trainer, student=s).order_by('-created_at')
        last_msg = thread.first()
        unread_count = thread.filter(is_read=False, sender_role='STUDENT').count()
        conversation_list.append({
            'student': s,
            'last_message': last_msg,
            'unread_count': unread_count,
            'total_count': thread.count(),
        })

    return render(request, 'trainer/message_history.html', {
        'trainer': trainer,
        'conversation_list': conversation_list,
    })


@trainer_required
def student_conversation(request, student_id):
    """1-on-1 private chat thread between trainer and a specific assigned student."""
    trainer = request.user.trainer_profile
    student = get_object_or_404(trainer.students, id=student_id)

    # Mark incoming student replies as read
    StudentDirectMessage.objects.filter(
        trainer=trainer,
        student=student,
        sender_role='STUDENT',
        is_read=False
    ).update(is_read=True)

    if request.method == 'POST':
        form = StudentDirectMessageForm(request.POST, request.FILES, trainer=trainer)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.trainer = trainer
            msg.student = student
            msg.sender_role = 'TRAINER'
            msg.save()

            if student and student.user:
                send_notification(
                    recipient=student.user,
                    title=f"Message from {trainer.full_name}",
                    message=f"{msg.subject}: {msg.message[:80]}",
                    link_url="/student/messages/",
                    notification_type='MESSAGE'
                )

            messages.success(request, "Message sent.")
            return redirect('trainer:student_conversation', student_id=student.id)
    else:
        form = StudentDirectMessageForm(initial={'student': student.id, 'subject': f'Conversation with {student.name}'}, trainer=trainer)

    thread_messages = StudentDirectMessage.objects.filter(
        trainer=trainer,
        student=student
    ).order_by('created_at')

    return render(request, 'trainer/student_conversation.html', {
        'trainer': trainer,
        'student': student,
        'thread_messages': thread_messages,
        'form': form,
    })


# ------------------- COURSE LEARNING RESOURCES -------------------

@trainer_required
def resource_list(request):
    """Trainer manages learning resources uploaded for courses."""
    trainer = request.user.trainer_profile
    course_filter = request.GET.get('course', '').strip()

    resources = trainer.uploaded_resources.select_related('course', 'department').all()
    if course_filter:
        resources = resources.filter(course_id=course_filter)

    courses = Course.objects.filter(is_active=True).order_by('name')
    return render(request, 'trainer/resource_list.html', {
        'trainer': trainer,
        'resources': resources,
        'courses': courses,
        'selected_course': course_filter,
    })


@trainer_required
def resource_create(request):
    """Trainer uploads learning resources (File/PDF, Link, Notes) tagged by Course & Department."""
    trainer = request.user.trainer_profile
    if request.method == 'POST':
        form = CourseResourceForm(request.POST, request.FILES)
        if form.is_valid():
            res = form.save(commit=False)
            res.trainer = trainer
            res.save()

            # Activity Notification: Alert students enrolled in this course
            enrolled = StudentProfile.objects.filter(course=res.course, is_active=True).select_related('user')
            recipients = [s.user for s in enrolled if s.user]
            send_notification(
                recipient=recipients,
                title=f"New Study Material: {res.title}",
                message=f"Trainer {trainer.full_name} shared new study materials for {res.course.name}.",
                link_url="/student/resources/",
                notification_type='RESOURCE'
            )

            messages.success(request, f"Resource '{res.title}' added to {res.course.name}! Students enrolled in this course can now access it.")
            return redirect('trainer:resource_list')
    else:
        initial = {}
        if trainer.department:
            initial['department'] = trainer.department.id
        form = CourseResourceForm(initial=initial)

    return render(request, 'trainer/resource_form.html', {
        'form': form,
        'trainer': trainer,
    })


@trainer_required
def resource_delete(request, pk):
    """Delete a course resource."""
    trainer = request.user.trainer_profile
    resource = get_object_or_404(trainer.uploaded_resources, pk=pk)
    if request.method == 'POST':
        title = resource.title
        resource.delete()
        messages.success(request, f"Resource '{title}' deleted.")
    return redirect('trainer:resource_list')


# ------------------- STUDENT LEAVE REQUESTS REVIEW -------------------

@trainer_required
def student_leave_list(request):
    """
    Trainer views and manages leave requests submitted by assigned students.
    Can filter by status ('Pending', 'Approved', 'Rejected').
    """
    trainer = request.user.trainer_profile
    status_filter = request.GET.get('status', '').strip()

    leaves = StudentLeaveRequest.objects.filter(
        student__trainer=trainer
    ).select_related('student', 'student__course', 'student__department').order_by('-applied_on')

    if status_filter in ['Pending', 'Approved', 'Rejected']:
        leaves = leaves.filter(status=status_filter)

    pending_count = StudentLeaveRequest.objects.filter(
        student__trainer=trainer,
        status='Pending'
    ).count()

    review_form = StudentLeaveReviewForm()

    return render(request, 'trainer/student_leave_list.html', {
        'trainer': trainer,
        'leaves': leaves,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'review_form': review_form,
    })


@trainer_required
def student_leave_action(request, pk):
    """
    Trainer reviews (Accepts or Rejects) a student's leave request.
    - If Accepted (Approved):
      Marks 'Leave' on Student Attendance for all days in the requested date range.
    - If Rejected:
      Reverts any 'Leave' status to 'Absent' if student does not attend.
    - Sends an activity notification to the student with approval/rejection & remark.
    """
    trainer = request.user.trainer_profile
    leave = get_object_or_404(
        StudentLeaveRequest.objects.select_related('student', 'student__user'),
        pk=pk,
        student__trainer=trainer
    )

    if request.method == 'POST':
        action_status = request.POST.get('status', '').strip()
        remark = request.POST.get('trainer_remark', '').strip()

        if action_status in ['Approved', 'Rejected']:
            leave.status = action_status
            leave.trainer_remark = remark
            leave.reviewed_by = request.user
            leave.save()

            if action_status == 'Approved':
                # Mark 'Leave' on attendance records for each day in the range
                cur_d = leave.from_date
                while cur_d <= leave.to_date:
                    Attendance.objects.update_or_create(
                        student=leave.student,
                        date=cur_d,
                        defaults={
                            'status': 'Leave',
                            'marked_by': request.user
                        }
                    )
                    cur_d += timedelta(days=1)
                messages.success(
                    request,
                    f"Leave approved for {leave.student.name} ({leave.from_date} to {leave.to_date}). "
                    f"Attendance automatically marked as 'Leave'."
                )
            else:
                # If rejected, ensure any existing 'Leave' marking on these dates reverts to 'Absent'
                Attendance.objects.filter(
                    student=leave.student,
                    date__gte=leave.from_date,
                    date__lte=leave.to_date,
                    status='Leave'
                ).update(status='Absent', marked_by=request.user)
                messages.warning(
                    request,
                    f"Leave rejected for {leave.student.name}. Non-attendance will be marked as 'Absent'."
                )

            # Send activity notification to student
            if leave.student.user:
                send_notification(
                    recipient=leave.student.user,
                    title=f"Leave Application {action_status}",
                    message=f"Trainer {trainer.full_name} has {action_status.lower()} your leave request ({leave.from_date} to {leave.to_date}). Remark: {remark or 'None'}",
                    link_url="/student/leave/apply/",
                    notification_type='LEAVE_REVIEW'
                )

            return redirect('trainer:student_leaves')
        else:
            messages.error(request, "Invalid leave action selected.")

    return redirect('trainer:student_leaves')

