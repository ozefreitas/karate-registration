from django import forms
from .models import Athlete, Team, AthleteFilter, TeamFilter

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
                    "skip_number",
                    "category",
                    "gender",
                    "weight"]
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
        
        self.fields['weight'].help_text = "<br><ul><li>Pesos apenas se aplicam aos escalões masculinos.</li><li>Séniores masculinos passarão a ser 'Open' a partir da 3ª Jornada da Liga Soshinkai.</li></uL>"

class FilterAthleteForm(forms.ModelForm):
    class Meta:
        model = AthleteFilter
        fields = "__all__"


class FilterTeamForm(forms.ModelForm):
    class Meta:
        model = TeamFilter
        fields = "__all__"


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["category", "gender", "additional_emails", "athlete1", "athlete2", "athlete3", "athlete4", "athlete5"]
    
    def __init__(self, *args, **kwargs):
        dojo = kwargs.pop('dojo', None)
        match_type = kwargs.pop('match_type', None) 
        super().__init__(*args, **kwargs)
        if dojo:
            self.fields['athlete1'].queryset = Athlete.objects.filter(dojo=dojo, match_type=match_type)
            self.fields['athlete2'].queryset = Athlete.objects.filter(dojo=dojo, match_type=match_type)
            self.fields['athlete3'].queryset = Athlete.objects.filter(dojo=dojo, match_type=match_type)
            self.fields['athlete4'].queryset = Athlete.objects.filter(dojo=dojo, match_type=match_type)
            self.fields['athlete5'].queryset = Athlete.objects.filter(dojo=dojo, match_type=match_type)