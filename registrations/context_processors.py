def notifications(request):
    count = request.user.notifications.filter(read_at__isnull=True).count() if request.user.is_authenticated else 0
    return {"unread_notifications": count}
