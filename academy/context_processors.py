def notifications_processor(request):
    """
    Supplies unread notification count and recent notifications list
    to the global navbar and layout context for authenticated users.
    Also provides pending_student_leaves_count for trainers.
    """
    if request.user.is_authenticated:
        from academy.models import Notification
        from attendance.models import StudentLeaveRequest
        user_notifications = Notification.objects.filter(recipient=request.user)
        unread_count = user_notifications.filter(is_read=False).count()
        recent_notifs = user_notifications[:8]

        pending_student_leaves = 0
        if getattr(request.user, 'is_trainer', False) and hasattr(request.user, 'trainer_profile'):
            pending_student_leaves = StudentLeaveRequest.objects.filter(
                student__trainer=request.user.trainer_profile,
                status='Pending'
            ).count()

        return {
            'navbar_unread_notifications_count': unread_count,
            'navbar_recent_notifications': recent_notifs,
            'pending_student_leaves_count': pending_student_leaves,
        }
    return {
        'navbar_unread_notifications_count': 0,
        'navbar_recent_notifications': [],
        'pending_student_leaves_count': 0,
    }
