#!/usr/bin/env python3
"""
FLOW-MATIC Test Runner
======================
Runs all test cases and compares output with expected results.

Similar to the Plankalkül test runner structure.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py 01           # Run specific test
    python run_tests.py --verbose    # Verbose output
"""

import sys
import json
import glob
from pathlib import Path
from decimal import Decimal

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowmatic_parser import FlowMaticInterpreter


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def normalize_record(record: dict) -> dict:
    """Normalize a record for comparison"""
    normalized = {}
    for key, value in record.items():
        # Normalize key
        norm_key = key.upper().replace('_', '-')
        
        # Normalize value
        if isinstance(value, Decimal):
            norm_value = float(value)
        elif isinstance(value, float):
            norm_value = round(value, 2)
        else:
            norm_value = value
        
        normalized[norm_key] = norm_value
    
    return normalized


def compare_outputs(actual: list, expected: list) -> tuple:
    """
    Compare actual output with expected.
    Returns (success, message)
    """
    if len(actual) != len(expected):
        return False, f"Record count mismatch: got {len(actual)}, expected {len(expected)}"
    
    for i, (act, exp) in enumerate(zip(actual, expected)):
        act_norm = normalize_record(act)
        exp_norm = normalize_record(exp)
        
        # Check all expected fields are present and match
        for key, exp_val in exp_norm.items():
            if key not in act_norm:
                return False, f"Record {i+1}: Missing field {key}"
            
            act_val = act_norm[key]
            
            # Compare with tolerance for floats
            if isinstance(exp_val, float) and isinstance(act_val, (int, float, Decimal)):
                if abs(float(act_val) - exp_val) > 0.01:
                    return False, f"Record {i+1}: Field {key} = {act_val}, expected {exp_val}"
            elif act_val != exp_val:
                return False, f"Record {i+1}: Field {key} = {act_val}, expected {exp_val}"
    
    return True, "OK"


def run_test(test_path: Path, verbose: bool = False) -> bool:
    """
    Run a single test case.
    
    Args:
        test_path: Path to .flowmatic test file
        verbose: Print detailed output
        
    Returns:
        True if test passed
    """
    test_name = test_path.stem
    
    # Find input and expected files
    input_path = test_path.with_suffix('.input.json')
    expected_path = test_path.with_suffix('.expected.json')
    
    if not input_path.exists():
        print(f"  SKIP {test_name}: No input file")
        return True
    
    if not expected_path.exists():
        print(f"  SKIP {test_name}: No expected file")
        return True
    
    # Load files
    with open(test_path, 'r') as f:
        source = f.read()
    
    with open(input_path, 'r') as f:
        input_data = json.load(f)
    
    with open(expected_path, 'r') as f:
        expected_data = json.load(f)
    
    # Run the interpreter
    try:
        interpreter = FlowMaticInterpreter(debug=False)
        interpreter.load_program(source)
        
        # Load input files
        for alias, records in input_data.items():
            interpreter.load_file(alias, records)
        
        interpreter.run()
        
        # Compare outputs
        all_passed = True
        messages = []
        
        for alias, expected_records in expected_data.items():
            if alias == '_printer':
                # Check printer output
                actual_printer = interpreter.get_printer_output()
                if actual_printer != expected_records:
                    all_passed = False
                    messages.append(f"Printer: Output mismatch")
                elif verbose:
                    messages.append(f"Printer: OK ({len(actual_printer)} lines)")
            else:
                actual_records = interpreter.get_output(alias)
                success, msg = compare_outputs(actual_records, expected_records)
                
                if not success:
                    all_passed = False
                    messages.append(f"File {alias}: {msg}")
                elif verbose:
                    messages.append(f"File {alias}: OK ({len(actual_records)} records)")
        
        if all_passed:
            print(f"  PASS {test_name}")
            if verbose:
                for msg in messages:
                    print(f"       {msg}")
            return True
        else:
            print(f"  FAIL {test_name}")
            for msg in messages:
                print(f"       {msg}")
            return False
            
    except Exception as e:
        print(f"  ERROR {test_name}: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FLOW-MATIC Test Runner')
    parser.add_argument('filter', nargs='?', help='Test name filter')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Find test directory
    test_dir = Path(__file__).parent
    
    # Find all test files
    test_files = sorted(test_dir.glob('*.flowmatic'))
    
    if args.filter:
        test_files = [t for t in test_files if args.filter in t.stem]
    
    if not test_files:
        print("No test files found")
        return 1
    
    print("\n" + "="*60)
    print("  FLOW-MATIC TEST SUITE")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test(test_file, args.verbose):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*60)
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("-"*60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

