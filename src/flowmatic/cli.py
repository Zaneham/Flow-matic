"""
FLOW-MATIC Command Line Interface
=================================

Run FLOW-MATIC programs from the command line.

Usage:
    flowmatic program.flowmatic
    flowmatic --demo
    flowmatic --list
    flowmatic --help
"""

import argparse
import sys
import os
import json
from pathlib import Path

from .parser import FlowMaticInterpreter


def get_examples_dir() -> Path:
    """Get path to examples directory."""
    # Check if running from package or source
    package_dir = Path(__file__).parent
    examples_dir = package_dir / "examples"
    if examples_dir.exists():
        return examples_dir
    
    # Try relative to working directory
    if Path("examples").exists():
        return Path("examples")
    
    return None


def list_examples():
    """List available example programs."""
    examples_dir = get_examples_dir()
    if not examples_dir:
        print("Examples directory not found.")
        return
    
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║        FLOW-MATIC Example Programs - The Ian Index            ║")
    print("╠════════════════════════════════════════════════════════════════╣")
    
    examples = sorted(examples_dir.glob("*.flowmatic"))
    for ex in examples:
        name = ex.stem.replace("_", " ").title()
        print(f"║  • {name:<56} ║")
    
    print("╚════════════════════════════════════════════════════════════════╝")
    print(f"\nRun with: flowmatic examples/{examples[0].name}" if examples else "")


def run_demo():
    """Run demonstration of all example programs."""
    examples_dir = get_examples_dir()
    if not examples_dir:
        print("Examples directory not found.")
        return
    
    print("\n" + "="*70)
    print("  FLOW-MATIC Demonstration - The Ian Index")
    print("  Grace Hopper's Business Language (1957)")
    print("="*70)
    
    for example_file in sorted(examples_dir.glob("*.flowmatic")):
        print(f"\n{'─'*70}")
        print(f"  Running: {example_file.name}")
        print(f"{'─'*70}\n")
        
        try:
            interpreter = FlowMaticInterpreter()
            interpreter.load_program(str(example_file))
            interpreter.run()
            
            # Show printer output
            printer = interpreter.get_printer_output()
            if printer:
                for line in printer[:10]:  # First 10 lines
                    print(f"  {line}")
                if len(printer) > 10:
                    print(f"  ... ({len(printer) - 10} more lines)")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n{'='*70}")
    print("  Demo complete!")
    print("="*70)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="flowmatic",
        description="FLOW-MATIC Interpreter - Grace Hopper's 1957 Business Language",
        epilog="Part of The Ian Index - https://github.com/Zaneham/Flow-matic"
    )
    
    parser.add_argument(
        "program",
        nargs="?",
        help="Path to .flowmatic program file"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run all example programs"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available example programs"
    )
    parser.add_argument(
        "--input", "-i",
        help="JSON file with input data"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed execution output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0 - The Ian Index"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_examples()
        return 0
    
    if args.demo:
        run_demo()
        return 0
    
    if not args.program:
        parser.print_help()
        return 1
    
    # Run specified program
    if not os.path.exists(args.program):
        print(f"Error: File not found: {args.program}")
        return 1
    
    try:
        interpreter = FlowMaticInterpreter()
        interpreter.load_program(args.program)
        
        # Load input data if provided
        if args.input:
            with open(args.input, 'r') as f:
                input_data = json.load(f)
            for letter, records in input_data.get("files", {}).items():
                interpreter.load_input_file(letter.upper(), records)
        
        if args.verbose:
            print(f"\n{'='*60}")
            print(f"  FLOW-MATIC: {os.path.basename(args.program)}")
            print(f"{'='*60}\n")
        
        interpreter.run()
        
        # Show output
        printer = interpreter.get_printer_output()
        if printer:
            for line in printer:
                print(line)
        
        outputs = interpreter.get_output_files()
        if outputs and args.verbose:
            print(f"\n{'─'*60}")
            print("  Output Files:")
            for letter, records in outputs.items():
                print(f"    File {letter}: {len(records)} records")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

