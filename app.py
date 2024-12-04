from flask import Flask, redirect, render_template, request
from helpers import get_statistic_data, get_study_data, check_blanks, validate_form, prepare_form
import itertools

app = Flask(__name__)

@app.route("/")
def home():
    raw_study_data = get_study_data("study_fields")
    study_data = raw_study_data.get("StudyFieldsResponse", {})

    number_of_studies = study_data["NStudiesAvail"]
    last_update_date = ((study_data["DataVrs"])[:11]).replace(":", "/")

    return render_template("home.html", number_of_studies=number_of_studies, last_update_date=last_update_date)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/phases")
def phases():
    raw_data = get_statistic_data("Phase")
    data = raw_data.get("FieldValuesResponse", {})

    labels = []
    values = []

    for dict in data["FieldValues"]:
        labels.append(dict["FieldValue"])
        values.append(dict["NStudiesFoundWithValue"])

    return render_template("phases.html", labels=labels, values=values)


@app.route("/types")
def types():
    raw_data = get_statistic_data("StudyType")
    data = raw_data.get("FieldValuesResponse", {})

    labels = []
    values = []

    for dict in data["FieldValues"]:
        labels.append(dict["FieldValue"])
        values.append(dict["NStudiesFoundWithValue"])
    return render_template("types.html", labels=labels, values=values)


@app.route("/locations")
def locations():
    raw_data = get_statistic_data("LocationCountry")
    data = raw_data.get("FieldValuesResponse", {})

    locations = {}
    labels = []
    values = []
    other_countries = 0

    for location in data["FieldValues"]:
        locations[location["FieldValue"]] = location["NStudiesFoundWithValue"]
    sorted_locations = sorted(locations.items(), key = lambda x:x[1], reverse = True)

    for key, value in itertools.islice(sorted_locations, 20):
        labels.append(key)
        values.append(value)

    for key, value in sorted_locations[21:]:
        other_countries += value


    return render_template("locations.html", labels=labels, values=values, other_countries=other_countries)


@app.route("/years")
def years():
    raw_data = get_statistic_data("StartDate")
    data = raw_data.get("FieldValuesResponse", {})

    estimated_studies = 0
    previous_studies = 0
    years = {}
    labels = []
    values = []

    for dict in data["FieldValues"]:
        year = int((dict["FieldValue"])[-4:])
        if year > 2023:
            estimated_studies += 1
            continue

        if year in years:
            years[year] += dict["NStudiesFoundWithValue"]
        else:
            years[year] = 1

    first_study = (list(years.keys()))[0]

    years_keys = list(years.keys())
    years_values = list(years.values())
    labels = (years_keys)[-24:]
    values = (years_values)[-24:]

    for value in (years_values[:-24]):
        previous_studies += value

    return render_template("years.html", labels=labels, values=values, first_study=first_study, estimated_studies=estimated_studies, previous_studies=previous_studies)


@app.route("/intervention")
def intervention():
    raw_data = get_statistic_data("InterventionType")
    data = raw_data.get("FieldValuesResponse", {})

    labels = []
    values = []

    for dict in data["FieldValues"]:
        labels.append(dict["FieldValue"])
        values.append(dict["NStudiesFoundWithValue"])

    return render_template("interventions.html", labels=labels, values=values)


@app.route("/status")
def status():
    raw_data = get_statistic_data("LocationStatus")
    data = raw_data.get("FieldValuesResponse", {})

    labels = []
    values = []

    for dict in data["FieldValues"]:
        labels.append(dict["FieldValue"])
        values.append(dict["NStudiesFoundWithValue"])

    return render_template("status.html", labels=labels, values=values)


@app.route("/explore", methods=["GET", "POST"])
def explore():
    if request.method == "POST":

        form_data = [
            {
                "name" : "condition",
                "area" : "Condition"
            },
            {
                "name" : "sponsor",
                "area" : "OrgFullName"
            },
            {
                "name" :"country",
                "area" : "LocationCountry"
            },
            {
                "name" : "intervention",
                "area" : "InterventionName"
            }
        ]

        user_values = []
        for input in form_data:
            input["value"] = request.form.get(input["name"])
            user_values.append(input["value"])
            input["is_error"] = "no"

        condition_value = user_values[0]
        sponsor_value = user_values[1]
        country_value = user_values[2]
        intervention_value = user_values[3]

        checked_form = check_blanks(form_data)

        if len(checked_form) == 0:
            return render_template("explore.html", message = "Provide at least one input.")

        validated_form = validate_form(checked_form)

        errors = []
        for input in validated_form:
            if input["is_error"] != "no":
                errors.append(input["name"])

        if len(errors) > 1:
            message = f"Incorrect {', '.join(errors[:-1])} and {errors[-1]} format."
            return render_template("explore.html",
                                    message = message,
                                    condition_value = condition_value,
                                    sponsor_value = sponsor_value,
                                    country_value = country_value,
                                    intervention_value = intervention_value)
        elif len(errors) == 1:
            message = f"Incorrect {errors[0]} format."
            return render_template("explore.html",
                                    message = message,
                                    condition_value = condition_value,
                                    sponsor_value = sponsor_value,
                                    country_value = country_value,
                                    intervention_value = intervention_value)

        prepared_form = prepare_form(validated_form)

        areas = []
        for input in prepared_form:
            area = input["area"]
            value = input["value"]
            areas.append(f"AREA%5B{area}%5D{value}")

        expression = "+AND+".join(areas)

        api_fields = ["Phase", "StudyType", "LocationStatus", "StdAge"]

        labels_and_values = {}
        for field in api_fields:
            labels_and_values[f"{field}_labels"] = []
            labels_and_values[f"{field}_values"] = []


        for field in api_fields:
            raw_data = get_statistic_data(field, expression)
            data = raw_data.get("FieldValuesResponse", {})

            if data["NStudiesFound"] == 0:
                message = "Keys not found. Try again."
                return render_template("explore.html",
                                message = message,
                                condition_value = condition_value,
                                sponsor_value = sponsor_value,
                                country_value = country_value,
                                intervention_value = intervention_value)

            for dict in data["FieldValues"]:
                labels_and_values[f"{field}_labels"].append(dict["FieldValue"])
                labels_and_values[f"{field}_values"].append(dict["NStudiesFoundWithValue"])

        return render_template("explore.html",
                               condition_value = condition_value,
                               sponsor_value = sponsor_value,
                               country_value = country_value,
                               intervention_value = intervention_value,
                               phase_labels=labels_and_values["Phase_labels"],
                               phase_values=labels_and_values["Phase_values"],
                               type_labels=labels_and_values["StudyType_labels"],
                               type_values=labels_and_values["StudyType_values"],
                               status_labels=labels_and_values["LocationStatus_labels"],
                               status_values=labels_and_values["LocationStatus_values"],
                               age_labels=labels_and_values["StdAge_labels"],
                               age_values=labels_and_values["StdAge_values"])

    else:
        return render_template("explore.html")
