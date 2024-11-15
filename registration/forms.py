from django import forms
from .models import Athlete

class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ["first_name", 
                    "last_name",
                    "graduation",
                    "birth_date",
                    "gender",
                    "skip_number",
                    "category",
                    "match_type",
                    "weight",
                    "additional_emails"]
        widgets = {
            'birth_date': forms.DateInput(
                attrs={
                    'type': 'date',  # Renders an HTML5 date picker in modern browsers
                }
            )
        }