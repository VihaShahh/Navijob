from django.contrib import admin
from .models import ReviewDecision


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("kind", "target_id", "decision", "actor", "created_at")
    list_filter = ("kind", "decision")
    readonly_fields = ("kind", "target_id", "actor", "decision", "reason", "method", "before", "after", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
