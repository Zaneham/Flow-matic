"""
FLOW-MATIC Programming Language Interpreter
============================================

A faithful recreation of Grace Hopper's FLOW-MATIC (1957),
the first English-like business programming language.

Part of The Ian Index.

Example usage:
    from flowmatic import FlowMaticInterpreter
    
    interpreter = FlowMaticInterpreter()
    interpreter.load_program("examples/invoice_generator.flowmatic")
    interpreter.run()
"""

__version__ = "1.0.0"
__author__ = "The Ian Index"
__all__ = ["FlowMaticInterpreter", "run_program", "run_file"]

from .parser import FlowMaticInterpreter


def run_program(source: str, input_files: dict = None) -> dict:
    """
    Run a FLOW-MATIC program from source code.
    
    Args:
        source: FLOW-MATIC source code as a string
        input_files: Optional dict mapping file letters to list of records
        
    Returns:
        dict with output files, printer output, and execution stats
    """
    interpreter = FlowMaticInterpreter()
    interpreter.parse(source)
    
    if input_files:
        for letter, records in input_files.items():
            interpreter.load_input_file(letter, records)
    
    interpreter.run()
    
    return {
        "output_files": interpreter.get_output_files(),
        "printer": interpreter.get_printer_output(),
        "stats": {
            "operations_executed": interpreter.operation_count,
        }
    }


def run_file(filepath: str, input_files: dict = None) -> dict:
    """
    Run a FLOW-MATIC program from a file.
    
    Args:
        filepath: Path to .flowmatic file
        input_files: Optional dict mapping file letters to list of records
        
    Returns:
        dict with output files, printer output, and execution stats
    """
    with open(filepath, 'r') as f:
        source = f.read()
    return run_program(source, input_files)

