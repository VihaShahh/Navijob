from django.contrib import admin
from django.urls import include, path
from apps.core.views import csrf_token, health
from apps.core.moderation import ReviewDecisionView, ReviewQueueView
from apps.core.reports import ReportView, OperatorReportView, OperatorReportDecisionView
from apps.accounts.deletion import DeletionView, CancelDeletionView, OperatorDeletionView, OperatorDeletionDecisionView

urlpatterns = [
    path("api/me/deletion/", DeletionView.as_view()),
    path("api/me/deletion/<int:request_id>/cancel/", CancelDeletionView.as_view()),
    path("api/operator/deletion/", OperatorDeletionView.as_view()),
    path("api/operator/deletion/<int:request_id>/", OperatorDeletionDecisionView.as_view()),
    path("api/reports/", ReportView.as_view()),
    path("api/operator/reports/", OperatorReportView.as_view()),
    path("api/operator/reports/<int:report_id>/", OperatorReportDecisionView.as_view()),
    path("api/operator/reviews/", ReviewQueueView.as_view()),
    path("api/operator/reviews/<str:kind>/<int:target_id>/", ReviewDecisionView.as_view()),
    path("api/health/", health),
    path("api/auth/csrf/", csrf_token),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/me/", include("apps.accounts.career_urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/companies/", include("apps.companies.urls")),
    path("api/recruiter/", include("apps.companies.recruiter_urls")),
    path("api/recruiter/", include("apps.jobs.recruiter_urls")),
    path("admin/", admin.site.urls),
    path("api/", include("apps.jobs.urls")),
    path("api/waitlist/", include("apps.waitlist.urls")),
]
