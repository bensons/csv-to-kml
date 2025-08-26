# CSV to KML Converter

Convert CSV files with addresses or coordinates to KML format for Google Earth and mapping applications.

## Installation

Download `csv_to_kml.py` or clone this repository.

For address geocoding: `pip install geopy`

## Usage

**Convert addresses to KML:**
```bash
python csv_to_kml.py data.csv
```

**Use existing coordinates:**
```bash
python csv_to_kml.py data.csv --skip-geocoding --lat-column Latitude --lon-column Longitude
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
