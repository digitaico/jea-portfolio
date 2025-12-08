#!/usr/bin/env python3
"""
CSV Formatter for DICOM data
Generates CSV with single-quoted columns and double-quoted list elements
"""

import csv
import ast
import re
from typing import List, Tuple, Any


def clean_and_format_value(value: str) -> str:
    """
    Clean and format a value for CSV output.
    - Remove existing quotes to avoid duplication
    - Handle list values by double-quoting each element
    - Single-quote the entire value
    """
    if not value:
        return "''"
    
    # Remove existing quotes (both single and double)
    cleaned_value = value.strip()
    if cleaned_value.startswith("'") and cleaned_value.endswith("'"):
        cleaned_value = cleaned_value[1:-1]
    elif cleaned_value.startswith('"') and cleaned_value.endswith('"'):
        cleaned_value = cleaned_value[1:-1]
    
    # Check if this looks like a list representation
    if cleaned_value.startswith('[') and cleaned_value.endswith(']'):
        try:
            # Parse the list
            parsed_list = ast.literal_eval(cleaned_value)
            if isinstance(parsed_list, list):
                # Double-quote each element and join with commas
                formatted_elements = [f'"{str(item)}"' for item in parsed_list]
                list_content = ', '.join(formatted_elements)
                return f"'[{list_content}]'"
        except (ValueError, SyntaxError):
            # If parsing fails, treat as regular string
            pass
    
    # For regular strings, single-quote the entire value
    # Escape any single quotes inside the value
    escaped_value = cleaned_value.replace("'", "''")
    return f"'{escaped_value}'"


def format_data_to_csv(data: List[Tuple[str, str, str, str]], output_file: str) -> None:
    """
    Format the data to CSV with proper quoting.
    
    Args:
        data: List of tuples containing the data
        output_file: Path to the output CSV file
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Write header
        header = "'StudyInstanceUID','Group','Element','Value'"
        csvfile.write(header + '\n')
        
        # Write data rows
        for row in data:
            formatted_row = [clean_and_format_value(str(cell)) for cell in row]
            csvfile.write(','.join(formatted_row) + '\n')


def main():
    """Example usage with the provided data."""
    
    # Your example data
    example_data = [
        ('126489101', '0008', '0008', "['ORIGINAL', 'PRIMARY', 'AXIAL', 'HELICAL']"),
        ('126489101', '0008', '0020', '20250813'),
        ('126489101', '0008', '0030', '131441.000000'),
        ('126489101', '0008', '0060', 'CT'),
        ('126489101', '0008', '0070', 'UIH'),
        ('126489101', '0008', '0080', 'RADIOIMAGENES RADIOLOGOS ASOCIADOS'),
        ('126489101', '0008', '0081', 'Calle 22 # 13 - 84'),
        ('126489101', '0008', '1010', ''),
        ('126489101', '0008', '0090', ''),
        ('126489101', '0008', '1010', ''),
        ('126489101', '0008', '1030', 'CT TORAX SIMPLE'),
        ('126489101', '0008', '1040', 'MAGDALENA'),
        ('126489101', '0008', '1050', ''),
        ('126489101', '0008', '1070', 'User'),
        ('126489101', '0008', '1090', 'uCT 528'),
        ('126489101', '0010', '0030', '19900717'),
        ('126489101', '0010', '0040', 'M'),
        ('126489101', '0010', '1010', '035Y'),
        ('126489101', '0010', '1020', 'None'),
        ('126489101', '0010', '1030', 'None'),
        ('126489101', '0010', '2160', ''),
        ('126489101', '0018', '0010', ''),
        ('126489101', '0018', '0015', 'CHEST'),
        ('126489101', '0018', '0022', 'HELICAL'),
        ('126489101', '0018', '0060', '120'),
        ('126489101', '0018', '1151', '143'),
        ('126489101', '0018', '1150', '588'),
        ('126489101', '0018', '1170', '17257'),
        ('126489101', '0018', '5100', 'HFS'),
        ('126489101', '0018', '9309', '37.4'),
        ('126489101', '0020', '000D', '1.3.6.1.4.1.39470.1.1.3.7.1.2.1002380403.71824.1756824244.874'),
        ('126489101', '0020', '0010', '126489101'),
        ('126489101', '0032', '1032', ''),
        ('126489101', '0032', '1060', 'CT TORAX SIMPLE'),
        ('126489101', '0040', '0254', 'CT TORAX SIMPLE'),
        ('126489101', '0040', '0244', '20250813'),
        ('126489101', '0040', '0245', '131441')
    ]
    
    # Generate CSV
    output_file = 'formatted_dicom_data.csv'
    format_data_to_csv(example_data, output_file)
    
    print(f"CSV file generated: {output_file}")
    
    # Show first few lines of the generated file
    print("\nFirst 10 lines of the generated CSV:")
    with open(output_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 10:
                print(f"{i+1}: {line.strip()}")
            else:
                break


if __name__ == "__main__":
    main()
