from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from registration.models import Dojo
from .models import FeedbackData, Profile, PasswordConfirmReset
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm


class DojoRegisterForm(UserCreationForm):
    username = forms.ModelChoiceField(queryset=Dojo.objects.filter(is_registered = False),
                                    empty_label="Selecione um dojo")
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the attributes of each field

        # username
        self.fields['username'].help_text = " \t Escolha um dojo disponível. Copie e guarde este nome, pois será o que vai usar para fazer login."
        self.fields['username'].label = "Nome de utilizador (dojo)"
        self.fields['username'].widget.attrs.update({'placeholder': 'Inserir nome'})

        # first_name
        self.fields['first_name'].label = "Primeiro Nome"
        self.fields['first_name'].widget.attrs.update({'placeholder': 'p.e. Sónia'})

        # last_name
        self.fields['last_name'].help_text = None
        self.fields['last_name'].label = "Último Nome"
        self.fields['last_name'].widget.attrs.update({'placeholder': 'p.e. Marinho'})

        # email
        self.fields['email'].widget.attrs.update({'placeholder': 'p.e. soniamarinho@gmail.com'})

        # password1
        self.fields['password1'].help_text = "<ul><li>Não pode ser muito semelhante à informação fornecida acima;</li>\
                                                <li>Tem de ter pelo menos 8 caracteres;</li>\
                                                <li>Não pode ser uma palavra passe muito utilizada;</li>\
                                                <li>Não pode ser só numérica.</li></ul>"
        self.fields['password1'].label = "Palavra Passe"

        # password2
        self.fields['password2'].help_text = None
        self.fields['password2'].label = "Repetir Palavra Passe"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']  # Use the team name as the username
        if commit:
            user.save()
            # Mark the team as registered
            Dojo.objects.filter(dojo=self.cleaned_data['username']).update(is_registered=True)
        return user


class DojoUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the attributes of each field

        # first_name
        self.fields['first_name'].label = "Primeiro Nome"

        # last_name
        self.fields['last_name'].label = "Último Nome"

        # emaik
        self.fields['email'].label = "Email"


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image", "dojo_contact", "cellphone_number"]


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackData
        fields = "__all__"


class DojoPasswordResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ["email"]


class DojoPasswordConfirmForm(forms.ModelForm):

    new_password1 = forms.CharField(max_length=36, widget=forms.PasswordInput)
    new_password2 = forms.CharField(max_length=36, widget=forms.PasswordInput)

    class Meta:
        model = PasswordConfirmReset
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the attributes of each field

        self.fields['new_password1'].label = "Palavra Passe"
        self.fields['new_password1'].help_text = "<ul><li>Tem de ter pelo menos 8 caracteres;</li>\
                                                <li>Não pode ser uma palavra passe muito utilizada;</li>\
                                                <li>Não pode ser só numérica.</li></ul>"
        
        self.fields['new_password2'].label = "Repetir Palavra Passe"


class DojoPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the attributes of each field

        # old password
        self.fields['old_password'].help_text = "<ul><li>Não pode ser muito semelhante às informações do perfil;</li>\
                                                <li>Tem de ter pelo menos 8 caracteres;</li>\
                                                <li>Não pode ser uma palavra passe muito utilizada;</li>\
                                                <li>Não pode ser só numérica.</li></ul>"
        self.fields['old_password'].label = "Palavra Passe"

        # new  password 1
        self.fields['new_password1'].help_text = None
        self.fields['new_password1'].label = "Repetir Palavra Passe"

        # new password 2
        self.fields['new_password2'].help_text = None
        self.fields['new_password2'].label = "Repetir Palavra Passe"