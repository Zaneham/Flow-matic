#!/usr/bin/env python3
"""
FLOW-MATIC Program Runner
=========================
Execute authentic FLOW-MATIC programs from .flowmatic source files.

Usage:
    python run_flowmatic.py examples/invoice_generator.flowmatic
    python run_flowmatic.py examples/payroll.flowmatic
    python run_flowmatic.py --demo  # Run all demos with sample data

Based on: U1518 FLOW-MATIC Programming System (1958)
"""

import sys
import os
import json
import random
from pathlib import Path
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from flowmatic_parser import FlowMaticInterpreter


def generate_shuffled_deck():
    """Generate a shuffled deck of cards for UNIVAC 21"""
    suits = ['HEARTS', 'DIAMONDS', 'CLUBS', 'SPADES']
    cards = []
    
    for suit in suits:
        # Number cards
        for num in range(2, 11):
            name = f'{["TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE","TEN"][num-2]} OF {suit}'
            cards.append({'CARD-NAME': name, 'CARD-VALUE': num})
        # Face cards
        cards.append({'CARD-NAME': f'JACK OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'QUEEN OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'KING OF {suit}', 'CARD-VALUE': 10})
        cards.append({'CARD-NAME': f'ACE OF {suit}', 'CARD-VALUE': 11})
    
    random.shuffle(cards)
    return cards


def load_sample_data(program_name: str) -> dict:
    """Load sample data for a specific program"""
    
    sample_data = {
        'invoice_generator': {
            'A': [  # CUSTOMER-ORDERS
                {'CUSTOMER-NO': 'C001', 'CUSTOMER-NAME': 'ACME CORP', 'ORDER-NO': 'ORD001', 
                 'PRODUCT-NO': 'P001', 'QUANTITY': 10, 'ORDER-DATE': '1957-06-15'},
                {'CUSTOMER-NO': 'C001', 'CUSTOMER-NAME': 'ACME CORP', 'ORDER-NO': 'ORD001', 
                 'PRODUCT-NO': 'P002', 'QUANTITY': 5, 'ORDER-DATE': '1957-06-15'},
                {'CUSTOMER-NO': 'C002', 'CUSTOMER-NAME': 'CONSOLIDATED INC', 'ORDER-NO': 'ORD002', 
                 'PRODUCT-NO': 'P001', 'QUANTITY': 20, 'ORDER-DATE': '1957-06-16'},
                {'CUSTOMER-NO': 'C002', 'CUSTOMER-NAME': 'CONSOLIDATED INC', 'ORDER-NO': 'ORD002', 
                 'PRODUCT-NO': 'P003', 'QUANTITY': 3, 'ORDER-DATE': '1957-06-16'},
            ],
            'B': [  # PRODUCT-CATALOG
                {'PRODUCT-NO': 'P001', 'PRODUCT-DESC': 'UNIVAC RIBBON', 'UNIT-PRICE': Decimal('12.50'), 'TAX-RATE': Decimal('0.05')},
                {'PRODUCT-NO': 'P002', 'PRODUCT-DESC': 'PUNCH CARDS 1000', 'UNIT-PRICE': Decimal('8.75'), 'TAX-RATE': Decimal('0.05')},
                {'PRODUCT-NO': 'P003', 'PRODUCT-DESC': 'MAGNETIC TAPE', 'UNIT-PRICE': Decimal('45.00'), 'TAX-RATE': Decimal('0.05')},
                {'PRODUCT-NO': 'P004', 'PRODUCT-DESC': 'PAPER ROLL', 'UNIT-PRICE': Decimal('3.25'), 'TAX-RATE': Decimal('0.05')},
            ],
        },
        'payroll': {
            'A': [  # EMPLOYEE-MASTER
                {'EMPLOYEE-NO': 'E001', 'EMPLOYEE-NAME': 'GRACE HOPPER', 'HOURLY-RATE': Decimal('15.00'), 
                 'TAX-RATE': Decimal('0.20'), 'INSURANCE-RATE': Decimal('0.05')},
                {'EMPLOYEE-NO': 'E002', 'EMPLOYEE-NAME': 'JEAN SAMMET', 'HOURLY-RATE': Decimal('12.50'),
                 'TAX-RATE': Decimal('0.18'), 'INSURANCE-RATE': Decimal('0.05')},
                {'EMPLOYEE-NO': 'E003', 'EMPLOYEE-NAME': 'BETTY HOLBERTON', 'HOURLY-RATE': Decimal('14.00'),
                 'TAX-RATE': Decimal('0.19'), 'INSURANCE-RATE': Decimal('0.05')},
            ],
            'B': [  # TIME-CARDS
                {'EMPLOYEE-NO': 'E001', 'HOURS-WORKED': 45},  # Overtime!
                {'EMPLOYEE-NO': 'E002', 'HOURS-WORKED': 40},
                {'EMPLOYEE-NO': 'E003', 'HOURS-WORKED': 38},
            ],
        },
        'inventory_reorder': {
            'A': [  # INVENTORY-FILE
                {'PRODUCT-NO': 'P001', 'PRODUCT-DESC': 'UNIVAC RIBBON', 'QUANTITY-ON-HAND': 5,
                 'REORDER-POINT': 10, 'REORDER-QUANTITY': 50, 'UNIT-COST': Decimal('8.00'), 'VENDOR-CODE': 'V001'},
                {'PRODUCT-NO': 'P002', 'PRODUCT-DESC': 'PUNCH CARDS', 'QUANTITY-ON-HAND': 100,
                 'REORDER-POINT': 50, 'REORDER-QUANTITY': 500, 'UNIT-COST': Decimal('5.00'), 'VENDOR-CODE': 'V002'},
                {'PRODUCT-NO': 'P003', 'PRODUCT-DESC': 'MAGNETIC TAPE', 'QUANTITY-ON-HAND': 2,
                 'REORDER-POINT': 5, 'REORDER-QUANTITY': 20, 'UNIT-COST': Decimal('30.00'), 'VENDOR-CODE': 'V001'},
            ],
            'B': [  # VENDOR-FILE
                {'VENDOR-NO': 'V001', 'VENDOR-NAME': 'REMINGTON RAND', 'VENDOR-ADDRESS': 'NEW YORK NY'},
                {'VENDOR-NO': 'V002', 'VENDOR-NAME': 'IBM SUPPLIES', 'VENDOR-ADDRESS': 'ARMONK NY'},
            ],
        },
        'set_operation_demo': {
            'A': [  # TRANSACTIONS
                {'ACCOUNT-NO': 'A001', 'AMOUNT': Decimal('100.00'), 'TRANS-TYPE': 'DEPOSIT'},
                {'ACCOUNT-NO': 'A002', 'AMOUNT': Decimal('500.00'), 'TRANS-TYPE': 'DEPOSIT'},
                {'ACCOUNT-NO': 'A003', 'AMOUNT': Decimal('1000.00'), 'TRANS-TYPE': 'DEPOSIT'},
                {'ACCOUNT-NO': 'A001', 'AMOUNT': Decimal('50.00'), 'TRANS-TYPE': 'WITHDRAWAL'},
            ],
            'B': [  # ACCOUNT-TYPES
                {'ACCOUNT-NO': 'A001', 'ACCOUNT-TYPE': 'CHECKING'},
                {'ACCOUNT-NO': 'A002', 'ACCOUNT-TYPE': 'SAVINGS'},
                {'ACCOUNT-NO': 'A003', 'ACCOUNT-TYPE': 'INVESTMENT'},
            ],
        },
        'xi_sections_demo': {
            'A': [  # CALCULATION-INPUT
                {'VALUE-A': Decimal('10'), 'VALUE-B': Decimal('5'), 'VALUE-C': Decimal('3'), 
                 'FACTOR': Decimal('2'), 'INDEX-KEY': 'K1'},
                {'VALUE-A': Decimal('20'), 'VALUE-B': Decimal('3'), 'VALUE-C': Decimal('7'),
                 'FACTOR': Decimal('1.5'), 'INDEX-KEY': 'K2'},
                {'VALUE-A': Decimal('15'), 'VALUE-B': Decimal('4'), 'VALUE-C': Decimal('2'),
                 'FACTOR': Decimal('3'), 'INDEX-KEY': 'K1'},
            ],
            'B': [  # LOOKUP-TABLE
                {'TABLE-KEY': 'K1', 'TABLE-FACTOR': Decimal('1.1')},
                {'TABLE-KEY': 'K2', 'TABLE-FACTOR': Decimal('1.2')},
            ],
        },
        'block_integrity': {
            'A': [  # MASTER-FILE with integrity fields
                {'MASTER-KEY': 'M001', 'DATA-VALUE': 'RECORD ONE', 'CHECKSUM-FIELD': 12345,
                 'COMPUTED-CHECKSUM': 12345, 'RECORD-SENTINEL': 0},
                {'MASTER-KEY': 'M002', 'DATA-VALUE': 'RECORD TWO', 'CHECKSUM-FIELD': 23456,
                 'COMPUTED-CHECKSUM': 23456, 'RECORD-SENTINEL': 0},
                {'MASTER-KEY': 'M003', 'DATA-VALUE': 'BAD RECORD', 'CHECKSUM-FIELD': 99999,
                 'COMPUTED-CHECKSUM': 11111, 'RECORD-SENTINEL': 0},  # Integrity error!
                {'MASTER-KEY': 'M004', 'DATA-VALUE': 'RECORD FOUR', 'CHECKSUM-FIELD': 34567,
                 'COMPUTED-CHECKSUM': 34567, 'RECORD-SENTINEL': 0},
                {'MASTER-KEY': 'END', 'DATA-VALUE': '', 'CHECKSUM-FIELD': 0,
                 'COMPUTED-CHECKSUM': 0, 'RECORD-SENTINEL': 999999, 'EXPECTED-COUNT': 4},
            ],
            'B': [  # TRANSACTION-FILE
                {'TRANS-KEY': 'M001', 'UPDATE-VALUE': 'UPDATED'},
                {'TRANS-KEY': 'M002', 'UPDATE-VALUE': 'MODIFIED'},
            ],
        },
        'univac_21': {
            'A': generate_shuffled_deck(),  # CARD-DECK - Freshly shuffled!
        },
    }
    
    # Try to match program name
    for key in sample_data:
        if key in program_name.lower():
            return sample_data[key]
    
    return {}


def run_flowmatic_program(source_path: str, debug: bool = False) -> dict:
    """
    Run a FLOW-MATIC program from a .flowmatic source file
    
    Args:
        source_path: Path to the .flowmatic file
        debug: Enable debug output
        
    Returns:
        Dictionary with output files and printer output
    """
    source_path = Path(source_path)
    
    if not source_path.exists():
        print(f"Error: File not found: {source_path}")
        return {}
    
    # Read the source file
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Create interpreter
    interpreter = FlowMaticInterpreter(debug=debug)
    
    # Load the program
    print(f"\n{'='*70}")
    print(f"FLOW-MATIC PROGRAM: {source_path.name}")
    print(f"{'='*70}")
    
    interpreter.load_program(source_code)
    
    # Load sample data based on program name
    program_name = source_path.stem
    sample_data = load_sample_data(program_name)
    
    if sample_data:
        print(f"\nLoading sample data for: {program_name}")
        for alias, records in sample_data.items():
            interpreter.load_file(alias, records)
            print(f"  File {alias}: {len(records)} records")
    else:
        print(f"\nNo sample data found for: {program_name}")
        print("Program will run with empty files.")
    
    # Run the program
    print(f"\n{'-'*70}")
    print("EXECUTION OUTPUT:")
    print(f"{'-'*70}")
    
    interpreter.run()
    
    # Collect results
    results = {
        'output_files': {},
        'printer_output': interpreter.get_printer_output()
    }
    
    # Get all output files
    for alias, file in interpreter.files.items():
        if file.mode in ('OUTPUT', 'HSP'):
            results['output_files'][alias] = interpreter.get_output(alias)
    
    # Print results
    print(f"\n{'-'*70}")
    print("HIGH-SPEED PRINTER OUTPUT:")
    print(f"{'-'*70}")
    
    if results['printer_output']:
        for line in results['printer_output']:
            print(f"  {line}")
    else:
        print("  (no printer output)")
    
    print(f"\n{'-'*70}")
    print("OUTPUT FILES:")
    print(f"{'-'*70}")
    
    for alias, records in results['output_files'].items():
        print(f"\n  FILE {alias}: {len(records)} records")
        for i, record in enumerate(records[:5]):  # Show first 5
            # Format record nicely
            fields = []
            for k, v in record.items():
                if isinstance(v, Decimal):
                    fields.append(f"{k}={v:.2f}")
                else:
                    fields.append(f"{k}={v}")
            print(f"    [{i+1}] {', '.join(fields)}")
        if len(records) > 5:
            print(f"    ... and {len(records) - 5} more records")
    
    print(f"\n{'='*70}")
    print("PROGRAM COMPLETE")
    print(f"{'='*70}\n")
    
    return results


def run_all_demos():
    """Run all FLOW-MATIC demo programs"""
    
    examples_dir = Path(__file__).parent / 'examples'
    
    print("\n" + "="*70)
    print("  FLOW-MATIC DEMONSTRATION SUITE")
    print("  Based on U1518 FLOW-MATIC Programming System (1958)")
    print("  Remington Rand UNIVAC - Grace Hopper's Legacy")
    print("="*70)
    
    # List of demos in order
    demos = [
        'invoice_generator.flowmatic',
        'payroll.flowmatic',
        'inventory_reorder.flowmatic',
        'set_operation_demo.flowmatic',
        'xi_sections_demo.flowmatic',
        'block_integrity.flowmatic',
    ]
    
    for demo in demos:
        demo_path = examples_dir / demo
        if demo_path.exists():
            input(f"\nPress Enter to run: {demo} ")
            run_flowmatic_program(str(demo_path), debug=False)
        else:
            print(f"\nSkipping (not found): {demo}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='FLOW-MATIC Program Runner - Execute authentic 1957 programs',
        epilog='Based on U1518 FLOW-MATIC Programming System (Remington Rand, 1958)'
    )
    parser.add_argument('source', nargs='?', help='Path to .flowmatic source file')
    parser.add_argument('--demo', action='store_true', help='Run all demo programs')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--list', action='store_true', help='List available examples')
    
    args = parser.parse_args()
    
    if args.list:
        examples_dir = Path(__file__).parent / 'examples'
        print("\nAvailable FLOW-MATIC examples:")
        for f in sorted(examples_dir.glob('*.flowmatic')):
            print(f"  {f.name}")
        return
    
    if args.demo:
        run_all_demos()
        return
    
    if args.source:
        run_flowmatic_program(args.source, debug=args.debug)
        return
    
    # No arguments - show help
    parser.print_help()
    print("\n\nQuick start:")
    print("  python run_flowmatic.py --demo           # Run all demos")
    print("  python run_flowmatic.py --list           # List examples")
    print("  python run_flowmatic.py examples/invoice_generator.flowmatic")


if __name__ == '__main__':
    main()

