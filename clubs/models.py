from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from events.models import Event

# Create your models here.

class Club(models.Model):
    """
    Model that holds names to be used as usernames. 
    Can only be created when a 'main_admin' is created and can be linked.
    These same admin accounts can create these objects, and can only create usernames for themselves.
    The username for the admin accounts should not be listed here.
    """
    name = models.CharField("Clube", max_length=99, unique=True)
    is_registered = models.BooleanField(default=False)
    mother_acount = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        limit_choices_to={'role': 'main_admin'},
    )
    is_admin = models.BooleanField(default=False)

    def clean(self):
        # If no Club exists yet, allow creating the first one without mother_acount
        if not Club.objects.exists():
            return  
        
        if not self.is_admin:
            
            if not self.mother_acount:
                raise ValidationError({"mother_acount": "This field is required."})

            ### TODO: Add this after
            # if self.mother_acount.role != "main_admin":
            #     raise ValidationError({"mother_acount": "Mother account must be a main_admin."})
        
        super().clean()


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ClubRatingAudit(models.Model):
    club = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, editable=False)
    rating = models.IntegerField("Avaliação", default=0, editable=False)

    def __str__(self):
        return '{} {} rating'.format(self.club, self.event)
    

class Profile(models.Model):
    club = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')
    club_contact = models.IntegerField("Contacto do Clube", default=123456789)
    cellphone_number = models.IntegerField("Número de telemóvel pessoal", default=123456789)

    def __str__(self):
        return f'{self.club.username} profile'
