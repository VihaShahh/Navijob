from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .career_views import CareerProfileView, EducationViewSet, ExperienceViewSet, ProjectViewSet
from .privacy import ExportView, PrivacyView

router = DefaultRouter()
router.register("experience", ExperienceViewSet, basename="career-experience")
router.register("education", EducationViewSet, basename="career-education")
router.register("projects", ProjectViewSet, basename="career-project")
urlpatterns = [path("privacy/", PrivacyView.as_view()), path("export/", ExportView.as_view()), path("profile/", CareerProfileView.as_view()), path("", include(router.urls))]
