from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsCandidate
from apps.jobs.models import Job
from .models import ListingReport, ReviewDecision
from .moderation import IsOperator, ReviewConflict


class ReportSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = ListingReport
        fields = ["id", "job", "title", "category", "details", "status", "response", "created_at"]
        read_only_fields = ["id", "status", "response", "created_at"]

    def validate_job(self, job):
        if job.review_status != "approved" or job.status not in {"published", "closed"}:
            raise serializers.ValidationError("Choose a publicly available listing.")
        return job


class ReportView(APIView):
    permission_classes = [IsCandidate]

    def get(self, request):
        return Response(ReportSerializer(ListingReport.objects.filter(reporter=request.user).select_related("job")[:100], many=True).data)

    @transaction.atomic
    def post(self, request):
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        existing = ListingReport.objects.filter(reporter=request.user, job=serializer.validated_data["job"]).first()
        if existing:
            return Response(ReportSerializer(existing).data)
        if ListingReport.objects.filter(reporter=request.user, created_at__date=timezone.localdate()).count() >= 20:
            raise ValidationError("You have reached today's report limit.")
        report = serializer.save(reporter=request.user)
        return Response(ReportSerializer(report).data, status=201)


class ReportDecisionInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=["resolve", "dismiss", "close"])
    reason = serializers.CharField(max_length=2000)


class OperatorReportView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(ReportSerializer(ListingReport.objects.filter(status="pending").select_related("job").order_by("created_at")[:100], many=True).data)


class OperatorReportDecisionView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, report_id):
        serializer = ReportDecisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = get_object_or_404(ListingReport.objects.select_for_update(), pk=report_id)
        if report.status != "pending":
            raise ReviewConflict("This report has already been handled. Reload the queue.")
        job = Job.objects.select_for_update().get(pk=report.job_id)
        before = {"status": report.status, "job_status": job.status}
        if serializer.validated_data["action"] == "close":
            job.status = "closed"
            job.save(update_fields=["status", "updated_at"])
        report.status = "dismissed" if serializer.validated_data["action"] == "dismiss" else "resolved"
        report.response = serializer.validated_data["reason"]
        report.save(update_fields=["status", "response", "updated_at"])
        ReviewDecision.objects.create(kind="report", target_id=report.pk, actor=request.user, decision=serializer.validated_data["action"], reason=report.response, method="Listing report review", before=before, after={"status": report.status, "job_status": job.status})
        return Response(ReportSerializer(report).data)
