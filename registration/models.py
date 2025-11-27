from django.db import models
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from nanoid import generate
from datetime import date
from core.constants import GENDERS, GRADUATIONS, MATCHES
from events.models import Event

# Create your models here.

def generate_unique_nanoid(model_name, app_label, size=10):
    """
    Generates a unique NanoID for a given model.
    Uses `apps.get_model()` to avoid import issues.
    """
    model = apps.get_model(app_label, model_name)  # Dynamically get model
    while True:
        new_id = generate(size=size)  # Generate NanoID
        if not model.objects.filter(id=new_id).exists():
            return new_id


### Member model ###

class Member(models.Model):

    class MEMBER_TYPE(models.TextChoices):
        STUDENT = "student", "Student"
        ATHLETE = "athlete", "Athlete"
        COACH = "coach", "Coach"

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    member_type = models.CharField(max_length=16, choices=MEMBER_TYPE.choices, default=MEMBER_TYPE.ATHLETE)
    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    address = models.CharField("Morada", max_length=200, blank=True, null=True)
    post_code = models.PositiveIntegerField("Código Postal", blank=True, null=True)
    id_number = models.PositiveIntegerField("Nº SKI-P", blank=True, null=True)
    favorite = models.BooleanField("Favorito", default=False)
    registration_date = models.DateField("Data de Inscrição", default=date.today)
    national_card_number = models.PositiveIntegerField("Nº CC/BI", blank=True, null=True)
    taxpayer_number = models.PositiveIntegerField("NIF", blank=True, null=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    # main admin in multiple acount schemas won't be filling the weight
    weight = models.PositiveIntegerField("Peso", blank=True, null=True)
    quotes_legible = models.BooleanField("Paga Quotas", default=True)
    club = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_members",
        null=True
    )
    conditions = models.TextField("Condições Médicas", blank=True, null=True)
    observations = models.TextField("Observações", blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["first_name", "last_name", "birth_date", "member_type", "id_number"],
                name="unique_member_identity"
            )
        ]
    
    def current_month_payment(self):
        """Returns True if the member paid this month's quota."""
        today = date.today()
        return self.payments.filter(
            year=today.year,
            month=today.month,
            paid=True,
        ).exists()

    def clean(self):
        if self.member_type == "coach" and self.favorite == True:
            raise ValidationError("Coaches are not qualified as favorite.")
        
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid(self.__class__.__name__, self._meta.app_label)
        
        if not self.registration_date:
            self.registration_date = date.today()

        super().save(*args, **kwargs)

    def __str__(self): 
        return "{} {} | {}".format(self.first_name, self.last_name, self.club.username)


class MonthlyMemberPayment(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()  # 1=Jan ... 12=Dec

    amount = models.DecimalField(max_digits=7, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("member", "year", "month")
        ordering = ["-year", "-month"]

    def mark_as_paid(self):
        self.paid = True
        self.paid_at = timezone.now()
        self.save()


### Teams models ###

class Team(models.Model):

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    club = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    athlete1 = models.ForeignKey(Member, verbose_name="Atleta 1", related_name="first_element", on_delete=models.CASCADE)
    athlete2 = models.ForeignKey(Member, verbose_name="Atleta 2", related_name="second_element", on_delete=models.CASCADE)
    athlete3 = models.ForeignKey(Member, verbose_name="Atleta 3", related_name="third_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete4 = models.ForeignKey(Member, verbose_name="Atleta 4", related_name="forth_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete5 = models.ForeignKey(Member, verbose_name="Atleta 5", related_name="fifth_element", on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField("Escalão", max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    team_number = models.IntegerField("Nº Equipa")
    competition = models.ForeignKey(Event, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid("Team", "registration")
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {}".format(self.match_type, self.category, self.gender)


### Classification models ###

class Classification(models.Model):
    competition = models.ForeignKey(Event, on_delete=models.CASCADE)
    first_place = models.ForeignKey(Member, verbose_name="Primeiro Classificado", related_name="first_place", on_delete=models.CASCADE)
    second_place = models.ForeignKey(Member, verbose_name="Segundo Classificado", related_name="second_place", on_delete=models.CASCADE, null=True, blank=True)
    third_place = models.ForeignKey(Member, verbose_name="Terceiro Classificado", related_name="third_place", on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        super().clean()

        athletes = [self.first_place, self.second_place, self.third_place]
        athletes = [a for a in athletes if a is not None]

        if len(set(athletes)) != len(athletes):
            raise ValidationError("Each place must be assigned to a different athlete.")

        categories = {a.category for a in athletes}
        if len(categories) > 1:
            raise ValidationError("All athletes must belong to the same category.")
        
        genders = {a.gender for a in athletes}
        if len(genders) > 1:
            raise ValidationError("All athletes must belong to the same gender.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {} Classification".format(self.competition.name, self.first_place.category, self.first_place.gender.capitalize())
