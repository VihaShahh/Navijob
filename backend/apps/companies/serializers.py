from rest_framework import serializers

from apps.companies.models import Company


class CompanySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "slug",
            "logo_url",
            "industry",
            "stage",
            "company_size",
            "location",
            "is_verified",
            "is_sample",
            "is_premium_partner",
        )


class CompanyDetailSerializer(CompanySummarySerializer):
    identity_review = serializers.SerializerMethodField()

    def get_identity_review(self, company):
        from apps.core.models import ReviewDecision
        record = ReviewDecision.objects.filter(kind="company", target_id=company.pk).first()
        if not company.is_verified or not record or record.decision != "approve":
            return None
        return {"scope": "Company identity", "method": record.method, "checked_at": record.created_at}

    class Meta(CompanySummarySerializer.Meta):
        fields = CompanySummarySerializer.Meta.fields + (
            "identity_review",
            "website",
            "description",
            "funding_summary",
            "headquarters",
            "careers_url",
            "created_at",
            "updated_at",
        )
