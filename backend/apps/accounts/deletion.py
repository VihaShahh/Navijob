from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.models import ReviewDecision
from apps.core.moderation import IsOperator, ReviewConflict
from .models import ApplicantProfile, DeletionRequest
from .permissions import IsVerifiedAccount
from .privacy import private_response


class DeletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeletionRequest
        fields = ["id", "status", "reason", "response", "created_at", "updated_at"]
        read_only_fields = fields


class RequestInput(serializers.Serializer):
    confirmation = serializers.ChoiceField(choices=["REQUEST DELETION"])
    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class DeletionView(APIView):
    permission_classes = [IsVerifiedAccount]

    def get(self, request):
        return private_response(Response(DeletionSerializer(DeletionRequest.objects.filter(user=request.user)[:50], many=True).data))

    @transaction.atomic
    def post(self, request):
        values = RequestInput(data=request.data)
        values.is_valid(raise_exception=True)
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        existing = DeletionRequest.objects.filter(user=request.user, status="pending").first()
        if existing:
            return private_response(Response(DeletionSerializer(existing).data))
        item = DeletionRequest.objects.create(user=request.user, reason=values.validated_data.get("reason", ""))
        return private_response(Response(DeletionSerializer(item).data, status=201))


class CancelDeletionView(APIView):
    permission_classes = [IsVerifiedAccount]

    @transaction.atomic
    def post(self, request, request_id):
        item = get_object_or_404(DeletionRequest.objects.select_for_update(), pk=request_id, user=request.user)
        if item.status != "pending":
            raise ReviewConflict("This request is no longer pending.")
        item.status = "cancelled"
        item.save(update_fields=["status", "updated_at"])
        return private_response(Response(DeletionSerializer(item).data))


class OperatorDeletionView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        items = DeletionRequest.objects.filter(status="pending").select_related("user").order_by("created_at")[:100]
        return private_response(Response([{**DeletionSerializer(item).data, "email": item.user.email} for item in items]))


class DecisionInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=["disable_access", "decline"])
    reason = serializers.CharField(max_length=2000)


class OperatorDeletionDecisionView(APIView):
    permission_classes = [IsOperator]

    @transaction.atomic
    def post(self, request, request_id):
        values = DecisionInput(data=request.data)
        values.is_valid(raise_exception=True)
        item = get_object_or_404(DeletionRequest.objects.select_for_update(), pk=request_id)
        if item.user_id == request.user.pk:
            raise ValidationError("Another operator must review your own deletion request.")
        if item.status != "pending":
            raise ReviewConflict("This deletion request has already been handled.")
        user = get_user_model().objects.select_for_update().get(pk=item.user_id)
        before = {"status": item.status, "is_active": user.is_active}
        if values.validated_data["action"] == "disable_access":
            user.is_active = False
            user.save(update_fields=["is_active"])
            ApplicantProfile.objects.filter(user=user).update(public_visibility=False, is_open_to_work=False)
            item.status = "access_disabled"
        else:
            item.status = "declined"
        item.response = values.validated_data["reason"]
        item.save(update_fields=["status", "response", "updated_at"])
        ReviewDecision.objects.create(kind="deletion", target_id=item.pk, actor=request.user, decision=values.validated_data["action"], reason=item.response, method="Account deletion request review; physical erasure not performed", before=before, after={"status": item.status, "is_active": user.is_active})
        return private_response(Response(DeletionSerializer(item).data))
