import os
import json
from django.core.serializers.json import DjangoJSONEncoder
from karate_registration import settings
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

    from registration.models import Athlete

    interest_keys = ["name", "category", "gender", "weight"]
    
    athletes = list(Athlete.objects.all().values())

    new_athletes = [athlete for athlete in athletes if athlete["match_type"] == "kumite" and athlete["gender"] != "feminino"]

    kumite_athletes = []
    for athlete in new_athletes:
        new_athlete = {}
        for key, value in athlete.items():
            if key == "dojo_id":
                for user in new_users:
                    if user["id"] == value:
                        new_athlete["team"] = user["username"]
        new_athlete["name"] = athlete["first_name"] + " " + athlete["last_name"]
        new_athlete["category"] = athlete["category"] + " " + athlete["gender"].capitalize() + " " + athlete["weight"] + "Kg"
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