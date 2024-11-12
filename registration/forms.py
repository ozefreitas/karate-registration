from django.forms import ModelForm
from .models import Athlete

class AthleteForm(ModelForm):
    class Meta:
        model = Athlete
        fields = "__all__"