# Phenopackets to Beacon Friendly Format (BFF) Conversion Tool

## Description

This tool simplifies the metadata loading process to Beacon by converting **Phenopackets v2** into **Beacon Friendly 
Format** Biosamples and Individuals models while preserving as much information as possible.

For detailed information about the mapping of properties between Phenopackets and Beacon schemas, please refer to this spreadsheet: [Beacon + Phenopackets Schemas](https://docs.google.com/spreadsheets/d/1DfkV5BwXzOggDl53-ofi7obnHT4O7J-rtUrnhZH2BiE/edit?gid=474476020#gid=474476020).

**Please bear in mind that this is a beta version. If you encounter issues or have questions, feel free to open an issue in the [GitHub repository](https://github.com/EGA-archive/phenopackets-to-BFF/issues).**

## Features
- Converts Phenopackets to Beacon-friendly Biosamples and Individuals models.
- Retains rich metadata to ensure compatibility and completeness.
- Outputs are saved in the same directory as the input Phenopacket.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/mirgin01/phenopackets-to-BFF.git
   ```

2. Navigate to the project directory:

   ```bash
   cd phenopackets-to-BFF
   ```

## Usage

Run the script with the path to your Phenopacket file:

```bash
python working-w-phenopackets.py /path/to/phenopacket.json
```

### Output
- The converted Beacon Friendly Format (BFF) files will be saved in the same directory as the input Phenopacket.

## Requirements

- Python 3.8 or higher
- rich
- protobuf
- phenopackets==2.0.0

To install dependencies:

```bash
pip install -r requirements.txt
```

## About the Mapping

Most of the mapping between the Phenopackets and Beacon models was straightforward. However, some fields in the Phenopacket schema did not have a direct match in the Beacon schema.

Fields containing important metadata that could not be mapped to a specific Beacon property were stored in the additionalInformation (notes) field to preserve as much information as possible.

### Specific Mappings

- **Individuals.diseases.notes:**

The following Phenopacket fields related to diseases were saved in the notes field:
- resolution
- primary_site
- laterality
- excluded


- **Individuals.info:**

The file.individual_to_file_identifiers field from Phenopackets is saved in the info property of the Beacon individual.

- **Biosamples.notes:**

The biosamples.description field is stored in the notes field of the Beacon biosample.

### Handling collectionData

The biosamples.timeOfCollection property in Phenopackets supports various data types, including:

- gestationalAge: Measure of the age of a pregnancy
- Age: Age as an ISO8601 duration (e.g., P40Y10M05D)
- AgeRange: Age within a given range
- OntologyClass: Age as an ontology class
- Timestamp: Specific date and time
- TimeInterval: Time interval

In contrast, the Beacon schema defines biosamples.collectionDate as the "Date of biosample collection in ISO8601 
format" and expects a simple string.

To maximize data retention, the tool converts the collectionData from Phenopackets to a string and stores it in the collectionDate property of Beacon. While this approach does not fully align with the intended collectionDate field usage, it ensures valuable data is not lost.


## Support
If you encounter issues or have questions, feel free to open an issue in the [GitHub repository](https://github.com/mirgin01/phenopackets/issues).

## License


