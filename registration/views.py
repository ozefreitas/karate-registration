from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_filters.rest_framework import DjangoFilterBackend

from .forms import AthleteForm, FilterAthleteForm, TeamForm, FilterTeamForm, TeamCategorySelection
from .models import Athlete, Team, Individual, Classification
from .filters import IndividualFilters, AthletesFilters
from .templatetags.team_extras import valid_athletes
from .utils.utils import check_athlete_data, get_comp_age, check_filter_data, check_match_type, check_teams_data, check_team_selection
from dojos.models import CompetitionDetail
import datetime
import json
import os

from rest_framework import viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import registration.serializers as serializers

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

CATEGORY_RULES = {
        "Veterano +35": "Sénior",
        "Veterano +50": "Sénior",
        "Sénior": "Júnior",
        "Júnior": "Cadete",
        "Cadete": "Juvenil",
        "Juvenil": "Iniciado",
        "Iniciado": "Infantil",
        "Infantil": "Infantil",
    }

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class AthletesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    # TODO: order get request by the category_index from the serializer
    queryset=Athlete.objects.all()
    serializer_class = serializers.AthletesSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AthletesFilters
    permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": serializers.CreateAthleteSerializer,
        "update": serializers.UpdateAthleteSerializer
    }

    def get_queryset(self):
        return super().get_queryset()

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        # TODO: add authentication
        last_five = Athlete.objects.filter(dojo=request.user).order_by('creation_date')[:5]
        serializer = serializers.AthletesSerializer(last_five, many=True)
        return Response(serializer.data)
    

class IndividualsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Individual.objects.all()
    serializer_class = serializers.IndividualsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IndividualFilters
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": serializers.CreateIndividualSerializer,
        # "update": serializers.UpdateAthleteSerializer
    }

    def perform_create(self, serializer):
        serializer.save(dojo=self.request.user)

class TeamsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Team.objects.all()
    serializer_class = serializers.TeamsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    # serializer_classes = {
    #     "create": serializers.CreateAthleteSerializer,
    #     "update": serializers.UpdateAthleteSerializer
    # }

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        # TODO: add authentication
        last_five = Team.objects.filter(dojo=request.user).order_by('creation_date')[:5]
        serializer = serializers.TeamsSerializer(last_five, many=True)
        return Response(serializer.data)


class ClassificationsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Classification.objects.all()
    serializer_class = serializers.AllClassificationsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": serializers.CreateClassificationsSerializer,
    }

    @action(detail=False, methods=["get"], url_path="per_comp")
    def per_comp(self, request):
        queryset = Classification.objects.all()
        serialized_data = serializers.AllClassificationsSerializer(queryset, many=True)
        final_classification = {}
        competition = ""
        for classification in serialized_data.data:
            comp_dict = {}
            if competition == "" and classification["competition"] == competition:
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            else:
                competition = classification["competition"]
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            if competition not in final_classification.keys():
                final_classification[competition] = [comp_dict]
            else:
                final_classification[competition].append(comp_dict)

        return Response([final_classification])
    
    @action(detail=False, methods=["get"], url_path="last_comp_quali")
    def last_comp_quali(self, request):
        last_competition = CompetitionDetail.objects.filter(has_ended=True).order_by('competition_date').last()
        if last_competition is None:
            return Response([])
        last_comp_quali = Classification.objects.filter(competition=last_competition.id)
        serialized_data = serializers.ClassificationsSerializer(last_comp_quali, many=True)
        return Response(serialized_data.data)

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


class AthletesView(LoginRequiredMixin, View):
    template_name = 'registration/athletes.html'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        # For GET requests, simply instantiate an empty form
        filter_form = FilterAthleteForm()
        athletes = Athlete.objects.filter(dojo=request.user)
        not_found = False
        paginator = Paginator(athletes, self.paginate_by)
        page = request.GET.get('page')

        try:
            athletes_paginated = paginator.page(page)
        except PageNotAnInteger:
            athletes_paginated = paginator.page(1)
        except EmptyPage:
            athletes_paginated = paginator.page(paginator.num_pages)

        number_athletes = len(athletes)
        context = {
            "athletes": athletes_paginated,
            "filters": filter_form,
            "not_found": not_found,
            "number_athletes": number_athletes,
            "title": "Atletas"
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Process the form data on POST requests
        filter_form = FilterAthleteForm(request.POST)
        if filter_form.is_valid():
            athletes = Athlete.objects.filter(dojo=request.user)
            # check_filter_data should return a tuple (filtered athletes, not_found flag)
            athletes, not_found = check_filter_data(request, filter_form, athletes)
        else:
            athletes = Athlete.objects.filter(dojo=request.user)
            not_found = False

        number_athletes = len(athletes)

        paginator = Paginator(athletes, self.paginate_by)
        page = request.GET.get('page')

        try:
            athletes_paginated = paginator.page(page)
        except PageNotAnInteger:
            athletes_paginated = paginator.page(1)
        except EmptyPage:
            athletes_paginated = paginator.page(paginator.num_pages)
        
        context = {
            "athletes": athletes_paginated,
            "filters": filter_form,
            "not_found": not_found,
            "number_athletes": number_athletes,
            "title": "Atletas"
        }
        return render(request, self.template_name, context)


### Individuals processing ###

class IndividualsView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/individuals.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Capture the comp_id from URL kwargs
        comp_id = self.kwargs.get('comp_id')
        comp_detail = CompetitionDetail.objects.filter(id=comp_id).first()
        individuals = Individual.objects.filter(competition=comp_id)
        number_individuals = len(individuals)
        is_closed = datetime.date.today() > comp_detail.retifications_deadline and not comp_detail.has_ended

        paginator = Paginator(individuals, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            individuals_paginated = paginator.page(page)
        except PageNotAnInteger:
            individuals_paginated = paginator.page(1)
        except EmptyPage:
            individuals_paginated = paginator.page(paginator.num_pages)

        context.update({
            "individuals": individuals_paginated,
            "title": "Individual",
            "number_indiv": number_individuals,
            "comp_id": comp_id,
            "comp": comp_detail,
            "is_closed": is_closed
        })
        return context

@login_required
def athletes_preview(request, comp_id):
    if request.method == "POST":
        positive_ids = [k for k, v in request.POST.dict().items() if v == "on"]
        for pos_id in positive_ids:
            athlete_instance = get_object_or_404(Athlete, id=pos_id)
            comp_instance = get_object_or_404(CompetitionDetail, id=comp_id)
            if not Individual.objects.filter(athlete=athlete_instance, competition=comp_instance).exists():
                Individual.objects.create(dojo=request.user, athlete=athlete_instance, competition=comp_instance)
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
        action = request.POST.get("action")
        if action == "search":
            form = TeamCategorySelection(request.POST)

            if form.is_valid():
                error = check_team_selection(form)

                if error is not None:
                    messages.error(request, error)
                    context = {"form": form, "title": "Inscriver Equipa", "match_type": match_type, "comp_id": comp_id}

                    return render(request, 'registration/teams_form.html', context)
                
                athletes = Athlete.objects.filter(gender=form.cleaned_data["gender"], 
                                                  category__in=[form.cleaned_data["category"], CATEGORY_RULES[form.cleaned_data["category"]]],
                                                  match_type=match_type)
                
                context = {"form": form, "athletes": athletes, "title": "Inscriver Equipa", "match_type": match_type, "comp_id": comp_id}
                return render(request, 'registration/teams_form.html', context)
            
        else:
            athlete_instances = []
            positive_ids = [k for k, v in request.POST.dict().items() if v == "on"]
            
            comp_instance = get_object_or_404(CompetitionDetail, id=comp_id)
            for pos_id in positive_ids:
                athlete_instances.append(get_object_or_404(Athlete, id=pos_id))

            ola = {f"athlete{i + 1}": athlete_instance for i, athlete_instance in enumerate(athlete_instances)}
            team_object = Team(**ola, dojo=request.user, match_type = match_type, competition=comp_instance, team_number=1)
            
            errors = check_teams_data(request.POST.dict(), team_object)
            

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
            new_team.competition = get_object_or_404(CompetitionDetail, id=comp_id)
            new_team.save()
            request.session['can_access_target_page'] = True
            request.session['team'] = True

            messages.success(request, f'Equipa de {match_type.capitalize()} {form.cleaned_data["category"].capitalize()} {form.cleaned_data["gender"].capitalize()} inscrita com sucesso!')

            if action == "save_back":
                return HttpResponseRedirect(f"/teams/{comp_id}")
            elif action == "save_add":
                return HttpResponseRedirect(f"/teams_form/{match_type}/{comp_id}")

    else:
        form = TeamCategorySelection()
        context = {"form": form, "title": "Inscriver Equipa", "match_type": match_type, "comp_id": comp_id}
        return render(request, 'registration/teams_form.html', context)


class TeamView(LoginRequiredMixin, View):
    template_name = 'registration/teams.html'
    paginate_by = 10

    def get(self, request, *args, **kwargs):

        comp_id = self.kwargs.get('comp_id')
        comp_detail = CompetitionDetail.objects.filter(id=comp_id).first()
        not_found = False
        filter_form = FilterTeamForm()
        teams = Team.objects.filter(dojo=request.user)
        paginator = Paginator(teams, self.paginate_by)
        page = request.GET.get('page')
        is_closed = datetime.date.today() > comp_detail.retifications_deadline and not comp_detail.has_ended

        try:
            teams_paginated = paginator.page(page)
        except PageNotAnInteger:
            teams_paginated = paginator.page(1)
        except EmptyPage:
            teams_paginated = paginator.page(paginator.num_pages)

        number_teams = len(teams)
        comp = get_object_or_404(CompetitionDetail, id=comp_id)
        context = {"teams": teams_paginated, 
                    "filters": filter_form, 
                    "not_found": not_found,
                    "comp": comp,
                    "number_teams": number_teams,
                    "is_closed": is_closed,
                    "title": "Equipas"}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        comp_id = self.kwargs.get('comp_id')
        not_found = False
        filter_form = FilterTeamForm(request.POST)
        if filter_form.is_valid():
            teams = Team.objects.filter(dojo=request.user)
            teams, not_found = check_filter_data(request, filter_form, teams)
        paginator = Paginator(teams, self.paginate_by)
        page = request.GET.get('page')

        try:
            teams_paginated = paginator.page(page)
        except PageNotAnInteger:
            teams_paginated = paginator.page(1)
        except EmptyPage:
            teams_paginated = paginator.page(paginator.num_pages)

        number_teams = len(teams)
        comp = get_object_or_404(CompetitionDetail, id=comp_id)
        context = {"teams": teams_paginated, 
                    "filters": filter_form, 
                    "not_found": not_found,
                    "comp": comp,
                    "number_teams": number_teams,
                    "title": "Equipas"}
        return render(request, self.template_name, context)


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
    return render(request, 'registration/comp_details.html', {"comp_detail": comp_detail,
                                                              "is_open": is_open,
                                                              "is_retification": is_retification,
                                                              "is_closed": is_closed})

@login_required
def previous_registration(request, comp_id):
    if not os.path.exists("archived_comps.json"):
        return render(request, "error/404.html")
    with open("archived_comps.json", "r") as file:
        json_data = json.loads(file.read())
    indiv_ids, teams = [], []
    for model, data in json_data.items():
        for entry in data:
            if entry["fields"]["competition"] == comp_id:
                if model == "individuals":
                    indiv_ids.append(entry["fields"]["athlete"])
                else:
                    team_athlete_ids = [value for field, value in entry["fields"].items() if field.startswith("athlete") and value is not None]
                    teams_athletes = Athlete.objects.filter(id__in=team_athlete_ids).order_by("match_type")
                    team_info = (f'{entry["fields"]["match_type"].capitalize()} {entry["fields"]["category"]} {entry["fields"]["gender"].capitalize()}', teams_athletes)
                    teams.append(team_info)
    athletes = Athlete.objects.filter(id__in=indiv_ids).order_by("first_name")
    return render(request, "registration/previous_registrations.html", {"individuals": athletes,
                                                                        "teams": teams})


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
                        return HttpResponseRedirect(f"/teams/{comp_id}")
            
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


def update(request, type, match_type, id, comp_id):
    if type == "athlete":
        athlete = get_object_or_404(Athlete, id=id)

        # Checks if there's another athlete in other match_type
        data = {field.name: getattr(athlete, field.name) for field in athlete._meta.get_fields() if hasattr(athlete, field.name) and field.name in ["first_name", "last_name", "graduation", "birth_date", "age", "skip_number", "category", "gender"]}
        data["match_type"] = "kumite" if match_type == "kata" else "kata"

        try:
            other_match = Athlete.objects.filter(**data).first()
        except Exception:
            print("This athlete is unique")

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

                if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], 
                                          birth_date=birth_date, 
                                          match_type=form.cleaned_data.get("match_type")).exists():
                    athlete_test = Athlete.objects.filter(first_name=form.cleaned_data["first_name"], 
                                                          birth_date=birth_date, 
                                                          match_type=form.cleaned_data.get("match_type")).first()
                    if athlete_test.id != athlete.id:
                        errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se quer inscrever a mesma pessoa noutra prova")
                    else:
                        errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
                else:
                    errors = check_athlete_data(form, age_at_comp, age_graduation_rules, age_category_rules)
        else:
            message = f'Informação da equipa nº {team.team_number} atualizada!'
            form = TeamForm(request.POST, instance=team)
            if form.is_valid():
                errors = check_teams_data(form)

        # Check for occured errors
        if len(errors) > 0:
            messages.error(request, "Não foi possível atualizar")
            for error in errors:
                messages.error(request, error)
            return HttpResponseRedirect(f"/update_registration/{type}/{match_type}/{id}/{comp_id}")
        
        # If no erros, proceed
        else:
            if type == "athlete":
                new_athlete = form.save(commit=False) 
                new_athlete.dojo = request.user
                new_athlete.age = age_at_comp
                new_athlete.save()
                messages.success(request, message)

                # If another athlete in other match_type, change it too
                if other_match:
                    form = AthleteForm(request.POST, instance=other_match)
                    new_athlete = form.save(commit=False) 
                    new_athlete.dojo = request.user
                    new_athlete.age = age_at_comp
                    new_athlete.save()
                    messages.success(request, "Outr@ atleta com a mesma informação mas de outra prova encontrad@ e atualizad@!")
                
            else:
                teams = Team.objects.filter(dojo=request.user,
                                         category=form.cleaned_data["category"], 
                                         match_type=match_type,
                                         gender=form.cleaned_data["gender"])
                new_team = form.save(commit=False)
                new_team.dojo = request.user
                new_team.match_type = match_type
                new_team.team_number = len(teams) + 1
                new_team.save()
            return HttpResponseRedirect("/athletes/") if type == "athlete" else HttpResponseRedirect(f"/teams/{comp_id}")
    else:
        form = AthleteForm(instance=athlete) if type == "athlete" else TeamForm(instance=team)
        if match_type == "kata":
            del form.fields['weight']
        return render(request, 'registration/update_registration.html', {"form": form, 
                                                                         "type": type, 
                                                                         "match_type": match_type,
                                                                         "id": id,
                                                                         "comp_id": comp_id,
                                                                         "title": "Atualizar Atleta" if type == "athlete" else "Atualizar Equipa"})