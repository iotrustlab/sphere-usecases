#!/usr/bin/env python3
"""
SPHERE Use Cases - I/O Mapping Validation Tool

Validates I/O mapping CSV files for consistency and completeness.
"""

import csv
import sys
import argparse
from pathlib import Path


def validate_io_map(csv_file):
    """
    Validate an I/O mapping CSV file.
    
    Args:
        csv_file (str): Path to the I/O mapping CSV file
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    required_columns = ['Tag', 'Address', 'Type', 'Units', 'Range', 'SafetyNotes']
    errors = []
    warnings = []
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            # Check if all required columns are present
            if not reader.fieldnames:
                errors.append("CSV file is empty or has no headers")
                return False
                
            missing_columns = set(required_columns) - set(reader.fieldnames)
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(missing_columns)}")
                
            # Validate each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                # Check for empty required fields
                for col in required_columns:
                    if col in row and not row[col].strip():
                        warnings.append(f"Row {row_num}: Empty {col}")
                        
                # Validate address format
                if 'Address' in row and row['Address']:
                    address = row['Address'].strip()
                    if not address.startswith(('DI_', 'DO_', 'AI_', 'AO_')):
                        warnings.append(f"Row {row_num}: Address '{address}' doesn't follow standard format")
                        
                # Validate type
                if 'Type' in row and row['Type']:
                    io_type = row['Type'].strip()
                    if io_type not in ['Digital Input', 'Digital Output', 'Analog Input', 'Analog Output']:
                        warnings.append(f"Row {row_num}: Type '{io_type}' is not standard")
                        
    except FileNotFoundError:
        errors.append(f"File not found: {csv_file}")
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        
    # Print results
    if errors:
        print("❌ Validation FAILED:")
        for error in errors:
            print(f"  ERROR: {error}")
            
    if warnings:
        print("⚠️  Validation WARNINGS:")
        for warning in warnings:
            print(f"  WARNING: {warning}")
            
    if not errors and not warnings:
        print("✅ Validation PASSED: I/O mapping is valid")
        
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description='Validate I/O mapping CSV files')
    parser.add_argument('csv_file', help='Path to the I/O mapping CSV file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ ERROR: File not found: {args.csv_file}")
        sys.exit(1)
        
    success = validate_io_map(args.csv_file)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
