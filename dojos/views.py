from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import DojoRegisterForm, DojoUpdateForm, ProfileUpdateForm, FeedbackForm, DojoPasswordResetForm, DojoPasswordConfirmForm, DojoPasswordChangeForm
from .models import CompetitionDetail
from django.template.loader import render_to_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from registration.models import Dojo, ArchivedAthlete, Athlete
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
from django.contrib.auth import update_session_auth_hash

def register_user(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = DojoRegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            form.save()
            dojo = form.cleaned_data.get("username")
            messages.success(request, f'Sucesso! Conta criada para o dojo {dojo}')
            return HttpResponseRedirect("/register/login/")
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect("/wrong")

    else:
        form = DojoRegisterForm()
        return render(request, 'dojos/register_user.html', {"form": form, "title": "Criar Conta"})

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login efetuado com sucesso")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, "Credênciais inválidas")
            messages.error(request, "Pista: O nome de utilizador tem o nome do Dojo que selecionou aquando da criação da conta")
            return HttpResponseRedirect("/register/login/")
    else:
        return render(request, "dojos/login.html", {"title": "Plataforma Login"})

@login_required
def logout_user(request):
    logout(request)
    return render(request, "dojos/logout.html")

@login_required
def profile(request):
    comps = CompetitionDetail.objects.all()
    archived_athletes = ArchivedAthlete.objects.all()
    return render(request, 'dojos/profile.html', {"title": "Perfil",
                                                  "archived_athletes": archived_athletes,
                                                  "comps": comps})

def feedback(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = FeedbackForm(request.POST)
        # check whether it's valid:
        if form.is_valid():

            # TODO: add notification to admin that a feedback message has just arrived
            
            form.save()
            messages.success(request, "Obrigado pelo feedback. Entrarei em contacto brevemente ")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect("/wrong")
            
    else:
        form = FeedbackForm()
        return render(request, 'dojos/feedback.html', {"form": form, "title": "Feedback"})
    
def update_dojo_account(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form_dojo = DojoUpdateForm(request.POST, instance=request.user)
        form_profile = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        # check whether it's valid:
        if form_dojo.is_valid() and form_profile.is_valid():
            form_dojo.save()
            form_profile.save()
            messages.success(request, "Perfil atualizado com sucesso! ")
            return HttpResponseRedirect("/profile")
        else:
            messages.error(request, form_dojo.errors)
            messages.error(request, form_profile.errors)
            return HttpResponseRedirect("/wrong")
            
    else:
        form_dojo = DojoUpdateForm(instance=request.user)
        form_profile = ProfileUpdateForm(instance=request.user.profile)
        context = {"form_dojo": form_dojo, "form_profile": form_profile, "title": "Atualizar Perfil"}
    return render(request, 'dojos/update_user.html', context)

def delete_dojo_account(request):
    if request.method == "GET":
        if not request.user.is_superuser:
            object_of = get_object_or_404(User, username=request.user.username)
            message = f'Utilizador {object_of.first_name} {object_of.last_name} eliminado com sucesso!'
            messages.success(request, message)
            object_of.delete()
            Dojo.objects.filter(dojo=request.user.username).update(is_registered=False)
            return HttpResponseRedirect("/register/register_user/")
    return HttpResponseRedirect("/")

@login_required
def change_password(request):
    if request.method == "POST":
        form = DojoPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session to prevent logging out after password change
            update_session_auth_hash(request, user)
            return HttpResponseRedirect('/profile/')
    else:
        form = DojoPasswordChangeForm(user=request.user)
        return render(request, 'password/change_password.html', {"form": form})

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        form = DojoPasswordResetForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, email=email)
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = request.build_absolute_uri(f"/register/password_reset_confirm/{uid}/{token}/")
            try:
                send_mail(
                    subject="Recuperação de Password - Karate Score App",
                    message="Está a receber este email porque pediu a recuperação da sua conta na plaforma de registos da SKI-Portugal.\n\n"
                            "Por favor, aceda ao link seguinte para continuar o processo, e escolher uma nova palavra passe.\n\n"
                            f"{reset_url}\n\n"
                            f"O seu nome de utilizador, caso se tenha esquecido, é   {user.username}.\n\n"
                            "Obrigado por usar a Karate Score App.\n"
                            "A equipa da Karate Score App:\n"
                            "José Freitas\n\n"
                            "Contactos:\n- jpsfreitas12@gmail.com / 917479331\n- info@skiportugal.pt",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as exc:
                raise SMTPException(exc)

            return HttpResponseRedirect("/register/password_reset/done/")
    else:
        form = DojoPasswordResetForm()
        return render(request, 'password/reset_password.html', {"form": form})
    
def password_reset_confirmation(request, 
                                uidb64, 
                                token
                                ):
    form = DojoPasswordConfirmForm()
    if request.method == "POST":
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")
        if new_password1 != new_password2:
            messages.error(request, "Palavras passe inseridas não são iguais!")
            return render(request, "dojos/reset_password_confirm.html", {"form": form})
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if PasswordResetTokenGenerator().check_token(user, token):
                user.password = make_password(new_password1)
                user.save()
                return render(request, "dojos/password_reset_complete.html")
            else:
                return render(request, "Invalid or expired token.", status=400)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(request, "Invalid link.", status=400)
    else:
        return render(request, "password/reset_password_confirm.html", {"form": form})

def clone_athletes(request, comp_id):
    if request.method == "POST":
        comp = get_object_or_404(CompetitionDetail, id=comp_id)
        archived = ArchivedAthlete.objects.filter(competition=comp_id)
        for athlete in archived:
            athlete_data = {}
            for field in athlete._meta.fields:
                if field.name not in ["id", "competition", "archived_date"]:
                    athlete_data[field.name] = getattr(athlete, field.name)
            Athlete.objects.create(**athlete_data)
        messages.success(request, f'Os atletas da/do {comp.name} foram copiados para o registo atual')
    return HttpResponseRedirect("/athletes")

def custom_404(request, exception):
    return render(request, 'error/404.html', status=500)

def custom_500(request):
    return render(request, 'error/500.html', status=500)

def test_500_error(request):
    raise("This is a test error")