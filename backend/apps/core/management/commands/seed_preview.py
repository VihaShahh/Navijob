"""Create fictional, opt-in local data without touching remote services."""
import hashlib
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import AccountState, ApplicantProfile, Experience, Project, RecruiterProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.resumes.models import Resume


def sample_pdf():
    text = b"BT /F1 16 Tf 60 760 Td (Fictional NaviJob candidate - local preview only) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"\nendstream"]
    result = b"%PDF-1.4\n"
    offsets = [0]
    for index, value in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{index} 0 obj\n".encode() + value + b"\nendobj\n"
    xref = len(result)
    result += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        result += f"{offset:010} 00000 n \n".encode()
    return result + f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


class Command(BaseCommand):
    help = "Seed explicitly fictional accounts and roles in the isolated local preview database."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="NaviJob-Preview-42!")

    @transaction.atomic
    def handle(self, *args, **options):
        if not getattr(settings, "NAVIJOB_ALLOW_SAMPLE_SEED", False) or settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Sample seeding requires isolated SQLite preview settings. Use --settings=config.settings.preview.")
        users = {}
        for role, name in [("candidate", "Sample Candidate"), ("recruiter", "Sample Hiring Team"), ("operator", "Sample Operator")]:
            email = f"{role}@sample.navijob.test"
            user, created = get_user_model().objects.get_or_create(username=email, defaults={"email": email, "first_name": name, "is_staff": role == "operator"})
            if created:
                user.set_password(options["password"])
                user.save(update_fields=["password"])
            AccountState.objects.get_or_create(user=user, defaults={"role": "recruiter" if role == "recruiter" else "candidate", "email_verified": True, "verified_email": email})
            users[role] = user
        users["operator"].user_permissions.add(Permission.objects.get(codename="moderate_marketplace"))
        profile, _ = ApplicantProfile.objects.get_or_create(user=users["candidate"], defaults={"headline": "Engineer building fictional preview products", "location": "Bengaluru", "skills": ["Python", "Django", "React"], "summary": "Synthetic career profile for local product review. No real person or employment is represented."})
        ApplicantProfile.objects.get_or_create(user=users["operator"])
        Experience.objects.get_or_create(profile=profile, company="Fictional Studio", title="Sample engineer", defaults={"start_date": "2022-01-01", "is_current": True, "description": "Fictional experience for preview."})
        Project.objects.get_or_create(profile=profile, title="Fictional garden planner", defaults={"description": "Synthetic project for testing application review.", "contribution": "Built the sample interface.", "stack": ["React"], "stage": "prototype"})
        company, _ = Company.objects.get_or_create(slug="sample-sprout-studio", defaults={"name": "Sprout Studio · Sample", "website": "https://example.com", "description": "Fictional company used for local preview, not an employer partnership.", "industry": "Sample software", "location": "Bengaluru", "company_size": "11_50", "is_sample": True, "is_verified": True, "review_status": "approved"})
        recruiter, _ = RecruiterProfile.objects.get_or_create(user=users["recruiter"], defaults={"company": company, "title": "Fictional hiring manager", "is_verified": True, "can_manage_company": True, "authority_declaration_at": timezone.now()})
        for suffix, mode, status, review in [("engineer", "native", "published", "approved"), ("designer", "external", "published", "approved"), ("closed", "native", "closed", "approved"), ("pending", "native", "draft", "pending")]:
            Job.objects.get_or_create(slug=f"sample-sprout-{suffix}", defaults={"company": company, "posted_by": recruiter, "title": f"Sample {suffix.title()} · Fictional role", "description": "This fictional role exercises the local NaviJob workflow. It is not a real vacancy or a hiring commitment.", "location": "Bengaluru", "work_mode": "hybrid", "skills": ["Python", "React"], "currency": "INR", "salary_min": 1800000, "salary_max": 3000000, "application_mode": mode, "apply_url": "https://example.com" if mode == "external" else "", "status": status, "review_status": review, "is_sample": True, "published_at": timezone.now() if status == "published" else None, "review_requested_at": timezone.now() if review == "pending" else None, "source": "Fictional local preview"})
        if not Resume.objects.filter(user=users["candidate"]).exists():
            content = sample_pdf()
            Resume.objects.create(user=users["candidate"], title="Sample resume · Fictional", pdf_file=ContentFile(content, name="sample-resume.pdf"), original_filename="sample-resume.pdf", file_size=len(content), content_sha256=hashlib.sha256(content).hexdigest(), is_primary=True)
        self.stdout.write(self.style.SUCCESS("Fictional preview data ready. Existing profiles, credentials and workflow states were preserved."))
        self.stdout.write("Accounts: candidate@sample.navijob.test, recruiter@sample.navijob.test, operator@sample.navijob.test")
