from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import RecruiterProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from .models import ReviewDecision


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.is_active and user.is_staff and user.has_perm("core.moderate_marketplace")


class ReviewConflict(APIException):
    status_code = 409
    default_detail = "This item changed. Reload the queue and review it again."


class DecisionInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approve", "reject"])
    reason = serializers.CharField(max_length=2000)
    method = serializers.CharField(max_length=240)
    expected_updated_at = serializers.DateTimeField()


def state_of(item, kind):
    fields = {"company": ["review_status", "is_verified", "review_feedback"], "recruiter": ["is_verified"], "job": ["review_status", "status", "is_verified", "review_feedback"]}[kind]
    return {field: getattr(item, field) for field in fields}


@transaction.atomic
def decide(user, kind, target_id, values):
    model = {"company": Company, "recruiter": RecruiterProfile, "job": Job}.get(kind)
    if not model:
        raise ValidationError("Unknown review queue.")
    item = get_object_or_404(model.objects.select_for_update(), pk=target_id)
    if item.updated_at != values["expected_updated_at"]:
        raise ReviewConflict()
    approved = values["decision"] == "approve"
    before = state_of(item, kind)
    if kind == "recruiter" and approved:
        company = Company.objects.select_for_update().get(pk=item.company_id)
        if not item.authority_declaration_at or not company.is_verified or company.review_status != "approved":
            raise ValidationError("Review the company and recruiter authority declaration first.")
    if kind == "job":
        company = Company.objects.select_for_update().get(pk=item.company_id)
        recruiter = RecruiterProfile.objects.select_for_update().filter(pk=item.posted_by_id, company=company).first()
        if not item.review_requested_at or item.status != "draft":
            raise ValidationError("Only a submitted draft can receive a publication decision.")
        if approved and (not company.is_verified or company.review_status != "approved" or not recruiter or not recruiter.is_verified or not recruiter.can_manage_company):
            raise ValidationError("Review company identity and recruiter authority before publication.")
        item.status = "published" if approved else "draft"
        if approved:
            if item.application_deadline and item.application_deadline < timezone.localdate():
                raise ValidationError("The application deadline has passed.")
            if item.expires_at and item.expires_at <= timezone.now():
                raise ValidationError("The listing has expired.")
            item.published_at = timezone.now()
            item.is_active = True
    if kind != "recruiter":
        item.review_status = "approved" if approved else "rejected"
        item.review_feedback = values["reason"]
    item.is_verified = approved
    item.save()
    return ReviewDecision.objects.create(kind=kind, target_id=item.pk, actor=user, decision=values["decision"], reason=values["reason"], method=values["method"], before=before, after=state_of(item, kind))


def audit_payload(record):
    return {"id": record.pk, "kind": record.kind, "target_id": record.target_id, "decision": record.decision, "reason": record.reason, "method": record.method, "before": record.before, "after": record.after, "actor": record.actor.get_full_name() or record.actor.get_username() if record.actor else "Former operator", "created_at": record.created_at}


class ReviewQueueView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        companies = Company.objects.filter(review_status="pending").order_by("created_at")[:100]
        recruiters = RecruiterProfile.objects.filter(is_verified=False, authority_declaration_at__isnull=False).select_related("company", "user").order_by("created_at")[:100]
        jobs = Job.objects.filter(review_status="pending", status="draft", review_requested_at__isnull=False).select_related("company").order_by("review_requested_at")[:100]
        return Response({"companies": [{"id": c.pk, "name": c.name, "website": c.website, "description": c.description, "updated_at": c.updated_at} for c in companies], "recruiters": [{"id": r.pk, "name": r.user.get_full_name() or r.user.email, "company": r.company.name, "title": r.title, "declaration_at": r.authority_declaration_at, "updated_at": r.updated_at} for r in recruiters], "jobs": [{"id": j.pk, "name": j.title, "company": j.company.name, "description": j.description, "application_mode": j.application_mode, "apply_url": j.apply_url, "salary_min": j.salary_min, "salary_max": j.salary_max, "currency": j.currency, "updated_at": j.updated_at} for j in jobs], "audit": [audit_payload(item) for item in ReviewDecision.objects.select_related("actor")[:50]], "limit": 100})


class ReviewDecisionView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, kind, target_id):
        serializer = DecisionInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = decide(request.user, kind, target_id, serializer.validated_data)
        response = Response(audit_payload(record), status=201)
        response["Cache-Control"] = "private, no-store"
        return response
