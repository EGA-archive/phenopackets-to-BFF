__author__ = "Mireia Marin Ginestar"
__version__ = "1.0"
__maintainer__ = "Mireia Marin Ginestar"
__email__ = "mireia.marin@crg.eu"

import json
import sys
from rich.console import Console
console = Console()
from google.protobuf.json_format import MessageToDict, ParseDict
import phenopackets.schema.v2 as pps2
from validators.biosamples import Biosamples
from validators.individuals import Individuals
from google.protobuf.json_format import ParseError

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
    "UNKNOWN_SEX" : {"id": "NCIT:C17998", "label": "Uknown"},
    "FEMALE": {"id": "NCIT:C46113", "label": "Female"},
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
    "severity" : "severity",
    "excluded" : "excluded"
}

medicalActions_mapping = {
    "cumulativeDose":"cumulativeDose",
    "doseIntervals": "doseIntervals",
    "routeOfAdministration" : "routeOfAdministration",
    "agent" : "treatmentCode"
}

timeElement = {
    "age" : "age",
    "ageRange" : "ageRange",
    "gestationalAge" : "gestationalAge",
    "timestamp" : "timestamp",
    "interval" : "timeInterval",
    "ontologyClass" : "OntologyTerm"
}

pedigree_affectedStatus = {
    "AFFECTED" : True,
    "UNAFFECTED" : False,
    "MISSING" : "missing" # this will trough an error in the beacon validators. Only boolean values accepted.
}
diseases_extra_att = ["resolution", "primarySite", "laterality", "excluded"]
diseases_keys_to_reformat = ["severity", "stage"]


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
            value = data[key] # gets the timeElement content

            if isinstance(value, dict):
                # Recursively process nested structures
                return {k: process_time_element(v) for k, v in value.items()}
            return value  # If it's not a dict, return directly (handles simple cases like timestamps)

    return data  # If no match is found, return unchanged



def process_measurement(measurement):
    """
    Process and rename measurement properties.
    Args:
        measurement (dict): The original measurement dictionary.

    Returns:
        dict: A new measurement dictionary with beacon structure.
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

def process_disease(disease):
    """
    Process and rename disease properties.
    Args:
        disease (dict): The original disease dictionary.

    Returns:
        dict: A new disease dictionary with beacon structure.
        *** The properties resolution, primarySite and laterality doesn't have a specific field in beacon.
            To avoid losing the info, if present saved as notes.
    """

    notes = {}
    if any(key in disease for key in diseases_extra_att):  # save information that doesn't have a field in beacon
        # as notes
        notes = {
            "resolution": disease.get("resolution"),
            "primarySite": disease.get("primarySite"),
            "laterality": disease.get("laterality"),
            "excluded": disease.get("excluded")
        }
    updated_disease = rename_keys(disease, diseases_mapping) # rename keys
    for key in diseases_keys_to_reformat:
        if key in updated_disease.keys():
            updated_disease[key] = updated_disease[key][0]  # must be dict not list
    if "ageOfOnset" in updated_disease.keys():  # correct time formatting
        updated_disease["ageOfOnset"] = process_time_element(
            updated_disease["ageOfOnset"])
    if notes:
        updated_disease["notes"] = str(notes)  ## add extra attributes

    return updated_disease

def process_phenotypicFeatures(phenotypicFeature):
    """
    Process and rename phenotypicFeatures properties.
    Args:
        phenotypicFeature (dict): The original phenotypicFeature dictionary.

    Returns:
        dict: A new phenotypicFeature dictionary with beacon structure.
    """
    updated_phenotypicFeature = rename_keys(phenotypicFeature, phenotypicFeature_mapping)

    if "evidence" in updated_phenotypicFeature.keys():
        updated_phenotypicFeature["evidence"] = updated_phenotypicFeature["evidence"][0]
        if "reference" in updated_phenotypicFeature["evidence"]:
            updated_phenotypicFeature["evidence"]["reference"]["notes"] = updated_phenotypicFeature["evidence"]["reference"].pop(
                "description") # extra entry not allowed
    for key in ["onset", "resolution"]:  # timeElement objects
        if key in updated_phenotypicFeature.keys():
            updated_phenotypicFeature[key] = process_time_element(updated_phenotypicFeature[key])

    return updated_phenotypicFeature



def gather_biosamples(data):
    """
    Process and rename the biosample properties.

    Args:
        data (dict): Dictionary containing biosamples building block.

    Returns:
        dict: A formatted dictionary with the correct properties names and levels.
    """
    if "id" and "materialSample" and "sampleType" in biosamples_mapping:
        print("Mandatory properties for Biosamples schema (id, materialSample and sampleType) present in the "
              "phenopacket.")
        print("-> Creating Biosamples schema ...")
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

        # log of the properties added
        matching_keys = [key for key, value in biosamples_mapping.items() if value in biosample] # list of properties
        # added in phenopackets properties naming
        for key in matching_keys:
            print(f"    - {key} added to Biosamples")
        print("-> Creating Biosamples schema - DONE")

        return biosample

    else:
        print("The mandatory fields for Biosamples beacon schema (id, biosamplesStatus and sampleOriginType) are not "
              "present in the phenopacket")
        print("... Skipping Biosamples Schema ...")

def create_biosamples(phenopacket_dict):
    """
    Loop through all the biosamples in the phenopackets and creates a JSON per biosamples.id
    Args:
        phenopacket_dict (dict): Complete phenopacket dict

    Returns:
        dict: A formatted dictionary with the correct properties names and levels for biosamples model
    """
    for biosample in phenopacket_dict["biosamples"]:  # Biosamples multiciplicity : 0..*
        biosamples_beacon_dict = gather_biosamples(biosample)

        Biosamples(**biosamples_beacon_dict)  # Validate output with beacon r.i tools v2 validators

        output_path = sys.argv[1].replace(".json", f"-biosamplesBFF-"
                                                   f"{biosamples_beacon_dict['id']}.json")  # new name for
        # output file
        with open(output_path, "w") as f:  # save BFFs
            json.dump([biosamples_beacon_dict], f, indent=4)
        console.print("[bold]+ BFFs BioSamples JSON saved in: [/bold]", output_path)


def gather_individuals(data):
    """
    Gather and rename different properties to form individuals
    Args:
        data (dict): Complete phenopacket dict (individuals info doesn't come from one single building block)

    Returns:
        dict: A formatted dictionary with the correct properties names and levels for individuals model
    """
    individuals_beacon_dict = {}
    individuals_beacon_dict["id"] = data["subject"]["id"]

    for key in sex_mapping.keys():
        if key == data["subject"]["sex"]:
            individuals_beacon_dict["sex"] = sex_mapping[key]
    
    if "karyotypicSex" in data["subject"]:
        individuals_beacon_dict["karyotypicSex"] = data["subject"]["karyotypicSex"]
        print("    - karyotypicSex added to Individuals")

    if "measurements" in data:
        print("    - measurements added to Individuals")
        for assayCode in data["measurements"]:
            measurement_beacon = process_measurement(assayCode)
            individuals_beacon_dict.setdefault("measures", []).append(measurement_beacon)

    if "files" in data:  # additional info
        for file in data["files"]:
            if "individualToFileIdentifiers" in file:
                print("    - individualToFileIdentifiers added as info to Individuals")
                mapping = {"individualToFileIdentifiers": file["individualToFileIdentifiers"]}
                individuals_beacon_dict["info"] = mapping

    if "diseases" in data:
        print("    - diseases added to Individuals")
        for disease in data["diseases"]:
            updated_disease = process_disease(disease)
            individuals_beacon_dict.setdefault("diseases", []).append(updated_disease)  ## add it to beacon language dict



    if "phenotypicFeatures" in data:
        print("    - phenotypicFeatures added to Individuals")
        for phenotypicFeature in data["phenotypicFeatures"]:
            updated_phenotypicFeature = process_phenotypicFeatures(phenotypicFeature)
            individuals_beacon_dict.setdefault("phenotypicFeatures", []).append(
                updated_phenotypicFeature)  ## add it to beacon language dict

    if "medicalActions" in data:
        for medicalAction in data["medicalActions"]:
            if "treatment" in medicalAction.keys():
                print("    - medicalAction.action.treatment added as treatment to Individuals")
                updated_keys = rename_keys(medicalAction["treatment"], medicalActions_mapping)
                individuals_beacon_dict.setdefault("treatments", []).append(updated_keys)
            if "procedure" in medicalAction.keys():
                print("    - medicalAction.action.procedure added as interventionsOrProcedures to Individuals")
                updated_keys = rename_keys(medicalAction["procedure"], procedure_mapping)
                updated_keys["ageAtProcedure"] = process_time_element(updated_keys["ageAtProcedure"])
                individuals_beacon_dict.setdefault("interventionsOrProcedures", []).append(updated_keys)

    return individuals_beacon_dict

def create_individuals(data):
    """
    Check if mandatory fields for individuals are present and start the processing
    Args:
        data (dict): Complete phenopacket dict (individuals info doesn't come from one single building block)

    Returns:
        dict: A formatted dictionary with the correct properties names and levels for individuals model
    """
    if "subject" in data and "id" in data["subject"] and "sex" in data["subject"]:  # mandatory fields for Individuals
        print("Mandatory properties for Individual schema (id and sex) present in the phenopacket.")
        print("-> Creating Individuals schema ...")
        individuals_beacon_dict = gather_individuals(data) # if JSON phenopacket
        print("-> Creating Individuals schema - DONE")

    else:
        print("The mandatory fields for Individuals beacon schema (id and sex) are not present in your phenopacket")
        print("... Skipping Individuals Schema ...")

    return individuals_beacon_dict

def main():

    with open(sys.argv[1], 'r') as f: # Load JSON Phenopacket file
        phenopacket_data = json.load(f)

    # Deserialize JSON into a Phenopacket protobuf object and convert to dictionary
    phenopacket = ParseDict(phenopacket_data, pps2.Phenopacket())
    phenopacket_dict = MessageToDict(phenopacket)

    if "biosamples" in phenopacket_dict:
        create_biosamples(phenopacket_dict)
    else:
        console.print("[bold]The mandatory fields for BioSamples were not present in the phenopacket "
                      "[/bold]")

    individuals_beacon_dict = create_individuals(phenopacket_dict) # Individuals multiciplicity: 0..1
    if individuals_beacon_dict:
        Individuals(**individuals_beacon_dict) # Validate output with beacon r.i tools v2 validators
        output_path = sys.argv[1].replace(".json", "-individualsBFF.json")  # new name for output file
        with open(output_path, "w") as f:  # save BFFs
            json.dump([individuals_beacon_dict], f, indent=4)
        console.print("[bold]+ BFFs Individuals JSON saved in: [/bold]", output_path)
    else:
        console.print("[bold]The mandatory fields for Individuals were not present in the phenopacket "
                      "[/bold]")

if __name__ == "__main__":  # the first executed function will be main()
    main()