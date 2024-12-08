from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import AthleteForm, FilterAthleteForm, TeamForm, FilterTeamForm
from datetime import datetime
from django.contrib import messages
from .utils.utils import check_athlete_data, get_comp_age, check_filter_data
from .models import Athlete, Teams

# views for the athlets registrations

age_graduation_rules = {
    "0-9": 15,
    "10-11": 15,
    "12-13": 14,
    "14-15": 13,
    "16-17": 12,
    "18-50": 11
}

age_category_rules = {
    "0-9": "Infantil",
    "10-11": "Iniciado",
    "12-13": "Juvenil",
    "14-15": "Cadete",
    "16-17": "Júnior",
    "18-34": "Sénior",
    "35-49": "Veterano +35",
    "50-99": "Veterano +50"
}

@login_required()
def form(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AthleteForm(request.POST)
        errors = []
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            birth_date = form.cleaned_data["birth_date"]
            age_at_comp = get_comp_age(birth_date)

            if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type")).exists():
                errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se a quer inscrever a mesma pessoa noutra prova")

            else:
                errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
            
            if len(errors) != 0:
                request.session['can_access_target_page'] = True
                for error in errors:
                    messages.error(request, error)
                return HttpResponseRedirect("/wrong")
            
            new_athlete = form.save(commit=False) 
            new_athlete.dojo = request.user
            new_athlete.age = age_at_comp
            new_athlete.save()
            messages.success(request, f'{new_athlete.first_name} {new_athlete.last_name} registad@ com sucesso!')
            # form will allow thanks to open
            request.session['can_access_target_page'] = True
            # redirect to a new URL:
            return HttpResponseRedirect("/thanks/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AthleteForm()
        context = {"form": form, "title": "Inscrever atleta"}
        return render(request, 'registration/form.html', context)
    
@login_required
def team_form(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        print(request.POST)
        if form.is_valid():
            teams = Teams.objects.filter(dojo=request.user, 
                                         category=form.cleaned_data["category"], 
                                         match_type=form.cleaned_data["match_type"],
                                         gender=form.cleaned_data["gender"])
            for key, value in form.cleaned_data.items():
                if key.startswith("athlete"):
                    print(value)
            new_team = form.save(commit=False) 
            new_team.dojo = request.user
            new_team.team_number = len(teams) + 1
            new_team.save()
            request.session['can_access_target_page'] = True
            request.session['team'] = True
            # redirect to a new URL:
            return HttpResponseRedirect("/thanks/")
    else:
        form = TeamForm(dojo=request.user)
        context = {"form": form, "title": "Inscriver Equipa"}
        return render(request, 'registration/teams_form.html', context)

@login_required
def athletes(request):
    not_found = False
    if request.method == "POST":
        filter_form = FilterAthleteForm(request.POST)
        if filter_form.is_valid():
            athletes = Athlete.objects.filter(dojo=request.user)
            athletes, not_found = check_filter_data(request, filter_form, athletes)
    else:
        filter_form = FilterAthleteForm()
        athletes = Athlete.objects.filter(dojo=request.user)
    number_athletes = len(athletes)
    return render(request, 'registration/athletes.html', {"athletes": athletes,
                                                      "filters": filter_form, 
                                                      "not_found": not_found, 
                                                      "number_athletes": number_athletes,
                                                      "title": "Atletas"})

@login_required
def teams(request):
    not_found = False
    if request.method == "POST":
        filter_form = FilterTeamForm(request.POST)
        if filter_form.is_valid():
            teams = Teams.objects.filter(dojo=request.user)
            teams, not_found = check_filter_data(request, filter_form, teams)
    else:
        filter_form = FilterTeamForm()
        teams = Teams.objects.filter(dojo=request.user)
    number_teams = len(teams)
    return render(request, 'registration/teams.html', {"teams": teams, 
                                                      "filters": filter_form, 
                                                      "not_found": not_found,
                                                      "number_teams": number_teams,
                                                      "title": "Equipas"})

def home(request):
    return render(request, 'registration/home.html')

def thanks(request):
    # if not from form, cannot access this url
    if not request.session.get('can_access_target_page', False):
        return HttpResponseRedirect('/')
    request.session['can_access_target_page'] = False
    if not request.session.get('team', False):
        from_where = "athlete"
    else: from_where = "team"
    request.session['team'] = False
    return render(request, "registration/thanks.html", {"from_where": from_where})

def wrong(request):
    if not request.session.get('can_access_target_page', False):
        return HttpResponseRedirect('/')
    request.session['can_access_target_page'] = False
    return render(request, "registration/wrong.html")

def delete(request, type, id):
    if request.method == "POST":
        if type == "athlete":
            object_of = get_object_or_404(Athlete, id=id)
            message = f'Atleta com o nome {object_of.first_name} {object_of.last_name} eliminad@ com sucesso!'
        else:
            object_of = get_object_or_404(Teams, id=id)
            message = f'Equipa com o número {object_of.team_number} eliminada com sucesso'
        messages.success(request, message)
        object_of.delete()
        return HttpResponseRedirect("/athletes/") if type == "athlete" else HttpResponseRedirect("/teams/")

def update(request, type, id):
    if type == "athlete":
        athlete = get_object_or_404(Athlete, id=id)
    else:
        team = get_object_or_404(Teams, id=id)

    if request.method == "POST":
        errors = []
        if type == "athlete":
            message = f'Informações de {athlete.first_name} {athlete.last_name} atualizadas!'
            form = AthleteForm(request.POST, instance=athlete)
            if form.is_valid():
                birth_date = form.cleaned_data["birth_date"]
                age_at_comp = get_comp_age(birth_date)

            if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type")).exists():
                athlete_test = Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type"))
                if athlete_test[0].id != athlete.id:
                    errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se a quer inscrever a mesma pessoa noutra prova")
                else:
                    errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
            else:
                errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
        else:
            message = f'Informações da equipa nº {team.team_number} atualizadas!'
            form = TeamForm(request.POST, instance=team)
        # if form.is_valid():
        if len(errors) > 0:
            messages.error(request, "Não foi possível atualizar")
            for error in errors:
                messages.error(request, error)
            return HttpResponseRedirect("/wrong")
        else:
            new_form = form.save(commit=False) 
            new_form.dojo = request.user
            new_form.save()
            messages.success(request, message)
        return HttpResponseRedirect("/athletes/") if type == "athlete" else HttpResponseRedirect("/teams/")
    else:
        form = AthleteForm(instance=athlete) if type == "athlete" else TeamForm(instance=team, dojo=request.user)
        # athletes = Athlete.objects.filter(dojo=request.user)
        return render(request, 'registration/update_registration.html', {"form": form, "type": type, "id": id})