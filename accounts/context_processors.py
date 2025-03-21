from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        unread_notifications_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        return {
            'recent_notifications': recent_notifications,
            'unread_notifications_count': unread_notifications_count
        }
    return {} 