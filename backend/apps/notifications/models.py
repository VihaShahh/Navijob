from django.conf import settings
from django.db import models


class ApplicationUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="application_updates")
    event = models.ForeignKey("jobs.ApplicationEvent", on_delete=models.CASCADE, related_name="updates")
    title = models.CharField(max_length=260)
    body = models.CharField(max_length=400)
    href = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["user", "event"], name="unique_update_per_user_event")]
        indexes = [models.Index(fields=["user", "read_at"])]
