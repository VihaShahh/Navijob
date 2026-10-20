from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from apps.jobs.models import Job
from apps.resumes.models import Resume


class PreviewSeedTests(TestCase):
    def test_default_settings_refuse_seeding(self):
        with self.assertRaises(CommandError):
            call_command("seed_preview", stdout=StringIO())

    @override_settings(NAVIJOB_ALLOW_SAMPLE_SEED=True)
    def test_preview_seed_is_idempotent_and_clearly_fictional(self):
        call_command("seed_preview", stdout=StringIO())
        call_command("seed_preview", stdout=StringIO())
        self.assertEqual(Job.objects.count(), 4)
        self.assertFalse(Job.objects.filter(is_sample=False).exists())
        self.assertEqual(Resume.objects.count(), 1)
        job = Job.objects.get(slug="sample-sprout-engineer")
        job.status = "closed"
        job.save()
        call_command("seed_preview", stdout=StringIO())
        job.refresh_from_db()
        self.assertEqual(job.status, "closed")
