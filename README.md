# CSV to KML Converter

Convert CSV files with addresses or coordinates to KML format for Google Earth and mapping applications.

## Installation

Clone this repository and install using Poetry:

```bash
git clone https://github.com/yourusername/csv-to-kml
cd csv-to-kml
poetry install
```

For address geocoding support:
```bash
poetry install -E geocoding
```

## Usage

**Convert addresses to KML:**
```bash
poetry run csv-to-kml data.csv
```

**Use existing coordinates:**
```bash
poetry run csv-to-kml data.csv --skip-geocoding --lat-column Latitude --lon-column Longitude
```

**Options:**
- `-o OUTPUT` - Output file path
- `-a COLUMN` - Address column name (default: Address)
- `-n COLUMN` - Name column for placemarks
- `--skip-geocoding` - Use existing lat/lon columns
- `--lat-column` / `--lon-column` - Coordinate column names

## CSV Format

**With addresses:**
```csv
Name,Address
Library,1000 4th Ave Seattle WA
Space Needle,400 Broad St Seattle WA
```

**With coordinates:**
```csv
Name,Latitude,Longitude
Statue of Liberty,40.6892,-74.0445
Empire State Building,40.7484,-73.9857
```

## License

MIT License
