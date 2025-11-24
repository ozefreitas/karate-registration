from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from core.constants import ENCOUNTERS, SEASONS

# Create your models here.

class Event(models.Model):

    id = models.SlugField(primary_key=True, unique=True, max_length=100, blank=True)
    name = models.CharField("Nome", max_length=99)
    location = models.CharField("Local", max_length=99)
    season = models.CharField("Época", choices=SEASONS, max_length=15)
    start_registration = models.DateField("Início das inscrições", null=True, blank=True)
    end_registration = models.DateField("Fim das inscrições", null=True, blank=True)
    retifications_deadline = models.DateField("Fim do periodo de retificações", null=True, blank=True)
    event_date = models.DateField("Dia da prova")
    description = models.TextField("Descrição", default="", blank=True, null=True)
    custody = models.CharField("Tutela", max_length=99, default="", null=True, blank=True)
    email_contact = models.EmailField("Email", default="jpsfreitas19@gmail.com", null=True, blank=True)
    contact = models.PositiveIntegerField("Contacto", default="123456789", null=True, blank=True)
    individuals = models.ManyToManyField("registration.Member", related_name='general_events', blank=True)
    has_ended = models.BooleanField(default=False)
    has_registrations = models.BooleanField(default=False)
    has_categories = models.BooleanField(default=False)
    has_teams = models.BooleanField(default=False)
    encounter = models.BooleanField("É estágio/encontro", default=False)
    encounter_type = models.CharField("Estágio", choices=ENCOUNTERS, max_length=16, blank=True, null=True, default=ENCOUNTERS["none"])
    rating = models.IntegerField("Avaliação", default=0)

    # def clean(self):
    #     super().clean()

    def save(self, *args, **kwargs):
        # self.full_clean()

        if self.event_date < datetime.date.today():
            raise ValidationError({"date_error": "Não pode criar Eventos para dias passados."})
        
        if not self.id:  # Auto-generate slug only if not set
            self.id = slugify(f"{self.name} {self.season}")

        super().save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.name, self.season)
    

class Discipline(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='disciplines')
    name = models.CharField("Nome", max_length=100)
    is_team = models.BooleanField(default=False)
    is_coach = models.BooleanField(default=False)
    
    individuals = models.ManyToManyField(
        "registration.Member",
        through="DisciplineMember",
        related_name="disciplines_indiv",
        blank=True
    )
    
    teams = models.ManyToManyField("registration.Team", related_name='disciplines_team', blank=True)
    categories = models.ManyToManyField("core.category", related_name='event_categories', blank=True)

    def add_member(self, member):
        DisciplineMember.objects.get_or_create(
            discipline=self,
            member=member
        )

    def clean(self):
        if self.is_team == self.is_coach:
            raise ValidationError({"error": "Disciplines may not be for coaches and teams at the same time."})
        
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.event.name, self.name)
    

class DisciplineMember(models.Model):
    discipline = models.ForeignKey("Discipline", on_delete=models.CASCADE)
    member = models.ForeignKey("registration.Member", on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('discipline', 'member') 


class FeedbackData(models.Model):
    first_name = models.CharField("Primeiro Nome", max_length=100)
    last_name = models.CharField("Último Nome", max_length=100)
    email = models.EmailField()
    feedback = models.TextField()

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Announcement(models.Model):
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)