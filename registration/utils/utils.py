from datetime import datetime
from django.contrib import messages

def range_decoder(some_range: str):
    some_range = some_range.split("-")
    some_range = range(int(some_range[0]), int(some_range[1]) + 1)
    return some_range

def get_comp_age(date_of_birth):
    year_of_birth = date_of_birth.year
    date_now = datetime.now()
    age_at_comp = (date_now.year) - year_of_birth
    return age_at_comp

def check_athlete_data(data, age_at_comp, grad_rules, category_rules):
    errors = []
    for age_range, grad in grad_rules.items():
        age_range = range_decoder(age_range)
        if age_at_comp in age_range and float(data.cleaned_data["graduation"]) > grad:
            errors.append("Atleta não dispõe da graduação mínima para a idade")
    
    for age_range, cat in category_rules.items():
        age_range = range_decoder(age_range)
        if age_at_comp in age_range and data.cleaned_data["category"] != cat:
            errors.append("Idade do atleta não corresponde à categoria selecionada")
    
    if data.cleaned_data["match_type"] == "kumite" and data.cleaned_data["category"] in ["infantil", "iniciado"]:
        errors.append("Não existe prova de Kumite para esse escalão")
    
    if data.cleaned_data["match_type"] == "kumite" and data.cleaned_data["weight"] is None and data.cleaned_data["gender"] == "masculino":
        errors.append("Por favor selecione um peso")

    if data.cleaned_data["match_type"] == "kumite" and data.cleaned_data["weight"] is not None and data.cleaned_data["gender"] == "feminino":
        errors.append("Os escalões femininos não são dividos por pesos")

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