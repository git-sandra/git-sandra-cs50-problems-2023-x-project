import requests
import json


def get_statistic_data(field, expression="", type="field_values", format="json"):
    url = (
        f"https://classic.clinicaltrials.gov/api/query/{type}"
        f"?expr={expression}"
        f"&field={field}"
        f"&fmt={format}"
    )

    response = requests.get(url)
    return response.json()


def get_study_data(type, field="", expression="", format="json", min_rnk=1, max_rnk=1):
    url = (
        f"https://classic.clinicaltrials.gov/api/query/{type}"
        f"?expr={expression}"
        f"&fields={field}"
        f"&min_rnk={min_rnk}"
        f"&max_rnk={max_rnk}"
        f"&fmt={format}"
    )

    response = requests.get(url)
    return response.json()

def check_blanks(form):
    for input in range(len(form) -1, -1, -1):
        if (form[input])["value"] == "":
            form.remove(form[input])
    return form


def validate_form(form):
    special_characters = "[@_!#$%^&*()<>?/|}{~:.]"

    for input in form:
        for char in input["value"]:
            if char.isnumeric() or char in special_characters:
                input["is_error"] = "yes"
                break
    return form


def prepare_form(form):
    for input in form:
        value = input["value"].strip().lower()
        input["value"] = value
    return form













