from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import AthleteForm
from datetime import datetime
from django.contrib import messages
from .utils.utils import range_decoder
from .models import Athlete

age_graduation_rules = {
    "0-9": 9,
    "10-11": 9,
    "12-13": 8,
    "14-15": 7,
    "16-17": 6,
    "18-50": 5
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

            if Athlete.objects.filter(first_name=form.cleaned_data["first_name"], birth_date=birth_date).exists():
                errors.append("Um atleta com as mesmas credenciais já está inscrito")

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
            
            if len(errors) != 0:
                for error in errors:
                    messages.error(request, error)
                return HttpResponseRedirect("/wrong")
            
            newpost = form.save(commit=False) 
            newpost.save()
            # redirect to a new URL:
            return HttpResponseRedirect("/thanks/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AthleteForm()
        context = {"form": form, "title": "Inscrições"}
        return render(request, 'registration/form.html', context)
    
def home(request):
    return render(request, 'registration/home.html')

def help(request):
    return render(request, 'registration/help.html')

def thanks(request):
    return render(request, "registration/thanks.html")

def wrong(request):
    context = {"errors": errors}
    return render(request, "registration/wrong.html", context)