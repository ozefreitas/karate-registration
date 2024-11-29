from django import forms
from .models import Athlete, Filters

class AthleteForm(forms.ModelForm):

    # MATCHES = {
    #     "kata": "Kata",
    #     "kumite": "Kumite"
    # }

    # match_type = forms.MultipleChoiceField(
    #     choices=MATCHES,
    #     widget=forms.CheckboxSelectMultiple,
    #     label="Prova",
    #     # initial=['kata'],
    #     required=False  # Set to True if the field is mandatory
    # )

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the attributes of each field
        
        self.fields['first_name'].help_text = "<br><ul><li>Recomendado apenas um nome. Se tiver atletas com nomes iguais ou parecidos, deve colocar outro nome que os diferencie.</li></uL>"


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filters
        fields = "__all__"