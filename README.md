# Phenopackets to Beacon Friendly Format (BFF) Conversion Tool

## Description

This tool simplifies the metadata loading process to Beacon by converting **Phenopackets v2** into **Beacon Friendly 
Format** Biosamples and Individuals models while preserving as much information as possible.

For detailed information about the mapping of properties between Phenopackets and Beacon schemas, please refer to this spreadsheet: [Beacon + Phenopackets Schemas](https://docs.google.com/spreadsheets/d/1DfkV5BwXzOggDl53-ofi7obnHT4O7J-rtUrnhZH2BiE/edit?gid=474476020#gid=474476020).

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

## Support
If you encounter issues or have questions, feel free to open an issue in the [GitHub repository](https://github.com/mirgin01/phenopackets/issues).

## License


