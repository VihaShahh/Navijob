import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.models import ListingReport
from apps.core.reports import ReportSerializer
from apps.jobs.application_serializers import ApplicationSerializer
from apps.jobs.models import JobApplication, SavedJob
from apps.resumes.models import Resume
from apps.resumes.serializers import ResumeMetadataSerializer
from .career_serializers import CareerProfileSerializer, ProjectSerializer
from .models import ApplicantProfile, DeletionRequest
from .permissions import IsVerifiedAccount


def private_response(response):
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


class PrivacyInput(serializers.Serializer):
    is_open_to_work = serializers.BooleanField()


class PrivacyView(APIView):
    permission_classes = [IsVerifiedAccount]

    def get(self, request):
        profile = ApplicantProfile.objects.filter(user=request.user).first()
        return private_response(Response({"is_open_to_work": profile.is_open_to_work if profile else None, "public_visibility": False, "sharing": "Profiles are private. Only applications you choose to submit share a frozen copy with that hiring team."}))

    def patch(self, request):
        serializer = PrivacyInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        ApplicantProfile.objects.filter(user=request.user).update(is_open_to_work=serializer.validated_data["is_open_to_work"], public_visibility=False, updated_at=timezone.now())
        return self.get(request)


class ExportView(APIView):
    permission_classes = [IsVerifiedAccount]

    def get(self, request):
        user = request.user
        from apps.notifications.models import ApplicationUpdate
        profile = ApplicantProfile.objects.filter(user=user).select_related("user").prefetch_related("experiences", "education", "projects").first()
        applications = JobApplication.objects.filter(applicant__user=user).select_related("job", "job__company").prefetch_related("events")
        resumes = []
        for resume in Resume.objects.filter(user=user):
            entry = dict(ResumeMetadataSerializer(resume).data)
            entry["download_url"] = f"/api/resumes/{resume.pk}/download/" if resume.pdf_file else None
            resumes.append(entry)
        payload = {
            "schema_version": 1, "exported_at": timezone.now(),
            "account": {"name": user.get_full_name(), "email": user.email, "role": user.account_state.role, "joined_at": user.date_joined},
            "profile": CareerProfileSerializer(profile).data if profile else None,
            "projects": ProjectSerializer(profile.projects.all(), many=True).data if profile else [],
            "resumes": resumes,
            "applications": ApplicationSerializer(applications, many=True).data,
            "saved_jobs": list(SavedJob.objects.filter(applicant__user=user).values("job_id", "created_at")),
            "reports": ReportSerializer(ListingReport.objects.filter(reporter=user).select_related("job"), many=True).data,
            "deletion_requests": list(DeletionRequest.objects.filter(user=user).values("id", "status", "reason", "response", "created_at")),
            "updates": list(ApplicationUpdate.objects.filter(user=user).values("title", "body", "href", "created_at", "read_at")),
            "file_handling": "PDFs are available through the authenticated download links in this export. Submitted application copies are separate from editable resume versions. Employer-private notes are excluded.",
        }
        response = HttpResponse(json.dumps(payload, cls=DjangoJSONEncoder, indent=2), content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="navijob-account-data.json"'
        return private_response(response)
