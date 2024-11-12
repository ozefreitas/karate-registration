from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import AthleteForm
from datetime import datetime

def home(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = AthleteForm(request.POST)
        print(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            birth_date = form.cleaned_data["birth_date"]
            date_now = datetime.now()
            newpost = form.save(commit=False) 
            newpost.save()
            # redirect to a new URL:
            return HttpResponseRedirect("/thanks/")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AthleteForm()
        context = {"form": form}
        return render(request, 'registration/home.html', context)

def help(request):
    return render(request, 'registration/help.html')

def thanks(request):
    return render(request, "registration/thanks.html")