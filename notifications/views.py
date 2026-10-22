
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import User
from .models import Notification


@login_required
def notification_list(request):
    if request.user.role != User.Role.CANDIDATE:
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(
            request,
            "Only candidates can view notifications.",
        )
        return redirect("home")

    notifications = Notification.objects.filter(
        recipient=request.user,
    ).select_related("application", "application__job")

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )



from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST


@login_required
@require_POST
def mark_notification_read(request, pk):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can update notifications.")
        return redirect("home")

    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return redirect("notification_list")
