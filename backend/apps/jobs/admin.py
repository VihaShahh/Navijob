from django.contrib import admin

from apps.jobs.models import Job, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "status", "seniority", "work_mode", "job_type", "is_premium", "published_at")
    list_filter = ("status", "seniority", "work_mode", "job_type", "is_premium", "is_verified")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "company__name", "location", "skills")
    readonly_fields = ("created_at", "updated_at", "status", "is_verified", "review_status", "review_feedback", "review_requested_at")
    date_hierarchy = "published_at"

    def save_model(self, request, obj, form, change):
        if change:
            obj.status = "draft"
            obj.review_status = "pending"
            obj.review_requested_at = None
            obj.review_feedback = ""
            obj.is_verified = False
        super().save_model(request, obj, form, change)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "source", "submitted_at", "updated_at")
    list_filter = ("status", "source", "submitted_at")
    search_fields = ("job__title", "applicant__user__email", "applicant__user__first_name", "applicant__user__last_name")
    readonly_fields = tuple(field.name for field in JobApplication._meta.fields)
    date_hierarchy = "submitted_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
