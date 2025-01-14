from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import DojoRegisterForm, DojoUpdateForm, ProfileUpdateForm, FeedbackForm
from .models import Profile, CompetitionDetail
from django.contrib.auth.models import User
from registration.models import Dojo, ArchivedAthlete, Athlete
from django.contrib.auth import logout

# Create your views here.

def register_user(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = DojoRegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            form.save()
            dojo = form.cleaned_data.get("username")
            messages.success(request, f'Sucesso! Conta criada para o dojo {dojo}')
            return HttpResponseRedirect("/login/")
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect("/wrong")

    else:
        form = DojoRegisterForm()
        return render(request, 'dojos/register_user.html', {"form": form, "title": "Criar Conta"})
    

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