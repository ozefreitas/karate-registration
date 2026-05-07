import json

GENDER_MAP = {
    "feminino": "Feminino",
    "masculino": "Masculino",
    "misto": "Misto"
}

def transform(old_data):
    new_data = []

    seen = set() 

    for obj in old_data:
        fields = obj["fields"]
        key = (fields["first_name"].strip().lower(),
               fields["last_name"].strip().lower(),
               fields["dojo"])

        if key in seen:
            continue  # skip duplicate
        seen.add(key)

        new_obj = {
            "model": "registration.athlete",  # keep same app_label.model
            "pk": obj["pk"],  # id is primary key
            "fields": {
                "first_name": fields["first_name"],
                "last_name": fields["last_name"],
                "graduation": fields["graduation"],
                "birth_date": fields["birth_date"],
                "id_number": fields["skip_number"],
                "competitor": not fields["is_just_student"],
                "favorite": False,
                "gender": GENDER_MAP[fields["gender"]],
                "weight": abs(int(fields["weight"])) if fields["weight"] is not None and fields["weight"] != "open" and fields["weight"] != "" else None,
                "club": fields["dojo"],  # must exist as User pk
                "creation_date": fields["creation_date"],
            },
        }

        new_data.append(new_obj)

    return new_data


if __name__ == "__main__":
    with open("athletes_backup.json", "r", encoding="utf-8") as f:
        old_data = json.load(f)

    new_data = transform(old_data)

    with open("converted_athletes.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print("✅ new_athletes.json created")