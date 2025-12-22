
from django.db import models
from django.utils import timezone

from training.models import UserQualification, UserQualificationCriterion


class QualificationManager(models.Manager):

    def get_by_category(self, category):
        """Return all qualifications in a given category."""
        return self.filter(category=category)

    def with_criteria(self):
        """Prefetch criteria for all qualifications."""
        return self.prefetch_related("criteria")

    def award_to_user(self, user, qualification, event=None, awarded_by=None):
        """
        Award a qualification to a user and automatically mark all criteria completed.
        """
        uq, created = UserQualification.objects.get_or_create(
            user=user,
            qualification=qualification,
            defaults={
                "event": event,
                "date_awarded": timezone.now().date(),
                "awarded_by": awarded_by,
            }
        )

        # Create UserQualificationCriterion entries if not already present
        existing_criteria_ids = set(uq.criteria_status.values_list('criterion_id', flat=True))
        for criterion in qualification.criteria.exclude(id__in=existing_criteria_ids):
            UserQualificationCriterion.objects.create(user_qualification=uq, criterion=criterion)

        return uq


class UserQualificationManager(models.Manager):

    def for_user(self, user):
        """Return all qualifications earned by a user."""
        return self.filter(user=user).select_related("qualification")

    def missing_criteria(self, user):
        """Return a list of criteria not yet awarded for this user's qualifications."""
        missing = []
        for uq in self.filter(user=user):
            completed_ids = set(uq.criteria_status.values_list("criterion_id", flat=True))
            all_ids = set(uq.qualification.criteria.values_list("id", flat=True))
            missing.extend(uq.qualification.criteria.filter(id__in=all_ids - completed_ids))
        return missing

    def award_bulk(self, users, qualification, event=None, awarded_by=None):
        """Award the same qualification to multiple users at once."""
        results = []
        for user in users:
            uq = self.model.objects.award_to_user(user, qualification, event=event, awarded_by=awarded_by)
            results.append(uq)
        return results


class QualificationEventManager(models.Manager):

    def get_events_for_qualification(self, qualification):
        """Return all events where a qualification can be awarded."""
        return self.filter(qualification=qualification)

    def get_users_awarded(self, qualification):
        """Return all users who earned this qualification via events."""
        return UserQualification.objects.filter(
            qualification=qualification,
            event__in=self.filter(qualification=qualification)
        )
