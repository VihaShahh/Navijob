from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsVerifiedAccount
from apps.accounts.privacy import private_response
from .models import ApplicationUpdate


def payload(item):
    return {"id": item.pk, "title": item.title, "body": item.body, "href": item.href, "created_at": item.created_at, "read_at": item.read_at}


class UpdatesView(APIView):
    permission_classes = [IsVerifiedAccount]

    def get(self, request):
        items = ApplicationUpdate.objects.filter(user=request.user)
        return private_response(Response({"unread_count": items.filter(read_at__isnull=True).count(), "results": [payload(item) for item in items[:100]]}))


class ReadUpdateView(APIView):
    permission_classes = [IsVerifiedAccount]

    def post(self, request, update_id):
        item = get_object_or_404(ApplicationUpdate, pk=update_id, user=request.user)
        if item.read_at is None:
            ApplicationUpdate.objects.filter(pk=item.pk, read_at__isnull=True).update(read_at=timezone.now())
            item.refresh_from_db()
        return private_response(Response(payload(item)))
