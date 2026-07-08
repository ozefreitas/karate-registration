from django.db import models
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import calendar

from nanoid import generate
from datetime import date
from core.constants import GENDERS, GRADUATIONS

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


### Person model ###

class Person(models.Model):

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    profile_image = models.ImageField(
        upload_to="members/profile_images/",
        blank=True,
        null=True
    )
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
        related_name="created_by",
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_by",
        null=True,
        blank=True
    )
    conditions = models.TextField("Condições Médicas", blank=True, null=True)
    observations = models.TextField("Observações", blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_validated = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["first_name", "last_name", "birth_date", "id_number"],
                name="unique_member_identity_fields"
            )
        ]
    
    def current_month_payment(self):
        """Returns paid if the member paid this month's quota."""
        if not self.quotes_legible:
            return None
        
        today = date.today()
        
        if MonthlyPersonPayment.objects.filter(person=self, 
                                               year=today.year, 
                                               month=today.month, 
                                               paid=True).exists():
            return "paid"
        else: return "unpaid"
    
    def past_month_payment(self):
        """Returns 'paid', 'unpaid', or None for the previous month quota."""
        if not self.quotes_legible:
            return None

        today = date.today()
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1

        payment = MonthlyPersonPayment.objects.filter(
            person=self,
            year=year,
            month=month,
        ).first()

        return None if not payment else ("paid" if payment.paid else "unpaid")

    def clean(self):
        member_types = self.member_types.values_list("member_type", flat=True)
        if "coach" in member_types and self.favorite == True:
            raise ValidationError("Coaches are not qualified as favorite.")
        
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid(self.__class__.__name__, self._meta.app_label)
        
        if not self.registration_date:
            self.registration_date = date.today()
        
        if self.created_by is not None and self.created_by.role == 'main_admin':
            self.is_validated = True

        super().save(*args, **kwargs)

    def __str__(self): 
        return "{} {} | {}".format(self.first_name, self.last_name, self.club.username)


class Membership(models.Model):

    class MEMBER_TYPE(models.TextChoices):
        STUDENT = "student", "Student"
        ATHLETE = "athlete", "Athlete"
        COACH = "coach", "Coach"
    
    member_type = models.CharField(max_length=16, choices=MEMBER_TYPE.choices, default=MEMBER_TYPE.ATHLETE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="member_types")
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("person", "member_type")

    def __str__(self): 
        return "{} {} | {} ({})".format(self.person.first_name, self.person.last_name, self.person.club.username, self.member_type)


class MonthlyPersonPayment(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()  # 1=Jan ... 12=Dec
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    due_date = models.DateTimeField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("person", "year", "month")
        ordering = ["-year", "-month"]
    
    def save(self, *args, **kwargs):
        if not self.due_date: 
            last_day_of_month = calendar.monthrange(self.year, self.month)[1]

            date_to_save = datetime(
                year=self.year, 
                month=self.month, 
                day=last_day_of_month, 
                hour=23, 
                minute=59, 
                second=59, 
                tzinfo=timezone.get_current_timezone()
                )

            self.due_date = date_to_save
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        self.paid = True
        self.paid_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} {self.month}-{self.year} subscription"


class MonthlyPersonPaymentConfig(models.Model):
    """
    Stores payment amount for each Person.
    Each Person should have exactly one config row, with a fixed amount, that can then be changed by the Club of that Person.
    That amount can be set just for this person, or chosen from a pre defined plan
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="monthly_person_payment_config")
    base_plan = models.ForeignKey("core.MonthlyPaymentPlan", on_delete=models.PROTECT)
    # This is the per-person amount (default copied from the base plan)
    custom_amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True
    )
    is_custom_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If custom amount not set, default to plan amount
        if self.custom_amount is None:
            self.custom_amount = self.base_plan.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} - subscription amount: {self.custom_amount}"

    @staticmethod
    def get_amount_for(person):
        """
        Returns the person's amount.
        """
        obj, _ = MonthlyPersonPaymentConfig.objects.get(person=person)
        if obj.is_custom_active:
            return obj.custom_amount
        else:
            obj.base_plan.amount


### Teams models ###

class Team(models.Model):

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    club = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    athlete1 = models.ForeignKey(Person, verbose_name="Atleta 1", related_name="first_element", on_delete=models.CASCADE)
    athlete2 = models.ForeignKey(Person, verbose_name="Atleta 2", related_name="second_element", on_delete=models.CASCADE)
    athlete3 = models.ForeignKey(Person, verbose_name="Atleta 3", related_name="third_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete4 = models.ForeignKey(Person, verbose_name="Atleta 4", related_name="forth_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete5 = models.ForeignKey(Person, verbose_name="Atleta 5", related_name="fifth_element", on_delete=models.CASCADE, blank=True, null=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    category = models.ForeignKey("core.Category", on_delete=models.CASCADE, verbose_name="Escalão")
    team_number = models.IntegerField("Nº Equipa")
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def clean(self):
        athletes = [
            self.athlete1,
            self.athlete2,
            self.athlete3,
            self.athlete4,
            self.athlete5,
        ]
        athletes = [a for a in athletes if a is not None]

        if len(athletes) != len(set(athletes)):
            raise ValidationError("A team cannot contain the same athlete more than once.")

        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid("Team", "registration")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.athlete1.first_name} {self.athlete1.last_name} | {self.athlete2.first_name} {self.athlete2.last_name} | {self.athlete3.first_name} {self.athlete3.last_name} - {self.club.username}"
    

### Classification models ###

class Classification(models.Model):
    PLACE_CHOICES = {
        1: "1st Place",
        2: "2nd Place",
        3: "3rd Place",
    }

    bracket = models.ForeignKey("draw.Bracket", on_delete=models.CASCADE, related_name="classifications")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="classifications", null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="classifications", null=True, blank=True)
    place = models.PositiveSmallIntegerField(choices=PLACE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["bracket", "place"] 

        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} - {} - {}º Lugar - {} {}".format(self.bracket.event.name, self.bracket.event.season, self.bracket.name, self.place, self.person.first_name, self.person.last_name)
