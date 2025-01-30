import json
from google.protobuf.json_format import MessageToDict, ParseDict
import phenopackets.schema.v2 as pps2
from validators.biosamples import Biosamples


# Load JSON Phenopacket file
with open('./testphen.json', 'r') as f:
    phenopacket_data = json.load(f)

# Deserialize JSON into a Phenopacket protobuf object and convert to dictionary
phenopacket = ParseDict(phenopacket_data, pps2.Phenopacket())
phenopacket_dict = MessageToDict(phenopacket)

biosamples_phenopacket = phenopacket_dict["biosamples"][0]  # Extract biosamples block

# General mapping dictionaries
beacon_mapping = {
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
    biosample = rename_keys(data, beacon_mapping)

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
biosamples_beacon_dict = process_biosamples(biosamples_phenopacket)

# Validate with Biosamples class
Biosamples(**biosamples_beacon_dict)
