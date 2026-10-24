from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


def send_notification(recipient, title, message, link_url='', notification_type='SYSTEM'):
    """
    Creates an activity notification for a recipient user (or list/queryset of users).
    
    Args:
        recipient: A User instance, or an iterable (list/queryset) of User instances.
        title: Short bold headline e.g. "Leave Request Approved"
        message: Description text e.g. "Your leave has been approved by your mentor."
        link_url: Target URL to open on click (web or mobile notification tap)
        notification_type: 'LEAVE_REQUEST' | 'LEAVE_REVIEW' | 'MESSAGE' | 'RESOURCE' | 'NOTICE' | 'STUDENT_ENROLLED' | 'COURSE_ASSIGNED' | 'SYSTEM'
    """
    if not recipient:
        return None

    # Handle iterable of recipients (batch sending)
    if hasattr(recipient, '__iter__') and not isinstance(recipient, User):
        created_list = []
        for u in recipient:
            if isinstance(u, User):
                notif = Notification.objects.create(
                    recipient=u,
                    title=title,
                    message=message,
                    link_url=link_url,
                    notification_type=notification_type,
                    is_read=False
                )
                created_list.append(notif)
        return created_list

    # Single recipient
    if isinstance(recipient, User):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            link_url=link_url,
            notification_type=notification_type,
            is_read=False
        )
    return None
