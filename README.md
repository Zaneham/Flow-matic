# FLOW-MATIC: Grace Hopper's Business Language (1957)

[![PyPI version](https://badge.fury.io/py/ian-flowmatic.svg)](https://badge.fury.io/py/ian-flowmatic)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *"It is much easier for most people to write an English statement than it is to use symbols."*
> — Grace Hopper, 1952

**Part of [The Ian Index](https://github.com/Zaneham/Flow-matic) coming soon** — Preserving computing history.
pip install ian-flowmatic

## What is FLOW-MATIC?

FLOW-MATIC was the **first English-like programming language**, developed by Grace Hopper and her team at Remington Rand from 1955-1959. It ran on the UNIVAC I and UNIVAC II computers and was the direct ancestor of COBOL.

This implementation faithfully recreates FLOW-MATIC's syntax and semantics based on the original **U1518 FLOW-MATIC Programming System** manual (1958).

## Installation

```bash
pip install ian-flowmatic
```

## Quick Start

```bash
# Run a program
flowmatic examples/invoice_generator.flowmatic

# Run all demos
flowmatic --demo

# List available examples
flowmatic --list

# Or use Python directly
python -c "from flowmatic import run_file; run_file('program.flowmatic')"
```

## Example Programs

| Program | Description |
|---------|-------------|
| `invoice_generator.flowmatic` | Generates invoices by matching orders with product catalog |
| `payroll.flowmatic` | Calculates employee pay with overtime and deductions |
| `inventory_reorder.flowmatic` | Checks stock levels and generates purchase orders |
| `set_operation_demo.flowmatic` | Demonstrates runtime flow modification (feature COBOL killed!) |
| `xi_sections_demo.flowmatic` | Shows X-I machine code sections (another lost feature) |
| `block_integrity.flowmatic` | Language-level data integrity checking |

## FLOW-MATIC Syntax

### File Definitions (Operation 0)

```
(0)  INPUT INVENTORY FILE-A PRICE-LIST FILE-B ;
     OUTPUT INVOICE FILE-C ;
     HSP D .
```

- `INPUT` - Define input files with single-letter aliases
- `OUTPUT` - Define output files
- `HSP` - High-Speed Printer output

### Operations

Each operation is numbered and contains statements:

```
(1)  READ-ITEM A ;
     IF END OF DATA GO TO OPERATION 10 .

(2)  COMPARE PRODUCT-NO (A) WITH PRODUCT-NO (B) ;
     IF EQUAL GO TO OPERATION 4 ;
     IF LESS GO TO OPERATION 3 ;
     OTHERWISE GO TO OPERATION 5 .
```

### Available Statements

| Statement | Description |
|-----------|-------------|
| `READ-ITEM A` | Read next record from file A |
| `WRITE-ITEM C` | Write current record to file C |
| `PRINT-ITEM D` | Print to high-speed printer |
| `TRANSFER A TO C` | Copy entire record from A to C |
| `MOVE value TO field (C)` | Move value to a field |
| `COMPARE field (A) WITH field (B)` | Compare two fields |
| `IF EQUAL GO TO OPERATION n` | Conditional jump |
| `IF GREATER GO TO OPERATION n` | Conditional jump |
| `IF LESS GO TO OPERATION n` | Conditional jump |
| `OTHERWISE GO TO OPERATION n` | Default branch |
| `JUMP TO OPERATION n` | Unconditional jump |
| `IF END OF DATA GO TO OPERATION n` | End-of-file check |
| `MULTIPLY a BY b GIVING c` | Multiplication |
| `ADD a TO b` | Addition |
| `SUBTRACT a FROM b` | Subtraction |
| `DIVIDE a BY b GIVING c` | Division |
| `SET OPERATION n TO GO TO OPERATION m` | **Runtime flow modification!** |
| `TEST field AGAINST value` | Test a field value |
| `EXECUTE OPERATION n [THROUGH m]` | **Subroutine call!** (from U1518) |
| `REWIND A` | Rewind file for multi-pass (from U1518) |
| `CLOSE-OUT FILES C` | Close output files |
| `STOP` | End program |

## Features COBOL Killed

### 1. SET OPERATION (Runtime Flow Modification)

FLOW-MATIC:
```
SET OPERATION 9 TO GO TO OPERATION 2
```

This **one English sentence** changes where operation 9 jumps to at runtime.

Modern equivalent requires:
- Interface definition
- Concrete strategy classes
- Context class
- Factory or dependency injection

COBOL had `ALTER` which did something similar, but it was deprecated and removed.

### 2. X-I Sections (Inline Machine Code)

FLOW-MATIC allowed embedding machine code for performance-critical sections:

```
* In original FLOW-MATIC:
X-I  A000  ; Load from input area
X-I  M010  ; Multiply instruction
X-I  W000  ; Store to working storage
```

The relative addressing (A000, W000, M000) kept code portable between UNIVAC models.

COBOL removed this to achieve "machine independence" — creating a **39-year gap** before FFI/JNI/ctypes reinvented the concept in 1996.

### 3. Single-Letter File Aliases

FLOW-MATIC:
```
COMPARE PRODUCT-NO (A) WITH PRODUCT-NO (B)
TRANSFER A TO C
```

COBOL:
```
COMPARE PRODUCT-NUMBER OF INVENTORY-MASTER-FILE
    WITH PRODUCT-NUMBER OF PRICE-LIST-FILE
MOVE CORRESPONDING INVENTORY-MASTER-RECORD
    TO OUTPUT-INVOICE-RECORD
```

**18 FLOW-MATIC operations became 50+ COBOL statements.**

### 4. EXECUTE (Subroutine Mechanism!)

From U1518 page 92: *"Performs designated operation or sequence of operations."*

```
(5)  EXECUTE OPERATION 10 THROUGH OPERATION 12 .
```

This runs operations 10-12 as a subroutine, then **returns** to operation 6!
A primitive but effective subroutine mechanism in 1958.

### 5. REWIND (Multi-Pass Processing)

From U1518 page 97: *"Rewinds current reel of an input file."*

```
(4)  REWIND A .
(5)  READ-ITEM A ; ...
```

This resets file A to the beginning, allowing multi-pass algorithms.

### 6. Language-Level Integrity Checking

FLOW-MATIC file definitions included:
```
BLK CT IND 000000000001   ; Enable block counting
BLK CT LOC 000000000001   ; Where count stored
END REEL SEN              ; End-of-reel sentinel
END FILE SEN              ; End-of-file sentinel
```

The **language** verified your data automatically. We now need external checksums, database transaction logs, and ETL validation code.

## Historical Context

- **1955**: Grace Hopper begins development of FLOW-MATIC
- **1957**: FLOW-MATIC operational on UNIVAC I
- **1958**: U1518 manual published
- **1959**: CODASYL committee formed (includes Hopper)
- **1960**: COBOL released, based heavily on FLOW-MATIC
- **1960+**: FLOW-MATIC features gradually dropped from COBOL

## Project Structure

```
flowmatic/
├── README.md                    # This file
├── flowmatic_parser.py          # FLOW-MATIC interpreter (recursive descent)
├── run_flowmatic.py             # Command-line runner
├── demo.py                      # Quick demonstration
├── play_21.py                   # Interactive UNIVAC 21 card game
├── src/
│   ├── flowmatic.gram           # Formal BNF grammar
│   └── ast_nodes.py             # AST node classes
├── tests/
│   ├── run_tests.py             # Test runner
│   ├── 01_simple_transfer.flowmatic
│   ├── 02_arithmetic.flowmatic
│   ├── 03_compare_match.flowmatic
│   └── 04_set_operation.flowmatic
└── examples/
    ├── invoice_generator.flowmatic
    ├── payroll.flowmatic
    ├── inventory_reorder.flowmatic
    ├── set_operation_demo.flowmatic
    ├── xi_sections_demo.flowmatic
    ├── block_integrity.flowmatic
    └── univac_21.flowmatic      # Card game in authentic FLOW-MATIC
```

## Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Run specific test
python tests/run_tests.py 01
```

## Grammar

The formal grammar is defined in `src/flowmatic.gram`. Key production rules:

```
Program         ::= Operation0 { Operation }
Operation       ::= '(' NUMBER ')' StatementList '.'
Statement       ::= ReadItem | WriteItem | Compare | IfCondition | Jump | Transfer | ...
FieldRef        ::= IDENTIFIER '(' LETTER ')'
```

## Implementation Notes

### Parser
The interpreter uses a recursive descent parser, following the same pattern as the 
Plankalkül implementation in this repository. Each statement type has a corresponding
regex pattern that matches the statement and extracts its components.

### Execution Model
FLOW-MATIC uses a **memory-changing model** where:
1. Files are read into current records indexed by single-letter aliases (A, B, C...)
2. Statements modify these records in place
3. Records are written back to output files

### SET OPERATION
The `SET OPERATION` feature stores modified jump targets in `operation_targets` dict.
When a JUMP/GO TO executes, it checks if the current operation has an override target.
This is how FLOW-MATIC achieved runtime polymorphism without objects or functions!

## References

- U1518 FLOW-MATIC Programming System (1958), Remington Rand UNIVAC
- "The Education of a Computer" - Grace Hopper (1952)
- COBOL-60 Report (1960)

## License

Part of the Ian index and Hopper project - Preserving Grace Hopper's Legacy.

---

*"The most dangerous words in the language: 'We have always done it this way.'"*
— Grace Hopper

