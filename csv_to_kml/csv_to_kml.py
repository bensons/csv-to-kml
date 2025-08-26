#!/usr/bin/env python3
"""
CSV to KML Converter - A simplified single-file tool to convert CSV data to KML format.

This tool can either geocode addresses or use existing latitude/longitude coordinates
to create KML files for use in mapping applications like Google Earth.
"""

import argparse
import csv
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from xml.dom import minidom

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


def parse_csv(file_path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse CSV file and return data and headers."""
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        data = list(reader)
    return data, headers


def find_address_column(headers: List[str], column_name: str) -> str:
    """Find the address column, with fallback to columns containing 'address'."""
    if column_name in headers:
        return column_name

    # Look for columns containing 'address' (case insensitive)
    address_columns = [col for col in headers if 'address' in col.lower()]
    if address_columns:
        return address_columns[0]

    raise ValueError(f"Column '{column_name}' not found in CSV. Available columns: {', '.join(headers)}")


def geocode_address(geocoder, address: str, cache: Dict[str, Optional[Tuple[float, float]]],
                   delay: float = 1.0) -> Optional[Tuple[float, float]]:
    """Geocode a single address with caching."""
    if not address or address.strip() == '':
        return None

    if address in cache:
        return cache[address]

    try:
        time.sleep(delay)
        location = geocoder.geocode(address, timeout=10)

        if location:
            coordinates = (location.longitude, location.latitude)
            cache[address] = coordinates
            return coordinates
        else:
            cache[address] = None
            return None

    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error for '{address}': {e}")
        cache[address] = None
        return None
    except Exception as e:
        print(f"Unexpected error geocoding '{address}': {e}")
        cache[address] = None
        return None


def batch_geocode(addresses: List[str]) -> Dict[str, Optional[Tuple[float, float]]]:
    """Geocode multiple addresses with progress reporting."""
    if not GEOPY_AVAILABLE:
        raise ImportError("geopy is required for geocoding. Install with: pip install geopy")

    geocoder = Nominatim(user_agent="csv-to-kml-converter")
    cache = {}
    results = {}
    total = len(addresses)

    for idx, address in enumerate(addresses, 1):
        percent = (idx / total) * 100
        print(f"Geocoding {idx}/{total} ({percent:.1f}%): {address[:50]}...")

        coordinates = geocode_address(geocoder, address, cache)
        results[address] = coordinates

    return results


def generate_kml(placemarks: List[Dict[str, Any]], document_name: str = "CSV Data Points") -> str:
    """Generate KML content from placemark data."""
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = ET.SubElement(kml, 'Document')

    # Document name
    doc_name = ET.SubElement(document, 'name')
    doc_name.text = document_name

    # Add default style
    style = ET.SubElement(document, 'Style', id='defaultStyle')
    icon_style = ET.SubElement(style, 'IconStyle')
    color = ET.SubElement(icon_style, 'color')
    color.text = 'ff0000ff'  # Red color
    scale = ET.SubElement(icon_style, 'scale')
    scale.text = '1.0'
    icon = ET.SubElement(icon_style, 'Icon')
    href = ET.SubElement(icon, 'href')
    href.text = 'http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png'

    # Add placemarks
    for placemark_data in placemarks:
        placemark = ET.SubElement(document, 'Placemark')

        # Name
        name = ET.SubElement(placemark, 'name')
        name.text = str(placemark_data['name'])

        # Description
        if placemark_data.get('description'):
            description = ET.SubElement(placemark, 'description')
            desc_text = placemark_data['description']

            # Add extended data as HTML table if present
            if placemark_data.get('extended_data'):
                desc_parts = [desc_text, "<![CDATA[<table border='1'>"]
                for key, value in placemark_data['extended_data'].items():
                    desc_parts.append(f"<tr><td><b>{key}</b></td><td>{value}</td></tr>")
                desc_parts.extend(["</table>]]>"])
                desc_text = '\n'.join(desc_parts)

            description.text = desc_text

        # Style
        style_url = ET.SubElement(placemark, 'styleUrl')
        style_url.text = '#defaultStyle'

        # Extended data (for compatibility)
        if placemark_data.get('extended_data'):
            extended_data = ET.SubElement(placemark, 'ExtendedData')
            for key, value in placemark_data['extended_data'].items():
                data = ET.SubElement(extended_data, 'Data', name=key)
                value_elem = ET.SubElement(data, 'value')
                value_elem.text = str(value)

        # Point coordinates
        point = ET.SubElement(placemark, 'Point')
        coordinates = ET.SubElement(point, 'coordinates')
        lon, lat = placemark_data['coordinates']
        coordinates.text = f"{lon},{lat},0"

    # Pretty print XML
    rough_string = ET.tostring(kml, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def convert_csv_to_kml(csv_file: str, output_file: str = None,
                      address_column: str = 'Address',
                      name_column: str = None,
                      skip_geocoding: bool = False,
                      lat_column: str = None,
                      lon_column: str = None) -> str:
    """Main conversion function."""

    # Validate input file
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    # Set output file if not provided
    if output_file is None:
        base_name = Path(csv_file).stem
        output_file = f"{base_name}.kml"

    # Parse CSV
    print(f"Parsing CSV file: {csv_file}")
    data, headers = parse_csv(csv_file)

    if not data:
        raise ValueError("No data found in CSV file")

    print(f"Found {len(data)} rows in CSV")

    placemarks = []

    if skip_geocoding and lat_column and lon_column:
        # Use existing coordinates
        print("Using latitude and longitude columns from CSV")

        if lat_column not in headers:
            raise ValueError(f"Latitude column '{lat_column}' not found in CSV")
        if lon_column not in headers:
            raise ValueError(f"Longitude column '{lon_column}' not found in CSV")

        for idx, row in enumerate(data, 1):
            try:
                lat = float(row.get(lat_column, 0))
                lon = float(row.get(lon_column, 0))
                coordinates = (lon, lat)
            except (ValueError, TypeError):
                print(f"Skipping row {idx}: Invalid coordinates")
                continue

            # Determine name
            if name_column and name_column in headers:
                name = row.get(name_column, f"Point {idx}")
            else:
                name = row.get(address_column, f"Point {idx}")

            # Extended data (exclude coordinate and name columns)
            excluded_cols = {lat_column, lon_column}
            if name_column:
                excluded_cols.add(name_column)
            if address_column in headers:
                excluded_cols.add(address_column)

            extended_data = {k: v for k, v in row.items() if k not in excluded_cols and v}

            placemarks.append({
                'name': name,
                'coordinates': coordinates,
                'description': row.get(address_column, ''),
                'extended_data': extended_data
            })

    else:
        # Geocode addresses
        print("Geocoding addresses...")

        # Find address column
        address_col = find_address_column(headers, address_column)

        # Get unique addresses
        addresses = [row.get(address_col, '') for row in data]
        unique_addresses = list(set(filter(None, addresses)))

        print(f"Geocoding {len(unique_addresses)} unique addresses...")
        geocoded_addresses = batch_geocode(unique_addresses)

        # Create placemarks
        success_count = 0
        for idx, row in enumerate(data, 1):
            address = row.get(address_col, '')
            coordinates = geocoded_addresses.get(address)

            if not coordinates:
                print(f"Warning: Could not geocode address: {address}")
                continue

            success_count += 1

            # Determine name
            if name_column and name_column in headers:
                name = row.get(name_column, address)
            else:
                name = address

            # Extended data (exclude address and name columns)
            excluded_cols = {address_col}
            if name_column:
                excluded_cols.add(name_column)

            extended_data = {k: v for k, v in row.items() if k not in excluded_cols and v}

            placemarks.append({
                'name': name,
                'coordinates': coordinates,
                'description': address,
                'extended_data': extended_data
            })

        print(f"Successfully geocoded {success_count}/{len(data)} addresses")

    # Generate and save KML
    print(f"Generating KML with {len(placemarks)} placemarks...")
    kml_content = generate_kml(placemarks, document_name=Path(csv_file).stem)

    print(f"Saving KML file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(kml_content)

    print(f"Conversion complete! KML file saved as: {output_file}")
    return output_file


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Convert CSV file with addresses to KML format',
        epilog='Examples:\n'
               '  %(prog)s data.csv\n'
               '  %(prog)s data.csv -o output.kml\n'
               '  %(prog)s data.csv --skip-geocoding --lat-column Latitude --lon-column Longitude',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('csv_file', help='Path to input CSV file')
    parser.add_argument('-o', '--output', help='Output KML file path (default: input_filename.kml)')
    parser.add_argument('-a', '--address-column', default='Address',
                       help='Name of the address column (default: Address)')
    parser.add_argument('-n', '--name-column',
                       help='Column to use for placemark names (default: uses address)')
    parser.add_argument('--skip-geocoding', action='store_true',
                       help='Skip geocoding and use lat/lon columns from CSV')
    parser.add_argument('--lat-column', help='Latitude column name (when skip-geocoding is used)')
    parser.add_argument('--lon-column', help='Longitude column name (when skip-geocoding is used)')

    args = parser.parse_args()

    # Validate arguments
    if args.skip_geocoding and (not args.lat_column or not args.lon_column):
        parser.error("--lat-column and --lon-column are required when --skip-geocoding is used")

    if not args.skip_geocoding and not GEOPY_AVAILABLE:
        parser.error("geopy is required for geocoding. Install with: pip install geopy")

    try:
        convert_csv_to_kml(
            csv_file=args.csv_file,
            output_file=args.output,
            address_column=args.address_column,
            name_column=args.name_column,
            skip_geocoding=args.skip_geocoding,
            lat_column=args.lat_column,
            lon_column=args.lon_column
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()