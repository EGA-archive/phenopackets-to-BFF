import json
from google.protobuf.json_format import MessageToDict
import phenopackets.schema.v2 as pps2
from google.protobuf.json_format import ParseDict
from validators.biosamples import Biosamples

# Load the JSON Phenopacket file
with open('./testphen.json', 'r') as f:
    phenopacket_data = json.load(f)

"""
# Deserialize JSON into a Phenopacket object
#phenopacket = pps2.Phenopacket(**phenopacket_data)

# Convert the Phenopacket object to a Python dictionary
#pf2 = MessageToDict(phenopacket_data)

This reads the json/phenopacket as a dictionary (string) which gives issue with Timestaps.
"""

"""
This command reads the phenopackets as a message (protobuf) which correctly understands the Timestamps formatting. 
"""
phenopacket = ParseDict(phenopacket_data, pps2.Phenopacket())

phenopacket = MessageToDict(phenopacket)

biosamples_phenopacket = phenopacket["biosamples"][0] # only take biosamples building block

print(biosamples_phenopacket)

# Rename building blocks

beacon_mapping = {
    "id": "id", #phenopacket : beacon
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

biosamples_beacon_dict = {}

for key, value in biosamples_phenopacket.items():
    for key_beacon in beacon_mapping.keys():
        if key == key_beacon:
            biosamples_beacon_dict[beacon_mapping[key_beacon]] =value

# Adapt properties of building blocks

# collection Date
biosamples_beacon_dict["collectionDate"] = str(biosamples_beacon_dict["collectionDate"]) # from dict to string

# measurements

measurement_mapping = { # rename properties of measurement
    "assay" : "assayCode",
    "value" : "measurementValue",
    "timeObserved" : "observationMoment",
    "procedure" : "procedure",
    "performed" : "date",
    "description" : "notes"
}

measurement_beconized = {}

for key, value in biosamples_beacon_dict["measurements"][0].items():
    for key_measurement in measurement_mapping.keys():
        if key == key_measurement:
            measurement_beconized[measurement_mapping[key_measurement]] = value

biosamples_beacon_dict["measurements"] = [measurement_beconized] # update final dict

"""
The biosamples_beacon_dict["measurements"] key is expected to be a list of dictionaries that Pydantic can unpack into Measurement objects.
"""

# Extract unit, value and referenceRange from quantity as in the beacon spec the 3 entries are directly in
# measurementValue

if "measurementValue" in measurement_beconized and "quantity" in measurement_beconized["measurementValue"]:
    quantity = measurement_beconized["measurementValue"]["quantity"]
    measurement_beconized["measurementValue"] = {
        "unit": quantity.get("unit"),
        "value": quantity.get("value"),
        "referenceRange": quantity.get("referenceRange")
    }

biosamples_beacon_dict["measurements"] = [measurement_beconized] # update final dict

measurement_procedure_mapping = {
    "code" : "procedureCode",
    "bodySite" : "bodySite",
    "performed": "ageAtProcedure"
}

measurement_procedure_beconized = {}

for key, value in biosamples_beacon_dict["measurements"]["procedure"][0].items():
    for key_measurement in measurement_procedure_mapping.keys():
        if key == key_measurement:
            measurement_procedure_beconized[measurement_procedure_mapping[key_measurement]] = value

biosamples_beacon_dict["measurements"]["procedure"] = measurement_procedure_beconized

"""
WORKING ON: 
- updating the names of the fields inside measurement.procedure --> measurement_procedure_mapping
- why is bodySite not being read?
"""
print(biosamples_beacon_dict["measurements"])
Biosamples(**biosamples_beacon_dict)







