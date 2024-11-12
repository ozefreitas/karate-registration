from django.shortcuts import render
from django.http import HttpResponse
from .forms import AthleteForm

def home(request):
    form = AthleteForm()
    context = {"form": form}
    return render(request, 'registration/home.html', context)

def help(request):
    return render(request, 'registration/help.html')