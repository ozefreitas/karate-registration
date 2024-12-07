from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import DojoRegisterForm, FeedbackForm
from .models import Profile
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
        return render(request, 'dojos/register_user.html', {"form": form})
    

def logout_user(request):
    logout(request)
    return render(request, "dojos/logout.html")

@login_required
def profile(request):
    return render(request, 'dojos/profile.html')

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
        return render(request, 'dojos/feedback.html', {"form": form})