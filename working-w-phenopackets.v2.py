import json
from google.protobuf.json_format import MessageToDict, ParseDict
import phenopackets.schema.v2 as pps2
from validators.biosamples import Biosamples
from validators.individuals import Individuals

# Load JSON Phenopacket file
with open('./testphen.json', 'r') as f:
    phenopacket_data = json.load(f)

# Deserialize JSON into a Phenopacket protobuf object and convert to dictionary
phenopacket = ParseDict(phenopacket_data, pps2.Phenopacket())
phenopacket_dict = MessageToDict(phenopacket)

# General mapping dictionaries
biosamples_mapping = {
    "id": "id",
    "individualId": "individualId",
    "description": "notes",
    "materialSample": "biosampleStatus",
    "timeOfCollection": "collectionDate",
    "sampleType": "sampleOriginType",
    "sampledTissue": "sampleOriginDetail",
    "procedure": "obtentionProcedure",
    "tumorProgression": "tumorProgression",
    "tumorGrade": "tumorGrade",
    "pathologicalStage": "pathologicalStage",
    "pathologicalTnmFinding": "pathologicalTnmFinding",
    "histologicalDiagnosis": "histologicalDiagnosis",
    "diagnosticMarkers": "diagnosticMarkers",
    "phenotypicFeatures": "phenotypicFeatures",
    "measurements": "measurements",
    "sampleProcessing": "sampleProcessing",
    "sampleStorage": "sampleStorage",
}

measurement_mapping = {
    "assay": "assayCode",
    "value": "measurementValue",
    "timeObserved": "observationMoment",
    "procedure": "procedure",
    "performed": "date",
    "description": "notes"
}

procedure_mapping = {
    "code": "procedureCode",
    "bodySite": "bodySite",
    "performed": "ageAtProcedure"
}

sex_mapping = {
    "UNKNOWN_SEX" : {"id": "NCIT_C17998", "label": "Uknown"},
    "FEMALE": {"id": "NCIT_C46113", "label": "Female"},
    "MALE": {"id": "NCIT:C46112", "label": "Male"},
    "OTHER_SEX" : {"id": "NCIT:C45908", "label": "Intersex"},
}

diseases_mapping = {
    "onset": "ageOfOnset",
    "term" : "diseaseCode",
    "clinicalTnmFinding" : "severity",
     "diseaseStage" : "stage"
}

phenotypicFeature_mapping= {
    "evidence" : "evidence",
    "type": "featureType",
    "modifiers" : "modifiers",
    "description": "notes",
    "onset": "onset",
    "resolution" : "resolution",
    "severity" : "severity"
}

medicalActions_mapping = {
    "cumulativeDose":"cumulativeDose",
    "doseIntervals": "doseIntervals",
    "routeOfAdministration" : "routeOfAdministration",
    "agent" : "treatmentCode"
}

timeElement = ["age", "ageRange", "gestationalAge", "timestamp", "ontologyClass"]


def rename_keys(data, mapping):
    """
    Rename keys in a dictionary based on a given mapping.

    Args:
        data (dict): The original dictionary.
        mapping (dict): The mapping of old keys to new keys.

    Returns:
        dict: A new dictionary with renamed keys.
    """
    return {mapping.get(k, k): v for k, v in data.items() if k in mapping}


def process_time_element(data):
    """
    Extracts the correct value from a dictionary containing time-related elements.
    It preserves structure dynamically.

    Args:
        data (dict): The dictionary that may contain time-related elements.

    Returns:
        dict: A formatted dictionary with the correct time element structure.
    """
    if not isinstance(data, dict):
        return data  # If data is not a dictionary, return as is.

    for key in timeElement:
        if key in data:
            value = data[key]

            if isinstance(value, dict):
                # Recursively process nested structures
                return {k: process_time_element(v) for k, v in value.items()}
            return value  # If it's not a dict, return directly (handles simple cases like timestamps)

    return data  # If no match is found, return unchanged



def process_measurement(measurement):
    """
    Process and rename measurement properties.
    """
    measurement = rename_keys(measurement, measurement_mapping)

    # Process nested 'procedure'
    if "procedure" in measurement:
        measurement["procedure"] = rename_keys(measurement["procedure"], procedure_mapping)

        # Handle ageAtProcedure dynamically with all timeElement options
        if "ageAtProcedure" in measurement["procedure"]:
            measurement["procedure"]["ageAtProcedure"] = process_time_element(measurement["procedure"]["ageAtProcedure"])

    # Process measurementValue
    if "measurementValue" in measurement and "quantity" in measurement["measurementValue"]:
        quantity = measurement["measurementValue"]["quantity"]
        measurement["measurementValue"] = {
            "unit": quantity.get("unit"),
            "value": quantity.get("value"),
            "referenceRange": quantity.get("referenceRange")
        }

    # Process observationMoment dynamically
    if "observationMoment" in measurement:
        measurement["observationMoment"] = process_time_element(measurement["observationMoment"])

    return measurement


def process_biosamples(data):
    """
    Process and rename the biosample properties.
    """
    biosample = rename_keys(data, biosamples_mapping)

    # Convert collectionDate to string if it exists
    if "collectionDate" in biosample:
        biosample["collectionDate"] = str(biosample["collectionDate"])

    # Process measurements
    if "measurements" in biosample and isinstance(biosample["measurements"], list):
        biosample["measurements"] = [process_measurement(measurement) for measurement in biosample["measurements"]]

    # Process obtentionProcedure
    if "obtentionProcedure" in biosample:
        biosample["obtentionProcedure"] = rename_keys(biosample["obtentionProcedure"], procedure_mapping)

        # Handle ageAtProcedure dynamically with all timeElement options
        if "ageAtProcedure" in biosample["obtentionProcedure"]:
            biosample["obtentionProcedure"]["ageAtProcedure"] = process_time_element(biosample["obtentionProcedure"]["ageAtProcedure"])

    return biosample


# Apply transformations

for biosample in phenopacket_dict["biosamples"]:
    biosamples_beacon_dict = process_biosamples(biosample)



individuals_beacon_dict = {}

# From subject : contains the two mandatory fields for Individuals

if phenopacket_dict["subject"] and "id" and "sex" in phenopacket_dict["subject"]: # mandatory fields for Individuals
    individuals_beacon_dict["id"] = phenopacket_dict["subject"]["id"]
    for key in sex_mapping.keys():
        if key in phenopacket_dict["subject"]["sex"]:
            individuals_beacon_dict["sex"] = sex_mapping[key]
    if "karyotypicSex" in phenopacket_dict["subject"]:
        individuals_beacon_dict["karyotypicSex"] = phenopacket_dict["subject"]["karyotypicSex"]


if "measurements" in phenopacket_dict:
    measurement_beacon = process_measurement(phenopacket_dict["measurements"][0])
    individuals_beacon_dict["measures"] = [measurement_beacon]

if "files" in phenopacket_dict : # additional info
    individuals_beacon_dict["info"] = phenopacket_dict["files"][0]["individualToFileIdentifiers"]




diseases_extra_att = ["resolution", "primarySite", "laterality"]
diseases_keys_to_reformat = ["severity", "stage"]

if "diseases" in phenopacket_dict:
    individuals_beacon_dict["diseases"] = []
    for i, disease in enumerate(phenopacket_dict["diseases"]):
        if any(key in disease for key in diseases_extra_att): # save information that doesn't have a field in beacon
            notes = {
                "resolution": disease.get("resolution"),
                "primarySite": disease.get("primarySite"),
                "laterality": disease.get("laterality"),
            }
        updated_disease = rename_keys(disease, diseases_mapping)
        for key in diseases_keys_to_reformat:
            if key in updated_disease.keys():
                updated_disease[key] = updated_disease[key][0] # must be dict not list
        if "ageOfOnset" in updated_disease.keys(): # correct time formatting
            updated_disease["ageOfOnset"] = process_time_element(
                updated_disease["ageOfOnset"])

        updated_disease["notes"] = str(notes) ## add extra attributes

        individuals_beacon_dict["diseases"].append(updated_disease) ## add it to beacon language dict



if "phenotypicFeatures" in phenopacket_dict:
    individuals_beacon_dict["phenotypicFeatures"] = []
    for i, phenotypicFeature in enumerate(phenopacket_dict["phenotypicFeatures"]):
        updated_keys = rename_keys(phenotypicFeature, phenotypicFeature_mapping)
        for key in diseases_keys_to_reformat:
            if key in updated_keys.keys():
                updated_keys[key] = updated_keys[key]  # must be dict not list
        if "evidence" in updated_keys.keys():
            updated_keys["evidence"] = updated_keys["evidence"][0]
            if "reference" in updated_keys["evidence"]:
                updated_keys["evidence"]["reference"]["notes"] = updated_keys["evidence"]["reference"].pop(
                    "description")
        for key in ["onset", "resolution"]: #timeElement objects
            if key in updated_keys.keys():
                updated_keys[key] = process_time_element(updated_keys[key])

        individuals_beacon_dict["phenotypicFeatures"].append(updated_keys)  ## add it to beacon language dict




if "medicalActions" in phenopacket_dict:
    individuals_beacon_dict["treatments"] = []
    individuals_beacon_dict["interventionsOrProcedures"] = []
    for i, medicalAction in enumerate(phenopacket_dict["medicalActions"]):
        if "treatment" in medicalAction.keys():
            updated_keys = rename_keys(medicalAction["treatment"], medicalActions_mapping)
            individuals_beacon_dict["treatments"].append(updated_keys)
        if "procedure" in medicalAction.keys():
            updated_keys = rename_keys(medicalAction["procedure"], procedure_mapping)
            updated_keys["ageAtProcedure"] = process_time_element(updated_keys["ageAtProcedure"])
            individuals_beacon_dict["interventionsOrProcedures"].append(updated_keys)











print(biosamples_beacon_dict)


# Validate with Biosamples class
Biosamples(**biosamples_beacon_dict)
Individuals(**individuals_beacon_dict)
