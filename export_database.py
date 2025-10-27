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


    from registration.models import Athlete, Team

    # event = CompetitionDetail.objects.filter(name="Torneio Shihan Mário Águas").first()

    # interest_keys = ["id", "first_name", "last_name", "category", "match_type", "gender", "weight", "skip_number"]
    # individuals = list(Individual.objects.filter(competition=event).values())


    # athletes = list(Athlete.objects.all().values())
    # athletes_by_id = {}
    # for athlete in athletes:
    #     athletes_by_id[athlete["id"]] = athlete

    # # format database info into Karate Score App ready format for draws
    # new_individuals = []

    # for individual in individuals:
    #     current_individual = athletes_by_id[individual["athlete_id"]]
    #     new_athlete = {}
    #     for key, value in individual.items():
    #         if key == "dojo_id":
    #             for user in new_users:
    #                 if user["id"] == value:
    #                     new_athlete["team"] = user["username"]
    #     new_athlete["name"] = current_individual["first_name"] + " " + current_individual["last_name"]
    #     new_athlete["category"] = current_individual["category"] + " " + current_individual["gender"].capitalize()
    #     if current_individual["match_type"] != "kata" and current_individual["weight"] is not None and current_individual["weight"] != "":
    #         if current_individual["weight"] != "open":
    #             new_athlete["category"] = new_athlete["category"] + " " + current_individual["weight"] + "Kg"
    #         else:
    #             new_athlete["category"] = new_athlete["category"] + " " + "Open"
    #     new_athlete["type"] = current_individual["match_type"].capitalize()
    #     new_athlete["favorite"] = "NO"
    #     try:
    #         new_athlete["skip_number"] = int(round(current_individual["skip_number"]))
    #     except:
    #         new_athlete["skip_number"] = ""
    #     new_individuals.append(new_athlete)

    # # sort by dojo name, and then name of the member
    # sorted_data = sorted(new_individuals, key=lambda x: (x["team"], x["name"]))

    # # add the number key with 3 filling characters as string
    # name = ""
    # dojo = ""
    # i = 0
    # for item in sorted_data:
    #     if name == item["name"] and dojo == item["team"]:
    #         item["number"] = str(i).zfill(3)
    #     else:
    #         i += 1
    #         item["number"] = str(i).zfill(3)
    #         name = item["name"]
    #         dojo = item["team"]

    athletes = list(Athlete.objects.all().values())
    athletes_by_id = {}
    for athlete in athletes:
        athletes_by_id[athlete["id"]] = athlete

    # teams processing
    teams = list(Team.objects.all().values())

    new_teams = []
    for team in teams:
        
        new_team = {}
        for key, value in team.items():
            if key == "dojo_id":
                for user in new_users:
                    if user["id"] == value:
                        new_team["dojo"] = user["username"]


        new_team["category"] = team["category"] + " " + team["gender"].capitalize()
        new_team["type"] = team["match_type"].capitalize()
        new_team["favorite"] = "NO"
        
        for k, v in team.items():
            if k in ["athlete1_id", "athlete2_id", "athlete3_id"]:
                current_athlete = athletes_by_id[team[k]]
                new_team[k] = current_athlete["first_name"] + " " + current_athlete["last_name"]

        new_teams.append(new_team)

    # sort by dojo name
    team_sorted_data = sorted(new_teams, key=lambda x: (x["dojo"], x["category"]))

    # # serialize to JSON
    # json_athletes = json.dumps(sorted_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=4)
    json_teams = json.dumps(team_sorted_data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=4)

    # # Save to a JSON file
    # with open("athlete_data.json", "w", encoding="utf-8") as f:
    #     f.write(json_athletes)
    with open("team_data.json", "w", encoding="utf-8") as f:
        f.write(json_teams)

    # # Save to a CSV file
    # with open("athlete_data.json", encoding='utf-8') as inputfile:
    #     df = pd.read_json(inputfile)
    # df.to_csv('registrations.csv', encoding='utf-8', index=False)
    with open("team_data.json", encoding='utf-8') as inputfile:
        df = pd.read_json(inputfile)
    df.to_csv('teams_registrations.csv', encoding='utf-8', index=False)

except Exception as exc:
    # Running the echo command
    os.system(f'echo The following problem occoured: {exc}')

else:
    os.system('echo Athletes data processed and JSON created!')