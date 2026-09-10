from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from events.models import Event

# Create your models here.

class ClubRatingAudit(models.Model):
    club = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, editable=False)
    rating = models.IntegerField("Avaliação", default=0, editable=False)

    def __str__(self):
        return '{} {} rating'.format(self.club, self.event)
    

class ClubSubscription(models.Model):
    club = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        limit_choices_to={"role__in": ["free_club", "subed_club"]}
    )

    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=7, decimal_places=2) 
    due_date = models.DateTimeField()
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("club", "year")
        ordering = ["-year"]

    def mark_as_paid(self):
        self.paid = True
        self.paid_at = timezone.now()
        self.save()

    def __str__(self):
        return f'{self.club.username} {self.year} payment'
    

class ClubSubscriptionConfig(models.Model):
    """
    Stores subscription amount for each Admin.
    Each Admin should have exactly one config row.
    The amount will be used to create ClubSubscriptions for all the children acounts
    """
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_config",
        limit_choices_to={"role": "main_admin"},  
    )
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)

    def __str__(self):
        return f"{self.admin.username} – subscription amount: {self.amount}"

    @staticmethod
    def get_amount_for(admin):
        """
        Returns the admin's amount, creating a config row if missing.
        """
        obj, _ = ClubSubscriptionConfig.objects.get_or_create(admin=admin)
        return obj.amount
    

class ClubSettings(models.Model):
    club = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="club_settings"
    )
    billing_day = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)]
    )

    def __str__(self):
        return f"{self.club} billing day: {self.billing_day}"