from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .forms import AthleteForm, FilterForm
from datetime import datetime
from django.contrib import messages
from .utils.utils import range_decoder
from .models import Athlete

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
    "0-9": "infantil",
    "10-11": "iniciado",
    "12-13": "juvenil",
    "14-15": "cadete",
    "16-17": "junior",
    "18-34": "senior",
    # "35-49": "Veterano +35",
    # "50-99": "Veterano +50"
}

errors = []

@login_required()
def form(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AthleteForm(request.POST)
        print(request.POST)
        errors = []
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            birth_date = form.cleaned_data["birth_date"]
            year_of_birth = birth_date.year
            date_now = datetime.now()
            age_at_comp = (date_now.year) - year_of_birth

            if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date, match_type=form.cleaned_data.get("match_type")).exists():
                errors.append("Um atleta com as mesmas credenciais já está inscrito. Verifique se a quer inscrever a mesma pessoa noutra prova")

            else:
                for age_range, grad in age_graduation_rules.items():
                    age_range = range_decoder(age_range)
                    if age_at_comp in age_range and int(form.cleaned_data["graduation"]) > grad:
                        errors.append("Atleta não dispõe da graduação mínima para a idade")
                
                for age_range, cat in age_category_rules.items():
                    age_range = range_decoder(age_range)
                    if age_at_comp in age_range and form.cleaned_data["category"] != cat:
                        errors.append("Idade do atleta não corresponde à categoria selecionada")
                
                if form.cleaned_data["match_type"] == "kumite" and form.cleaned_data["category"] in ["infantil", "iniciado"]:
                    errors.append("Não existe prova de Kumite para esse escalão")
                
                if form.cleaned_data["match_type"] == "kumite" and form.cleaned_data["weight"] is None and form.cleaned_data["gender"] == "masculino":
                    errors.append("Por favor selecione um peso")
            
            if len(errors) != 0:
                for error in errors:
                    messages.error(request, error)
                return HttpResponseRedirect("/wrong")
            
            new_athlete = form.save(commit=False) 
            new_athlete.dojo = request.user
            new_athlete.save()
            # redirect to a new URL:
            return HttpResponseRedirect("/thanks/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AthleteForm()
        context = {"form": form, "title": "Inscrições"}
        return render(request, 'registration/form.html', context)

@login_required()
def home(request):
    not_fount = False
    if request.method == "POST":
        filter_form = FilterForm(request.POST)
        if filter_form.is_valid():
            athletes = Athlete.objects.filter(dojo=request.user)
            if filter_form.cleaned_data["order"] != None:
                athletes = athletes.order_by(filter_form.cleaned_data["order"])
            elif filter_form.cleaned_data["filter"] != None and filter_form.cleaned_data["search"] != None:
                filter_kwargs = {f"{filter_form.cleaned_data["filter"]}": filter_form.cleaned_data["search"]}
                athletes = athletes.filter(**filter_kwargs)
                if len(athletes) == 0:
                    not_fount = True
    else:
        filter_form = FilterForm()
        athletes = Athlete.objects.filter(dojo=request.user)
    return render(request, 'registration/home.html', {"athletes": athletes, "filters": filter_form, "not_found": not_fount})

def help(request):
    return render(request, 'registration/help.html')

def thanks(request):
    return render(request, "registration/thanks.html")

def wrong(request):
    context = {"errors": errors}
    return render(request, "registration/wrong.html", context)

def delete(request, athlete_id):
    if request.method == "POST":
        athlete = get_object_or_404(Athlete, id=athlete_id)
        athlete.delete()
        athletes = Athlete.objects.filter(dojo=request.user)
        return render(request, 'registration/home.html', {"athlets": athletes})
    
def update(request, athlete_id):
    athlete = get_object_or_404(Athlete, id=athlete_id)
    if request.method == "POST":
        form = AthleteForm(request.POST, instance=athlete)
        if form.is_valid():
            new_athlete = form.save(commit=False) 
            new_athlete.dojo = request.user
            new_athlete.save()
            # add one time message indicating a successful update
            return HttpResponseRedirect("/")
    else:
        form = AthleteForm(instance=athlete)
        # athletes = Athlete.objects.filter(dojo=request.user)
        return render(request, 'registration/update_registration.html', {"form": form, "athlete_id": athlete_id})