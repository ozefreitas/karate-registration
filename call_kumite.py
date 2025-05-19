import os
import json
from django.core.serializers.json import DjangoJSONEncoder
import django
from django.contrib.auth import get_user_model
import os
import pandas as pd


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "karate_registration.settings")
django.setup()

try:
    # Import Users (Created Dojo Accounts)
    new_users = []
    User = get_user_model()
    users = User.objects.values()
    for user in users:
        new_user = {}
        for key, value in user.items():
            if key in ["id", "username"]:
                new_user[key] = value
        new_users.append(new_user)

    from registration.models import Athlete, Individual

    interest_keys = ["name", "category", "gender", "weight"]
    
    individuals = list(Individual.objects.all().values())
    
    athletes = list(Athlete.objects.all().values())
    athletes_by_id = {}
    for athlete in athletes:
        athletes_by_id[athlete["id"]] = athlete

    new_athletes = [indiv for indiv in individuals if athletes_by_id[indiv["athlete_id"]]["match_type"] == "kumite" and athletes_by_id[indiv["athlete_id"]]["gender"] != "feminino"]

    kumite_athletes = []
    for athlete in new_athletes:
        current_individual = athletes_by_id[athlete["athlete_id"]]
        new_athlete = {}
        for key, value in current_individual.items():
            if key == "dojo_id":
                for user in new_users:
                    if user["id"] == value:
                        new_athlete["team"] = user["username"]
        new_athlete["name"] = current_individual["first_name"] + " " + current_individual["last_name"]
        if current_individual["weight"] != "open":
            new_athlete["category"] = current_individual["category"] + " " + current_individual["gender"].capitalize() + " " + current_individual["weight"] + "Kg"
        else:
            new_athlete["category"] = current_individual["category"] + " " + current_individual["gender"].capitalize() + " " + "Open"
        kumite_athletes.append(new_athlete)


    sorted_data = sorted(kumite_athletes, key=lambda x: (x["team"], x["name"]))
    
    for i, item in enumerate(sorted_data, start=1):
        item["number"] = str(i).zfill(3)

    # serialize to JSON
    json_athletes = json.dumps(sorted_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=4)

    # Save to a JSON file
    with open("kumite_call.json", "w", encoding="utf-8") as f:
        f.write(json_athletes)

    # Save to a CSV file
    with open("kumite_call.json", encoding='utf-8') as inputfile:
        df = pd.read_json(inputfile)
    df.to_csv('kumite_call.csv', encoding='utf-8', index=False)

except Exception as exc:
    # Running the echo command
    os.system(f'echo The following problem occoured: {exc}')

else:
    os.system('echo Athletes data processed and JSON created!')