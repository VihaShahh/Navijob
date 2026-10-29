from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReviewDecision(models.Model):
    kind = models.CharField(max_length=20)
    target_id = models.PositiveBigIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    decision = models.CharField(max_length=20)
    reason = models.TextField(max_length=2000)
    method = models.CharField(max_length=240)
    before = models.JSONField()
    after = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["kind", "target_id"])]
        permissions = [("moderate_marketplace", "Review company identity, recruiter authority and jobs")]


class ListingReport(TimeStampedModel):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listing_reports")
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="reports")
    category = models.CharField(max_length=24, choices=[("misleading", "Misleading details"), ("closed", "Role no longer open"), ("unsafe", "Unsafe or abusive"), ("other", "Other concern")])
    details = models.TextField(max_length=3000)
    status = models.CharField(max_length=20, default="pending", choices=[("pending", "Pending"), ("resolved", "Resolved"), ("dismissed", "Dismissed")])
    response = models.TextField(max_length=2000, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["reporter", "job"], name="one_report_per_reporter_job")]
