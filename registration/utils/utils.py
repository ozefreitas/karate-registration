from datetime import datetime
from django.contrib import messages
import requests
from collections import Counter

def range_decoder(some_range: str):
    """Function that returns a range 

    Args:
        some_range (list): _description_

    Returns:
        range object: The range from the given range
    """
    some_range = some_range.split("-")
    some_range = range(int(some_range[0]), int(some_range[1]) + 1)
    return some_range


def check_match_type(response: requests) -> tuple:
    """Function that checks the checboxes for the match type selection

    Args:
        response (_type_): _description_

    Returns:
        tuple: A list containing the selected match types
    """
    matches_list= []
    error = ""
    if response.POST.dict().get("match_type_kata", 0) == 0 and response.POST.dict().get("match_type_kumite", 0) == 0:
        error = "Tem de selecionar pelo menos 1 prova"
    else:
        if response.POST.dict().get("match_type_kata", 0) == "on":
            matches_list.append("kata")
        if response.POST.dict().get("match_type_kumite", 0) == "on":
            matches_list.append("kumite")
    return matches_list, error


def get_comp_age(date_of_birth: datetime) -> int:
    """Function that return the age of an athlete by the begining of the year

    Args:
        date_of_birth (datetime): The birth date of the athlete. Must be an instance of datetime 

    Returns:
        int: The age as an int
    """
    year_of_birth = date_of_birth.year
    date_now = datetime.now()
    age_at_comp = (date_now.year) - year_of_birth
    return age_at_comp - 1
    ### methodology to date of birth as reference
    # if (date_now.month, date_now.day) < (date_of_birth.month, date_of_birth.day):
    #     age_at_comp -= 1
    # return age_at_comp


def check_athlete_data(data, age_at_comp: int, grad_rules: dict, category_rules: dict, extra_data = None) -> list:
    """Receives the form from the view, processes the data to check any error or rules infrigements 

    Args:
        data (form): The form data
        age_at_comp (int): _description_
        grad_rules (dict): _description_
        category_rules (dict): _description_
        extra_data (_type_, optional): _description_. Defaults to None.

    Returns:
        list: _description_
    """
    errors = []
    if " A " in data.cleaned_data["category"]:
        if float(data.cleaned_data["graduation"]) < grad_rules[data.cleaned_data["category"]]:
            errors.append("Graduação máxima não respeitada")
    else:
        if float(data.cleaned_data["graduation"]) > grad_rules[data.cleaned_data["category"]]:
            errors.append("Graduação minima não respeitada")

    possible_cats = []
    for cat, age_range in category_rules.items():
        if age_at_comp in range_decoder(age_range):
            possible_cats.append(cat)
    if data.cleaned_data["category"] not in possible_cats:
        errors.append("Idade do atleta não corresponde à categoria selecionada")

    if data.cleaned_data["category"] in ["Benjamins (n/SKIP)", "Infantil A (7 8 9) (n/SKIP)"] and data.cleaned_data["gender"] != "misto":
        errors.append("Categorias de Benjamins e Infantil A não se dividem em género")

    if extra_data is not None:
        if "(n/SKIP)" in data.cleaned_data["category"]:
            if "kumite" in extra_data and data.cleaned_data["weight"] is not None:
                errors.append("Os escalões não SKIP não são dividos por pesos")
        
        else:
            if "kumite" in extra_data and (data.cleaned_data["category"].startswith("Benjamins") or data.cleaned_data["category"].startswith("Infantil") or data.cleaned_data["category"].startswith("Iniciado")):
                errors.append("Não existe prova de Kumite para esse escalão")
            
            elif "kumite" in extra_data and data.cleaned_data["weight"] is None and data.cleaned_data["gender"] == "masculino":
                errors.append("Por favor selecione um peso")

            elif "kumite" in extra_data and data.cleaned_data["weight"] is not None and data.cleaned_data["gender"] == "feminino":
                errors.append("Os escalões femininos não são dividos por pesos")

    return errors


def check_team_selection(data) -> list:
    team_cat = data.cleaned_data.get("category", 0)
    team_gender = data.cleaned_data.get("gender", 0)
    # check for wrong gender
    if team_cat in ["Iniciado", "Infantil"] and team_gender != "misto":
        return ["Categorias de Infantil e Iniciado não se dividem em género"]


def check_teams_data(data: dict, match_type: str, athletes_list: list = None) -> list:
    """Receives the form from the view, processes the data to check any error or rules infrigements 

    Args:
        data (form): The form data

    Returns:
        list: A list of the errors that occured
    """
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

    errors = []
    category_up = 0
    team_cat = data.get("category", 0)
    team_gender = data.get("gender", 0)

    if match_type == "kumite" and len(athletes_list) > 2:
        errors.append(f"Kumite Equipa {team_cat} tem um máximo de 2 atletas")

    if team_gender != "misto" and match_type == "kata" and len(athletes_list) != 3:
        errors.append("Provas de Kata Equipa tem de ter 3 atletas")

    if team_gender != "misto" and match_type == "kumite" and len(athletes_list) < 3:
        errors.append("Provas de Kumite Equipa tem de ter pelo menos 3 atletas")

    for athlete in athletes_list:
        # check for category jumps

        if athlete.category != team_cat and CATEGORY_RULES[team_cat] == athlete.category:
            category_up += 1
        if category_up > 1:
            errors.append("Não pode haver mais do que um atleta a subir de escalão")
        
    return errors


def check_filter_data(request, filter_form, dojo_object):
    not_found = False
    if filter_form.cleaned_data["filter"] != None and filter_form.cleaned_data["search"] == None:
        messages.error(request, 'Adicione um termo de procura em "Procurar')
    elif filter_form.cleaned_data["filter"] == None and filter_form.cleaned_data["search"] != None:
        messages.error(request, 'Selecione o campo que quer procurar em "Filtrar por"')
    elif filter_form.cleaned_data["filter"] != None and filter_form.cleaned_data["order"] != None and filter_form.cleaned_data["search"] != None:
        filter_kwargs = {f'{filter_form.cleaned_data["filter"]}__icontains': filter_form.cleaned_data["search"]}
        dojo_object = dojo_object.filter(**filter_kwargs).order_by(filter_form.cleaned_data["order"])
        if len(dojo_object) == 0:
            not_found = True
    elif filter_form.cleaned_data["order"] != None:
        dojo_object = dojo_object.order_by(filter_form.cleaned_data["order"])
    elif filter_form.cleaned_data["filter"] != None and filter_form.cleaned_data["search"] != None:
        filter_kwargs = {f'{filter_form.cleaned_data["filter"]}__icontains': filter_form.cleaned_data["search"]}
        dojo_object = dojo_object.filter(**filter_kwargs)
        if len(dojo_object) == 0:
            not_found = True
    return dojo_object, not_found