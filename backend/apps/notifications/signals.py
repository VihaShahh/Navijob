from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import RecruiterProfile
from apps.jobs.models import ApplicationEvent
from .models import ApplicationUpdate


@receiver(post_save, sender=ApplicationEvent)
def application_updates(sender, instance, created, **kwargs):
    if not created:
        return
    application = instance.application
    title = f"{application.job.title[:210]} · {instance.get_status_display()}"
    ApplicationUpdate.objects.get_or_create(user_id=application.applicant.user_id, event=instance, defaults={"title": title, "body": instance.note, "href": f"/candidate/applications/{application.pk}"})
    recipients = RecruiterProfile.objects.filter(company_id=application.job.company_id, is_verified=True, user__is_active=True, user__account_state__email_verified=True, company__is_verified=True, company__review_status="approved").exclude(user_id=instance.actor_id)
    for recruiter in recipients:
        ApplicationUpdate.objects.get_or_create(user_id=recruiter.user_id, event=instance, defaults={"title": title, "body": instance.note, "href": f"/recruiter/applicants/{application.pk}"})
