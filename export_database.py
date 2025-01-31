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

    interest_keys = ["id", "first_name", "last_name", "category", "match_type", "gender", "weight"]
    athletes = list(Athlete.objects.all().values())

    # format database info into Karate Score App ready format for draws
    new_athletes = []

    for athlete in athletes:
        new_athlete = {}
        for key, value in athlete.items():
            if key == "dojo_id":
                for user in new_users:
                    if user["id"] == value:
                        new_athlete["team"] = user["username"]
        new_athlete["name"] = athlete["first_name"] + " " + athlete["last_name"]
        new_athlete["category"] = athlete["category"] + " " + athlete["gender"].capitalize()
        if athlete["weight"] is not None:
            new_athlete["category"] = new_athlete["category"] + " " + athlete["weight"] + "Kg"
        new_athlete["type"] = athlete["match_type"].capitalize()
        new_athlete["favorite"] = "NO"
        new_athletes.append(new_athlete)

    # sort by team name
    sorted_data = sorted(new_athletes, key=lambda x: x["team"])

    # add the number key with 3 filling characters as string
    for i, item in enumerate(sorted_data, start=1):  # Start enumeration at 1
        item["number"] = str(i).zfill(3)

    # serialize to JSON
    json_athletes = json.dumps(sorted_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=4)

    # Save to a JSON file
    with open("athlete_data.json", "w", encoding="utf-8") as f:
        f.write(json_athletes)

    # Save to a CSV file
    with open("athlete_data.json", encoding='utf-8') as inputfile:
        df = pd.read_json(inputfile)
    df.to_csv('registrations.csv', encoding='utf-8', index=False)

except Exception as exc:
    # Running the echo command
    os.system(f'echo The following problem occoured: {exc}')

else:
    os.system('echo Athletes data processed and JSON created!')