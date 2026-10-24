from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
import calendar

from accounts.decorators import student_required
from academy.models import TrainerNotice, StudentDirectMessage, CourseResource
from academy.forms import StudentProfileEditForm, StudentReplyMessageForm
from academy.notifications import send_notification
from attendance.models import Attendance, StudentLeaveRequest
from attendance.forms import StudentLeaveRequestForm
from attendance.calendar_utils import build_month_calendar_grid


@student_required
def dashboard(request):
    """
    Student Dashboard:
    - Name, student ID, course, course duration, start/end dates.
    - Assigned Trainer FULL Profile Card (including LinkedIn, GitHub, X, Instagram, YouTube).
    - Attendance summary and certificate eligibility alert.
    - Monthly attendance visual calendar (Present: Green, Absent: Red, Sunday: Gray).
    - Recent Trainer Leave / Holiday Notices banner alert.
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Student profile not found. Please contact Branch Head.")
        return redirect('accounts:logout')
    student = request.user.student_profile
    trainer = student.trainer
    today = date.today()

    stats = student.get_attendance_stats()
    attendance_records = student.attendances.order_by('-date')

    # Visual Calendar Generation for chosen month & year
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    month_att = student.attendances.filter(
        date__year=selected_year,
        date__month=selected_month
    )
    records_map = {a.date.day: a.status for a in month_att}

    calendar_data = build_month_calendar_grid(
        selected_year,
        selected_month,
        records_map,
        today=today
    )

    month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = [today.year - 1, today.year, today.year + 1]

    # Fetch active notices from the assigned trainer
    recent_notices = []
    if trainer:
        recent_notices = TrainerNotice.objects.filter(
            trainer=trainer,
            is_active=True
        ).order_by('-created_at')[:3]

    # Unread counts
    unread_messages_count = student.unread_messages_count
    unread_notices_count = student.unread_notices_count

    return render(request, 'student/dashboard.html', {
        'student': student,
        'trainer': trainer,
        'stats': stats,
        'attendance_records': attendance_records,
        'calendar_data': calendar_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'month_names': month_names,
        'years': years,
        'recent_notices': recent_notices,
        'unread_messages_count': unread_messages_count,
        'unread_notices_count': unread_notices_count,
        'today': today,
    })


@student_required
def edit_profile(request):
    """Student edits own profile (name, student_class, profile picture, social links)."""
    student = request.user.student_profile
    if request.method == 'POST':
        form = StudentProfileEditForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            student.user.first_name = student.name.split()[0]
            student.user.last_name = " ".join(student.name.split()[1:]) if len(student.name.split()) > 1 else ""
            student.user.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('student:dashboard')
    else:
        form = StudentProfileEditForm(instance=student)

    return render(request, 'student/profile.html', {
        'form': form,
        'student': student,
    })


@student_required
def notices_list(request):
    """
    Leave & Holiday Notices section:
    Shows ONLY notices posted by the student's assigned trainer (and related department).
    Automatically marks notices as read for this student.
    """
    student = request.user.student_profile
    trainer = student.trainer

    if not trainer:
        notices = []
    else:
        notices = TrainerNotice.objects.filter(
            trainer=trainer,
            is_active=True
        ).order_by('-created_at')

        # Mark all as read by this student
        for notice in notices:
            if student not in notice.read_by.all():
                notice.read_by.add(student)

    return render(request, 'student/notices.html', {
        'student': student,
        'trainer': trainer,
        'notices': notices,
    })


@student_required
def messages_list(request):
    """
    1-on-1 Direct Chat & Materials section with assigned trainer:
    - View all messages, PDFs, learning materials, and links exchanged with mentor.
    - Two-way messaging: Student can write replies directly to their assigned mentor.
    - Strictly 1-on-1 between the student and trainer.
    """
    student = request.user.student_profile
    trainer = student.trainer

    if not trainer:
        messages.warning(request, "No trainer has been assigned to your profile yet. Please reach out to institute support.")
        return render(request, 'student/messages.html', {
            'student': student,
            'trainer': None,
            'messages_list': [],
            'reply_form': None,
        })

    # Fetch 1-on-1 thread between student and trainer
    thread_qs = StudentDirectMessage.objects.filter(
        student=student,
        trainer=trainer
    ).order_by('created_at')

    # Mark all unread incoming messages from trainer as read
    incoming_unread = thread_qs.filter(sender_role='TRAINER', is_read=False)
    if incoming_unread.exists():
        incoming_unread.update(is_read=True)

    # Process student's reply
    if request.method == 'POST':
        reply_form = StudentReplyMessageForm(request.POST, request.FILES)
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.student = student
            reply.trainer = trainer
            reply.sender_role = 'STUDENT'
            reply.subject = f"Reply from {student.name}"
            reply.save()

            if trainer and trainer.user:
                send_notification(
                    recipient=trainer.user,
                    title=f"Direct Reply from {student.name}",
                    message=f"{student.name}: {reply.message[:80]}",
                    link_url=f"/trainer/messages/student/{student.id}/",
                    notification_type='MESSAGE'
                )

            messages.success(request, f"Your reply was sent directly to {trainer.full_name}!")
            return redirect('student:messages')
    else:
        reply_form = StudentReplyMessageForm()

    return render(request, 'student/messages.html', {
        'student': student,
        'trainer': trainer,
        'messages_list': thread_qs,
        'reply_form': reply_form,
    })


@student_required
def resources_list(request):
    """
    Learning Resources tab:
    Common tab where students access learning resources, but FILTERED STRICTLY
    according to their enrolled course!
    """
    student = request.user.student_profile
    course = student.course

    query = request.GET.get('q', '').strip()
    res_type = request.GET.get('type', '').strip()

    if not course:
        resources = CourseResource.objects.none()
    else:
        # Strictly matching the student's course
        resources = CourseResource.objects.filter(course=course).select_related('trainer', 'department')

        if query:
            resources = resources.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(notes_content__icontains=query)
            )

        if res_type:
            resources = resources.filter(resource_type=res_type)

    return render(request, 'student/resources.html', {
        'student': student,
        'course': course,
        'resources': resources,
        'query': query,
        'selected_type': res_type,
    })


@student_required
def leave_apply(request):
    """
    Student applies for leave (dates, reason, leave type).
    Notifies assigned trainer.
    Displays past leave applications and their review status (Pending / Approved / Rejected).
    """
    student = request.user.student_profile
    trainer = student.trainer

    if request.method == 'POST':
        form = StudentLeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = student
            leave.status = 'Pending'
            leave.save()

            # Send activity notification to assigned trainer
            if trainer and trainer.user:
                send_notification(
                    recipient=trainer.user,
                    title=f"Leave Request from {student.name}",
                    message=f"{student.name} ({student.student_id}) requested leave from {leave.from_date} to {leave.to_date}. Reason: {leave.reason[:70]}",
                    link_url="/trainer/student-leaves/",
                    notification_type='LEAVE_REQUEST'
                )

            messages.success(
                request,
                f"Your leave request for {leave.total_days} day(s) has been submitted to "
                f"{trainer.full_name if trainer else 'your trainer'} for review."
            )
            return redirect('student:leave_apply')
    else:
        form = StudentLeaveRequestForm(initial={'from_date': date.today()})

    leave_history = student.student_leave_requests.all()
    stats = student.get_attendance_stats()

    return render(request, 'student/leave_apply.html', {
        'student': student,
        'trainer': trainer,
        'form': form,
        'leave_history': leave_history,
        'stats': stats,
    })
