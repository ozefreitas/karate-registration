from datetime import datetime
from django.contrib import messages
import requests
from collections import Counter

def range_decoder(some_range: list):
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
    for age_range, grad in grad_rules.items():
        age_range = range_decoder(age_range)
        if age_at_comp in age_range and float(data.cleaned_data["graduation"]) > grad:
            errors.append("Atleta não dispõe da graduação mínima para a idade")
    
    for age_range, cat in category_rules.items():
        age_range = range_decoder(age_range)
        if age_at_comp in age_range and data.cleaned_data["category"] != cat:
            errors.append("Idade do atleta não corresponde à categoria selecionada")

    if extra_data is not None:
        if "kumite" in extra_data and data.cleaned_data["category"] in ["infantil", "iniciado"]:
            errors.append("Não existe prova de Kumite para esse escalão")
        
        if "kumite" in extra_data and data.cleaned_data["weight"] is None and data.cleaned_data["gender"] == "masculino":
            errors.append("Por favor selecione um peso")

        if "kumite" in extra_data and data.cleaned_data["weight"] is not None and data.cleaned_data["gender"] == "feminino":
            errors.append("Os escalões femininos não são dividos por pesos")

    return errors


def check_teams_data(data) -> list:
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

    athletes_set = [value for key, value in data.cleaned_data.items() if key.startswith("athlete") and value is not None]
    athlete_ids = Counter([athlete.id for athlete in athletes_set])
    for number_ids in athlete_ids.values():
        if number_ids > 1:
            return ["Pelo menos um dos atletas está repetido"]
    errors = []
    category_up = 0
    team_cat = data.cleaned_data.get("category", 0)
    team_gender = data.cleaned_data.get("gender", 0)
    for athlete in athletes_set:
        # check for category jumps
        if athlete.category != team_cat and CATEGORY_RULES[team_cat] != athlete.category:
            errors.append(f"{athlete.first_name} {athlete.last_name} não pode participar nesta prova")

        # check for wrong gender
        if team_cat in ["Iniciado", "Infantil"] and athlete.gender != "misto":
            return ["Categorias de Infantil e Iniciado não se dividem em género"]

        if team_cat not in ["Iniciado", "Infantil"] and athlete.gender == "misto":
            return ["Categorias acima de Iniciado não são mistas"]

        if team_cat not in ["Iniciado", "Infantil"] and athlete.gender != team_gender:
            return [f"Géneros não coincidem: {athlete.first_name} {athlete.last_name}"]

        if athlete.category != team_cat and CATEGORY_RULES[team_cat] == athlete.category:
            category_up += 1
        if category_up > 1:
            errors.append("Não pode ter mais do que um atleta a subir de escalão")
        
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