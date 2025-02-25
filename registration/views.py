from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from .templatetags.team_extras import valid_athletes
from django.contrib.auth.decorators import login_required
from .forms import AthleteForm, FilterAthleteForm, TeamForm, FilterTeamForm
import datetime
from django.contrib import messages
from .utils.utils import check_athlete_data, get_comp_age, check_filter_data, check_match_type, check_teams_data
from dojos.utils.utils import get_next_competition
from .models import Athlete, Team, Individual
from dojos.models import CompetitionDetail

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

### Athletes processing ###

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
            matches, match_type_error = check_match_type(request)

            if len(match_type_error) > 0:
                errors.append(match_type_error)
            
            for match in matches:
                if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=match).exists():
                    errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se quer inscrever a mesma pessoa noutra prova")

                else:
                    errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules, matches)
            
            if len(errors) != 0:
                request.session['can_access_target_page'] = True
                for error in errors:
                    messages.error(request, error)
                context = {"form": form, "title": "Inscrever atleta"}
                return render(request, 'registration/form.html', context)
            
            for match in matches:
                new_athlete = form.save(commit=False) 
                new_athlete.dojo = request.user
                new_athlete.age = age_at_comp
                new_athlete.match_type = match
                
                # if "kata", weight is set to None
                if match == "kata":
                    new_athlete.weight = None
                else:
                    new_athlete.weight = request.POST.dict().get("weight")

                # reset id to prevent overwrite
                new_athlete.pk = None

                # save
                new_athlete.save()

            messages.success(request, f'{new_athlete.first_name} {new_athlete.last_name} registad@ com sucesso!')
            # form will allow thanks to open
            request.session['can_access_target_page'] = True
            # redirect to a new URL:
            action = request.POST.get("action")
            if action == "save_back":
                return HttpResponseRedirect("/athletes/")
            elif action == "save_add":
                return HttpResponseRedirect("/form/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AthleteForm()
        context = {"form": form, "title": "Inscrever atleta"}
        return render(request, 'registration/form.html', context)


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


### Individuals processing ###

@login_required
def individual(request, comp_id):
    individuals = Individual.objects.filter(competition=comp_id)
    comp_detail = CompetitionDetail.objects.filter(id=comp_id).first()
    number_individuals = len(individuals)
    is_closed = datetime.date.today() > comp_detail.retifications_deadline and not comp_detail.has_ended
    return render(request, 'registration/individuals.html', {"individuals": individuals,
                                                             "title": "Individual",
                                                             "number_indiv": number_individuals,
                                                             "comp_id": comp_id,
                                                             "is_closed": is_closed})

@login_required
def athletes_preview(request, comp_id):
    if request.method == "POST":
        positive_ids = [k for k, v in request.POST.dict().items() if v == "on"]
        for pos_id in positive_ids:
            athlete_instance = get_object_or_404(Athlete, id=pos_id)
            if not Individual.objects.filter(athlete=athlete_instance).exists():
                Individual.objects.create(dojo=request.user, athlete=athlete_instance, competition=get_next_competition())
                if len(positive_ids) <= 2:
                    messages.success(request, f"{athlete_instance.first_name} {athlete_instance.last_name} inscrito em {athlete_instance.match_type.capitalize()} {athlete_instance.category} {athlete_instance.gender.capitalize()}")
            else:
                messages.error(request, f"{athlete_instance.first_name} {athlete_instance.last_name} já está inscrito em {athlete_instance.match_type.capitalize()} {athlete_instance.category} {athlete_instance.gender.capitalize()}")
        if len(positive_ids) > 2:
            messages.success(request, f"{len(positive_ids)} atletas inscritos em individual")  
        return HttpResponseRedirect(f"/individuals/{comp_id}")
    else:
        athletes = Athlete.objects.filter(dojo=request.user)
        number_athletes = len(athletes)
        athletes = sorted(athletes, key = lambda x: x.first_name)
        context = {"athletes": athletes,
                "number_athletes": number_athletes,
                "title": "Seleção de atletas"}
        return render(request, 'registration/athletes_preview.html', context=context)


### Teams processing ###

@login_required
def team_form(request, match_type, comp_id):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            errors = check_teams_data(form)

            if len(errors) != 0:
                request.session['can_access_target_page'] = True
                for error in errors:
                    messages.error(request, error)
                context = {"form": form, "title": "Inscrever Equipa", "comp_id": comp_id}
                return render(request, 'registration/teams_form.html', context)
            
            teams = Team.objects.filter(dojo=request.user,
                                         category=form.cleaned_data["category"], 
                                         match_type=match_type,
                                         gender=form.cleaned_data["gender"])
            new_team = form.save(commit=False)
            new_team.dojo = request.user
            new_team.match_type = match_type
            new_team.team_number = len(teams) + 1
            new_team.save()
            request.session['can_access_target_page'] = True
            request.session['team'] = True

            action = request.POST.get("action")
            if action == "save_back":
                return HttpResponseRedirect(f"/teams/{comp_id}")
            elif action == "save_add":
                return HttpResponseRedirect(f"/teams_form/{match_type}/{comp_id}")

    else:
        form = TeamForm(dojo=request.user, match_type=match_type)
        context = {"form": form, "title": "Inscriver Equipa", "match_type": match_type, "comp_id": comp_id}
        return render(request, 'registration/teams_form.html', context)


@login_required
def teams(request, comp_id):
    not_found = False
    if request.method == "POST":
        filter_form = FilterTeamForm(request.POST)
        if filter_form.is_valid():
            teams = Team.objects.filter(dojo=request.user)
            teams, not_found = check_filter_data(request, filter_form, teams)
    else:
        filter_form = FilterTeamForm()
        teams = Team.objects.filter(dojo=request.user)
    number_teams = len(teams)
    return render(request, 'registration/teams.html', {"teams": teams, 
                                                      "filters": filter_form, 
                                                      "not_found": not_found,
                                                      "comp_id": comp_id,
                                                      "number_teams": number_teams,
                                                      "title": "Equipas"})


### Auxiliar pages ###

def home(request):
    comp_details = CompetitionDetail.objects.all()
    comp_details = sorted(comp_details, key = lambda x: x.competition_date)
    return render(request, 'registration/home.html', {"comps": comp_details})


def comp_details(request, comp_id):
    comp_detail = CompetitionDetail.objects.filter(id=comp_id).first()
    today = datetime.date.today()
    # check registrations status
    is_open = today > comp_detail.start_registration and today < comp_detail.end_registration
    is_retification = today > comp_detail.end_registration and today < comp_detail.retifications_deadline
    is_closed = today > comp_detail.retifications_deadline and not comp_detail.has_ended
    has_teams = "Torneio" in comp_detail.name
    print(has_teams)
    return render(request, 'registration/comp_details.html', {"comp_detail": comp_detail,
                                                              "is_open": is_open,
                                                              "is_retification": is_retification,
                                                              "is_closed": is_closed,
                                                              "has_teams": has_teams})


def help(request):
    return render(request, 'registration/help.html')


### Registrations operations ###

def delete(request, type, id, comp_id):
    if request.method == "POST":

        # deletes an athlete
        if type == "athlete":
            object_of = Athlete.objects.filter(id=id)[0]

            # check if there's an individual with the athlete to be removed
            if Individual.objects.filter(athlete=object_of).exists():
                messages.error(request, f"{object_of.first_name} {object_of.last_name} está inscrit@ numa prova Individual. Elimine a inscrião correspondente em primeiro lugar")
                return HttpResponseRedirect(f"/individuals/{comp_id}")
            
            # check if there's a team with the the athlete to be removed
            teams = Team.objects.all()
            for team in teams:
                valid = valid_athletes(team)
                for athlete in valid:
                    if Individual.objects.filter(athlete=athlete).exists():
                        messages.error(request, f"{athlete.first_name} {athlete.last_name} está inscrit@ numa prova de Equipas. Elimine a inscrião correspondente em primeiro lugar")
                        return HttpResponseRedirect("/teams/")
            
            # if none, delete the athlete
            message = f'Atleta com o nome {object_of.first_name} {object_of.last_name} eliminad@ com sucesso!'
        
        # deletes a team
        elif type == "team":
            object_of = get_object_or_404(Team, id=id)
            message = f'Equipa com o número {object_of.team_number} eliminada com sucesso'
        
        # deletes an individual
        else:
            object_of = get_object_or_404(Individual, id=id)
            message = f'Inscrição d@ {object_of.athlete.first_name} {object_of.athlete.last_name} eliminada com sucesso!'

        messages.success(request, message)
        object_of.delete()
    
    # GET will delete all objects, id should always equal to 0
    else:
        if type == "athlete":
            Athlete.objects.all().delete()
        elif type == "team":
            Team.objects.all().delete()
        else:
            Individual.objects.all().delete()
        messages.success(request, 'Atletas eliminados' if type == "athlete" or type == "individual" else 'Equipas eliminadas')
    return HttpResponseRedirect(f"/{type}s/{comp_id}") if type == "individual" or type == "team" else HttpResponseRedirect(f"/{type}s/")


def update(request, type, id):
    if type == "athlete":
        athlete = get_object_or_404(Athlete, id=id)
    else:
        team = get_object_or_404(Team, id=id)

    if request.method == "POST":
        errors = []
        if type == "athlete":
            message = f'Informação de {athlete.first_name} {athlete.last_name} atualizada!'
            form = AthleteForm(request.POST, instance=athlete)
            if form.is_valid():
                birth_date = form.cleaned_data["birth_date"]
                age_at_comp = get_comp_age(birth_date)

            if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type")).exists():
                athlete_test = Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type"))
                if athlete_test[0].id != athlete.id:
                    errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se quer inscrever a mesma pessoa noutra prova")
                else:
                    errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
            else:
                errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
        else:
            message = f'Informação da equipa nº {team.team_number} atualizada!'
            form = TeamForm(request.POST, instance=team)
        # if form.is_valid():
        if len(errors) > 0:
            messages.error(request, "Não foi possível atualizar")
            for error in errors:
                messages.error(request, error)
            return HttpResponseRedirect(f"/update_registration/{type}/{id}/")
        else:
            new_form = form.save(commit=False) 
            new_form.dojo = request.user
            new_form.age = age_at_comp
            new_form.save()
            messages.success(request, message)
            return HttpResponseRedirect("/athletes/") if type == "athlete" else HttpResponseRedirect("/teams/")
    else:
        form = AthleteForm(instance=athlete) if type == "athlete" else TeamForm(instance=team, dojo=request.user)
        return render(request, 'registration/update_registration.html', {"form": form, 
                                                                         "type": type, 
                                                                         "id": id, 
                                                                         "title": "Atualizar Atleta" if type == "athlete" else "Atualizar Equipa"})