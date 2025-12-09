"""
FLOW-MATIC Programming System Parser & Interpreter
===================================================
Based on: U1518 FLOW-MATIC Programming System (1958)
         Remington Rand UNIVAC, developed under Grace Hopper

FLOW-MATIC was the first English-like business programming language (1955-1959).
It was a direct ancestor of COBOL, but had features COBOL dropped:
- X-I machine code sections (inline assembly)
- SET OPERATION (runtime flow modification)  
- Single-letter file aliases (A, B, C)
- Language-level integrity checking

This implementation faithfully recreates FLOW-MATIC's syntax and semantics.

Program Structure (from original manual):
=========================================
(0) COMPUTER section - defines files and outputs
    INPUT <file-name> FILE-<letter> ; 
    OUTPUT <file-name> FILE-<letter> ;
    HSP <letter> .  (High-Speed Printer)
    
(1-n) OPERATION sections - procedural statements
    READ-ITEM <letter>
    WRITE-ITEM <letter>
    COMPARE <field> (<letter>) WITH <field> (<letter>)
    IF EQUAL GO TO OPERATION <n>
    IF GREATER GO TO OPERATION <n>
    IF LESS GO TO OPERATION <n>
    OTHERWISE GO TO OPERATION <n>
    TRANSFER <letter> TO <letter>
    MOVE <value> TO <field> (<letter>)
    ADD <field> TO <field>
    SUBTRACT <field> FROM <field>
    MULTIPLY <field> BY <field> GIVING <field>
    DIVIDE <field> BY <field> GIVING <field>
    SET OPERATION <n> TO GO TO OPERATION <m>
    JUMP TO OPERATION <n>
    IF END OF DATA GO TO OPERATION <n>
    CLOSE-OUT FILES <letters>
    STOP

Author: Hopper Project
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import datetime


class FlowMaticDataType(Enum):
    """FLOW-MATIC data types"""
    NUMERIC = "numeric"      # Numbers (amount, quantity, price)
    ALPHABETIC = "alpha"     # Text strings
    ALPHANUMERIC = "alphanum"  # Mixed


@dataclass
class FlowMaticField:
    """A field within a record"""
    name: str
    data_type: FlowMaticDataType
    length: int
    decimals: int = 0
    value: Any = None


@dataclass
class FlowMaticRecord:
    """A record (line) from a file"""
    fields: Dict[str, FlowMaticField] = field(default_factory=dict)
    
    def get(self, field_name: str) -> Any:
        """Get field value"""
        if field_name in self.fields:
            return self.fields[field_name].value
        return None
    
    def set(self, field_name: str, value: Any):
        """Set field value"""
        if field_name in self.fields:
            self.fields[field_name].value = value
        else:
            # Create field on-the-fly
            self.fields[field_name] = FlowMaticField(
                name=field_name,
                data_type=FlowMaticDataType.ALPHANUMERIC,
                length=50,
                value=value
            )


@dataclass  
class FlowMaticFile:
    """Represents a FLOW-MATIC file with single-letter alias"""
    name: str
    alias: str  # Single letter: A, B, C, etc.
    mode: str   # INPUT, OUTPUT, HSP (High-Speed Printer)
    records: List[FlowMaticRecord] = field(default_factory=list)
    current_record: int = 0
    is_eof: bool = False
    is_open: bool = False
    
    # Integrity checking fields (from original manual page 39)
    block_count_enabled: bool = False
    block_count: int = 0
    end_reel_sentinel: Optional[str] = None
    end_file_sentinel: Optional[str] = None


@dataclass
class FlowMaticOperation:
    """A single operation (numbered statement block)"""
    number: int
    statements: List[str]
    jump_target: Optional[int] = None  # For SET OPERATION modification


class FlowMaticInterpreter:
    """
    FLOW-MATIC Interpreter
    
    Executes authentic FLOW-MATIC programs from the 1957-1959 era.
    Based on U1518 FLOW-MATIC Programming System manual.
    
    Usage:
        interpreter = FlowMaticInterpreter()
        interpreter.load_program(flowmatic_source)
        interpreter.load_file('A', records)  # Load data for file alias A
        interpreter.run()
        output = interpreter.get_output('C')  # Get output file C
    """
    
    def __init__(self, debug: bool = False):
        self.files: Dict[str, FlowMaticFile] = {}  # Keyed by alias (A, B, C)
        self.operations: Dict[int, FlowMaticOperation] = {}
        self.current_operation: int = 1
        self.running: bool = False
        self.debug: bool = debug
        self.output_buffer: List[str] = []  # HSP (High-Speed Printer) output
        
        # Operation targets - can be modified by SET OPERATION
        self.operation_targets: Dict[int, int] = {}
        
        # Comparison result from last COMPARE
        self.comparison_result: Optional[str] = None  # 'EQUAL', 'GREATER', 'LESS'
        
        # Current record buffers for each file alias
        self.current_records: Dict[str, FlowMaticRecord] = {}
        
        # Track last read file for EOF detection
        self.last_read_file: Optional[str] = None
        self.last_read_eof: bool = False
        
    def load_program(self, source: str) -> bool:
        """
        Parse and load a FLOW-MATIC program
        
        Returns True if successful
        """
        self.operations.clear()
        self.files.clear()
        
        # Normalize line endings and remove comments
        lines = source.replace('\r\n', '\n').split('\n')
        lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('*')]
        
        # Join into single string for parsing
        program_text = ' '.join(lines)
        
        # Parse operations - format: (n) statements .
        # Operation 0 is special: file definitions
        op_pattern = r'\((\d+)\)\s*(.+?)(?=\(\d+\)|$)'
        matches = re.findall(op_pattern, program_text, re.DOTALL)
        
        for op_num_str, op_body in matches:
            op_num = int(op_num_str)
            
            # Split by period (statement terminator) and semicolon (continuation)
            # Clean up the operation body
            op_body = op_body.strip().rstrip('.')
            
            if op_num == 0:
                # Operation 0: File definitions (COMPUTER section)
                self._parse_file_definitions(op_body)
            else:
                # Regular operation
                statements = self._parse_statements(op_body)
                self.operations[op_num] = FlowMaticOperation(
                    number=op_num,
                    statements=statements
                )
        
        if self.debug:
            print(f"Loaded {len(self.operations)} operations")
            print(f"Files defined: {list(self.files.keys())}")
            
        return True
    
    def _parse_file_definitions(self, body: str):
        """Parse operation 0 - file definitions"""
        # INPUT INVENTORY-FILE FILE-A ; PRICE-FILE FILE-B ;
        # OUTPUT INVOICE-FILE FILE-C ;
        # HSP D .
        
        # Split by semicolon
        parts = [p.strip() for p in body.split(';') if p.strip()]
        
        for part in parts:
            part = part.strip().rstrip('.')
            
            # INPUT file-name FILE-letter
            input_match = re.match(r'INPUT\s+(\S+)\s+FILE-([A-Z])', part, re.IGNORECASE)
            if input_match:
                file_name = input_match.group(1)
                alias = input_match.group(2)
                self.files[alias] = FlowMaticFile(
                    name=file_name,
                    alias=alias,
                    mode='INPUT'
                )
                continue
            
            # OUTPUT file-name FILE-letter
            output_match = re.match(r'OUTPUT\s+(\S+)\s+FILE-([A-Z])', part, re.IGNORECASE)
            if output_match:
                file_name = output_match.group(1)
                alias = output_match.group(2)
                self.files[alias] = FlowMaticFile(
                    name=file_name,
                    alias=alias,
                    mode='OUTPUT'
                )
                continue
            
            # HSP letter (High-Speed Printer)
            hsp_match = re.match(r'HSP\s+([A-Z])', part, re.IGNORECASE)
            if hsp_match:
                alias = hsp_match.group(1)
                self.files[alias] = FlowMaticFile(
                    name='HIGH-SPEED-PRINTER',
                    alias=alias,
                    mode='HSP'
                )
                continue
    
    def _parse_statements(self, body: str) -> List[str]:
        """Parse statements within an operation"""
        # Statements are separated by ; or .
        # But . can also be a decimal point in numbers like 1.1
        # So we only split on . when followed by whitespace or end of string
        
        statements = []
        
        # Split by semicolon, or period followed by whitespace/end
        # This preserves decimal numbers like 1.1, 0.05, etc.
        parts = re.split(r';|\.(?=\s|$)', body)
        parts = [p.strip() for p in parts if p.strip()]
        
        for part in parts:
            statements.append(part)
            
        return statements
    
    def load_file(self, alias: str, records: List[Dict[str, Any]]):
        """
        Load data into a file by alias
        
        Args:
            alias: Single letter file alias (A, B, C, etc.)
            records: List of dictionaries with field names and values
        """
        if alias not in self.files:
            # Create the file if not defined
            self.files[alias] = FlowMaticFile(
                name=f'FILE-{alias}',
                alias=alias,
                mode='INPUT'
            )
        
        file = self.files[alias]
        file.records = []
        
        for record_data in records:
            record = FlowMaticRecord()
            for field_name, value in record_data.items():
                # Determine type from value
                if isinstance(value, (int, float, Decimal)):
                    dtype = FlowMaticDataType.NUMERIC
                else:
                    dtype = FlowMaticDataType.ALPHANUMERIC
                    
                record.fields[field_name] = FlowMaticField(
                    name=field_name,
                    data_type=dtype,
                    length=len(str(value)),
                    value=value
                )
            file.records.append(record)
        
        file.current_record = 0
        file.is_eof = len(records) == 0
        file.is_open = True
        
        if self.debug:
            print(f"Loaded {len(records)} records into file {alias}")
    
    def run(self) -> bool:
        """
        Execute the FLOW-MATIC program
        
        Returns True if completed successfully
        """
        self.running = True
        self.current_operation = 1
        max_iterations = 100000  # Prevent infinite loops
        iterations = 0
        
        while self.running and iterations < max_iterations:
            iterations += 1
            
            if self.current_operation not in self.operations:
                if self.debug:
                    print(f"Operation {self.current_operation} not found - stopping")
                break
            
            op = self.operations[self.current_operation]
            
            if self.debug:
                print(f"\n=== Operation {self.current_operation} ===")
            
            # Execute all statements in the operation
            next_op = self.current_operation + 1  # Default: go to next
            jump_performed = False
            
            for stmt in op.statements:
                result = self._execute_statement(stmt)
                
                if result == 'STOP':
                    self.running = False
                    break
                elif isinstance(result, int):
                    # Jump to specific operation - IMMEDIATELY break
                    next_op = result
                    jump_performed = True
                    break  # Critical: stop processing remaining statements!
                elif result == 'CONTINUE':
                    continue
                elif result == 'NEXT':
                    break  # Go to next operation
            
            if not self.running:
                break
                
            self.current_operation = next_op
        
        if self.debug:
            print(f"\nProgram completed in {iterations} iterations")
            
        return True
    
    def _execute_statement(self, stmt: str) -> Any:
        """Execute a single FLOW-MATIC statement"""
        stmt = stmt.strip()
        
        if self.debug:
            print(f"  Executing: {stmt}")
        
        # STOP
        if stmt.upper() == 'STOP':
            return 'STOP'
        
        # READ-ITEM <alias>
        read_match = re.match(r'READ-ITEM\s+([A-Z])', stmt, re.IGNORECASE)
        if read_match:
            return self._exec_read_item(read_match.group(1))
        
        # WRITE-ITEM <alias>
        write_match = re.match(r'WRITE-ITEM\s+([A-Z])', stmt, re.IGNORECASE)
        if write_match:
            return self._exec_write_item(write_match.group(1))
        
        # PUNCH-ITEM <alias> (for card output)
        punch_match = re.match(r'PUNCH-ITEM\s+([A-Z])', stmt, re.IGNORECASE)
        if punch_match:
            return self._exec_write_item(punch_match.group(1))
        
        # PRINT-ITEM <alias> (HSP output)
        print_match = re.match(r'PRINT-ITEM\s+([A-Z])', stmt, re.IGNORECASE)
        if print_match:
            return self._exec_print_item(print_match.group(1))
        
        # IF END OF DATA GO TO OPERATION <n>
        eof_match = re.match(r'IF\s+END\s+OF\s+DATA\s+GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if eof_match:
            return self._exec_if_eof(int(eof_match.group(1)))
        
        # COMPARE <field> (<alias>) WITH <field> (<alias>)
        compare_match = re.match(
            r'COMPARE\s+(\S+)\s*\(([A-Z])\)\s+WITH\s+(\S+)\s*\(([A-Z])\)', 
            stmt, re.IGNORECASE
        )
        if compare_match:
            return self._exec_compare(
                compare_match.group(1), compare_match.group(2),
                compare_match.group(3), compare_match.group(4)
            )
        
        # IF EQUAL GO TO OPERATION <n>
        if_equal_match = re.match(r'IF\s+EQUAL\s+GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if if_equal_match:
            if self.comparison_result == 'EQUAL':
                return int(if_equal_match.group(1))
            return 'CONTINUE'
        
        # IF GREATER GO TO OPERATION <n>
        if_greater_match = re.match(r'IF\s+GREATER\s+GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if if_greater_match:
            if self.comparison_result == 'GREATER':
                return int(if_greater_match.group(1))
            return 'CONTINUE'
        
        # IF LESS GO TO OPERATION <n>
        if_less_match = re.match(r'IF\s+LESS\s+GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if if_less_match:
            if self.comparison_result == 'LESS':
                return int(if_less_match.group(1))
            return 'CONTINUE'
        
        # OTHERWISE GO TO OPERATION <n>
        otherwise_match = re.match(r'OTHERWISE\s+GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if otherwise_match:
            return int(otherwise_match.group(1))
        
        # JUMP TO OPERATION <n>
        jump_match = re.match(r'JUMP\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if jump_match:
            target = int(jump_match.group(1))
            # Check if this operation's target was modified by SET OPERATION
            # This is the feature COBOL killed!
            if self.current_operation in self.operation_targets:
                target = self.operation_targets[self.current_operation]
                if self.debug:
                    print(f"    SET OPERATION override: jumping to {target}")
            return target
        
        # GO TO OPERATION <n>
        goto_match = re.match(r'GO\s+TO\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if goto_match:
            target = int(goto_match.group(1))
            # Check for SET OPERATION override
            if self.current_operation in self.operation_targets:
                target = self.operation_targets[self.current_operation]
                if self.debug:
                    print(f"    SET OPERATION override: jumping to {target}")
            return target
        
        # TRANSFER <alias> TO <alias>
        transfer_match = re.match(r'TRANSFER\s+([A-Z])\s+TO\s+([A-Z])', stmt, re.IGNORECASE)
        if transfer_match:
            return self._exec_transfer(transfer_match.group(1), transfer_match.group(2))
        
        # MOVE <value> TO <field> (<alias>)
        move_match = re.match(r'MOVE\s+(.+?)\s+TO\s+(\S+)\s*\(([A-Z])\)', stmt, re.IGNORECASE)
        if move_match:
            return self._exec_move(move_match.group(1), move_match.group(2), move_match.group(3))
        
        # MULTIPLY <field> (<alias>) BY <field/literal> GIVING <field> (<alias>)
        # The BY operand can be a field reference OR a numeric literal
        mult_match = re.match(
            r'MULTIPLY\s+(\S+)\s*\(([A-Z])\)\s+BY\s+(\S+)\s*(?:\(([A-Z])\))?\s+GIVING\s+(\S+)\s*\(([A-Z])\)',
            stmt, re.IGNORECASE
        )
        if mult_match:
            return self._exec_multiply(
                mult_match.group(1), mult_match.group(2),
                mult_match.group(3), mult_match.group(4),  # group 4 may be None for literals
                mult_match.group(5), mult_match.group(6)
            )
        
        # ADD <field> (<alias>) TO <field> (<alias>) GIVING <field> (<alias>)
        add_giving_match = re.match(
            r'ADD\s+(\S+)\s*\(([A-Z])\)\s+TO\s+(\S+)\s*\(([A-Z])\)\s+GIVING\s+(\S+)\s*\(([A-Z])\)',
            stmt, re.IGNORECASE
        )
        if add_giving_match:
            return self._exec_add_giving(
                add_giving_match.group(1), add_giving_match.group(2),
                add_giving_match.group(3), add_giving_match.group(4),
                add_giving_match.group(5), add_giving_match.group(6)
            )
        
        # ADD <field/literal> TO <field> (<alias>)
        # First operand can be a field reference OR a numeric literal
        add_match = re.match(
            r'ADD\s+(\S+)\s*(?:\(([A-Z])\))?\s+TO\s+(\S+)\s*\(([A-Z])\)',
            stmt, re.IGNORECASE
        )
        if add_match:
            return self._exec_add(
                add_match.group(1), add_match.group(2),  # group 2 may be None for literals
                add_match.group(3), add_match.group(4)
            )
        
        # SUBTRACT <field> (<alias>) FROM <field> (<alias>)
        sub_match = re.match(
            r'SUBTRACT\s+(\S+)\s*\(([A-Z])\)\s+FROM\s+(\S+)\s*\(([A-Z])\)',
            stmt, re.IGNORECASE
        )
        if sub_match:
            return self._exec_subtract(
                sub_match.group(1), sub_match.group(2),
                sub_match.group(3), sub_match.group(4)
            )
        
        # DIVIDE <field> (<alias>) BY <field/literal> GIVING <field> (<alias>)
        # The BY operand can be a field reference OR a numeric literal
        div_match = re.match(
            r'DIVIDE\s+(\S+)\s*\(([A-Z])\)\s+BY\s+(\S+)\s*(?:\(([A-Z])\))?\s+GIVING\s+(\S+)\s*\(([A-Z])\)',
            stmt, re.IGNORECASE
        )
        if div_match:
            return self._exec_divide(
                div_match.group(1), div_match.group(2),
                div_match.group(3), div_match.group(4),  # group 4 may be None for literals
                div_match.group(5), div_match.group(6)
            )
        
        # SET OPERATION <n> TO GO TO OPERATION <m>
        # This is the runtime flow modification feature that COBOL dropped!
        set_match = re.match(
            r'SET\s+OPERATION\s+(\d+)\s+TO\s+GO\s+TO\s+OPERATION\s+(\d+)',
            stmt, re.IGNORECASE
        )
        if set_match:
            return self._exec_set_operation(
                int(set_match.group(1)),
                int(set_match.group(2))
            )
        
        # CLOSE-OUT FILES <aliases>
        close_match = re.match(r'CLOSE-OUT\s+FILES?\s+([A-Z\s,]+)', stmt, re.IGNORECASE)
        if close_match:
            aliases = re.findall(r'[A-Z]', close_match.group(1))
            for alias in aliases:
                if alias in self.files:
                    self.files[alias].is_open = False
            return 'CONTINUE'
        
        # REWIND <alias> - Rewinds file to beginning (from U1518 manual!)
        rewind_match = re.match(r'REWIND\s+([A-Z])', stmt, re.IGNORECASE)
        if rewind_match:
            return self._exec_rewind(rewind_match.group(1))
        
        # EXECUTE OPERATION h1 [THROUGH OPERATION h2] - Subroutine call! (from U1518 manual!)
        execute_through_match = re.match(
            r'EXECUTE\s+OPERATION\s+(\d+)\s+THROUGH\s+OPERATION\s+(\d+)',
            stmt, re.IGNORECASE
        )
        if execute_through_match:
            return self._exec_execute(
                int(execute_through_match.group(1)),
                int(execute_through_match.group(2))
            )
        
        # EXECUTE OPERATION h1 - Single operation subroutine call
        execute_single_match = re.match(r'EXECUTE\s+OPERATION\s+(\d+)', stmt, re.IGNORECASE)
        if execute_single_match:
            return self._exec_execute(
                int(execute_single_match.group(1)),
                int(execute_single_match.group(1))
            )
        
        # TEST <field> (<alias>) AGAINST <value>
        test_match = re.match(
            r'TEST\s+(\S+)\s*\(([A-Z])\)\s+AGAINST\s+(.+)',
            stmt, re.IGNORECASE
        )
        if test_match:
            return self._exec_test(
                test_match.group(1), test_match.group(2),
                test_match.group(3).strip()
            )
        
        # Unknown statement
        if self.debug:
            print(f"    WARNING: Unknown statement: {stmt}")
        
        return 'CONTINUE'
    
    def _exec_read_item(self, alias: str) -> Any:
        """READ-ITEM <alias> - Read next record from file"""
        alias = alias.upper()
        
        # Track last read file for IF END OF DATA
        self.last_read_file = alias
        self.last_read_eof = False
        
        if alias not in self.files:
            if self.debug:
                print(f"    ERROR: File {alias} not defined")
            return 'CONTINUE'
        
        file = self.files[alias]
        
        if file.current_record >= len(file.records):
            file.is_eof = True
            self.last_read_eof = True
            if self.debug:
                print(f"    EOF reached for file {alias}")
            return 'CONTINUE'
        
        # Get current record
        record = file.records[file.current_record]
        self.current_records[alias] = record
        file.current_record += 1
        
        # Update block count if enabled (integrity feature)
        if file.block_count_enabled:
            file.block_count += 1
        
        if self.debug:
            fields_str = ', '.join(f"{k}={v.value}" for k, v in record.fields.items())
            print(f"    Read from {alias}: {fields_str}")
        
        return 'CONTINUE'
    
    def _exec_write_item(self, alias: str) -> Any:
        """WRITE-ITEM <alias> - Write current record to file"""
        alias = alias.upper()
        
        if alias not in self.files:
            # Create output file on the fly
            self.files[alias] = FlowMaticFile(
                name=f'OUTPUT-{alias}',
                alias=alias,
                mode='OUTPUT'
            )
        
        file = self.files[alias]
        
        if alias in self.current_records:
            # Clone the current record for output
            import copy
            output_record = copy.deepcopy(self.current_records[alias])
            file.records.append(output_record)
            
            if self.debug:
                fields_str = ', '.join(f"{k}={v.value}" for k, v in output_record.fields.items())
                print(f"    Wrote to {alias}: {fields_str}")
        
        return 'CONTINUE'
    
    def _exec_print_item(self, alias: str) -> Any:
        """PRINT-ITEM <alias> - Print to HSP (High-Speed Printer)"""
        alias = alias.upper()
        
        if alias in self.current_records:
            record = self.current_records[alias]
            # Format for printing
            line_parts = []
            for field_name, field in record.fields.items():
                line_parts.append(f"{field_name}: {field.value}")
            line = "  |  ".join(line_parts)
            self.output_buffer.append(line)
            
            if self.debug:
                print(f"    PRINT: {line}")
        
        return 'CONTINUE'
    
    def _exec_if_eof(self, target_op: int) -> Any:
        """IF END OF DATA GO TO OPERATION <n>"""
        # Check if the last read operation hit EOF
        if self.last_read_eof:
            if self.debug:
                print(f"    EOF detected on file {self.last_read_file}, jumping to operation {target_op}")
            return target_op
        
        return 'CONTINUE'
    
    def _exec_compare(self, field1: str, alias1: str, field2: str, alias2: str) -> Any:
        """COMPARE <field> (<alias>) WITH <field> (<alias>)"""
        alias1 = alias1.upper()
        alias2 = alias2.upper()
        
        val1 = self._get_field_value(field1, alias1)
        val2 = self._get_field_value(field2, alias2)
        
        # Handle None values - treat as empty string or zero for comparison
        if val1 is None:
            val1 = '' if isinstance(val2, str) else 0
        if val2 is None:
            val2 = '' if isinstance(val1, str) else 0
        
        if val1 == val2:
            self.comparison_result = 'EQUAL'
        elif val1 > val2:
            self.comparison_result = 'GREATER'
        else:
            self.comparison_result = 'LESS'
        
        if self.debug:
            print(f"    Compare: {val1} vs {val2} = {self.comparison_result}")
        
        return 'CONTINUE'
    
    def _exec_transfer(self, from_alias: str, to_alias: str) -> Any:
        """TRANSFER <alias> TO <alias> - Copy entire record"""
        from_alias = from_alias.upper()
        to_alias = to_alias.upper()
        
        if from_alias in self.current_records:
            import copy
            self.current_records[to_alias] = copy.deepcopy(self.current_records[from_alias])
            
            if self.debug:
                print(f"    Transferred record from {from_alias} to {to_alias}")
        
        return 'CONTINUE'
    
    def _exec_move(self, value: str, field_name: str, alias: str) -> Any:
        """MOVE <value> TO <field> (<alias>)"""
        alias = alias.upper()
        
        # Parse the value - could be literal, field reference, or special value
        if value.startswith('"') and value.endswith('"'):
            # String literal
            actual_value = value[1:-1]
        elif value.upper() == 'ZEROS' or value.upper() == 'ZEROES':
            actual_value = 0
        elif value.upper() == 'SPACES':
            actual_value = ''
        elif re.match(r'^[\d.]+$', value):
            # Numeric literal
            if '.' in value:
                actual_value = Decimal(value)
            else:
                actual_value = int(value)
        else:
            # Could be a field reference like FIELD-NAME (X)
            field_ref = re.match(r'(\S+)\s*\(([A-Z])\)', value, re.IGNORECASE)
            if field_ref:
                actual_value = self._get_field_value(field_ref.group(1), field_ref.group(2))
            else:
                actual_value = value
        
        self._set_field_value(field_name, alias, actual_value)
        
        if self.debug:
            print(f"    Move {actual_value} to {field_name}({alias})")
        
        return 'CONTINUE'
    
    def _exec_multiply(self, field1: str, alias1: str, field2: str, alias2: str, 
                       result_field: str, result_alias: str) -> Any:
        """MULTIPLY <field> (<alias>) BY <field/literal> GIVING <field> (<alias>)"""
        val1 = self._get_field_value(field1, alias1.upper())
        
        # Second operand can be a field reference or a numeric literal
        if alias2:
            val2 = self._get_field_value(field2, alias2.upper())
        else:
            # It's a numeric literal
            try:
                val2 = Decimal(field2)
            except:
                val2 = 0
        
        # Handle None values
        val1 = val1 if val1 is not None else 0
        val2 = val2 if val2 is not None else 0
        
        result = Decimal(str(val1)) * Decimal(str(val2))
        self._set_field_value(result_field, result_alias.upper(), result)
        
        if self.debug:
            print(f"    Multiply: {val1} * {val2} = {result}")
        
        return 'CONTINUE'
    
    def _exec_add_giving(self, field1: str, alias1: str, field2: str, alias2: str,
                         result_field: str, result_alias: str) -> Any:
        """ADD <field> (<alias>) TO <field> (<alias>) GIVING <field> (<alias>)"""
        val1 = self._get_field_value(field1, alias1.upper())
        val2 = self._get_field_value(field2, alias2.upper())
        
        # Handle None values
        val1 = val1 if val1 is not None else 0
        val2 = val2 if val2 is not None else 0
        
        result = Decimal(str(val1)) + Decimal(str(val2))
        self._set_field_value(result_field, result_alias.upper(), result)
        
        if self.debug:
            print(f"    Add: {val1} + {val2} = {result}")
        
        return 'CONTINUE'
    
    def _exec_add(self, field1: str, alias1: str, field2: str, alias2: str) -> Any:
        """ADD <field/literal> TO <field> (<alias>) - result goes to second field"""
        # First operand can be a field reference or a numeric literal
        if alias1:
            val1 = self._get_field_value(field1, alias1.upper())
        else:
            # It's a numeric literal
            try:
                val1 = Decimal(field1)
            except:
                val1 = 0
        
        val2 = self._get_field_value(field2, alias2.upper())
        
        # Handle None values
        val1 = val1 if val1 is not None else 0
        val2 = val2 if val2 is not None else 0
        
        result = Decimal(str(val1)) + Decimal(str(val2))
        self._set_field_value(field2, alias2.upper(), result)
        
        if self.debug:
            print(f"    Add: {val1} + {val2} = {result}")
        
        return 'CONTINUE'
    
    def _exec_subtract(self, field1: str, alias1: str, field2: str, alias2: str) -> Any:
        """SUBTRACT <field> (<alias>) FROM <field> (<alias>)"""
        val1 = self._get_field_value(field1, alias1.upper())
        val2 = self._get_field_value(field2, alias2.upper())
        
        # Handle None values
        val1 = val1 if val1 is not None else 0
        val2 = val2 if val2 is not None else 0
        
        result = Decimal(str(val2)) - Decimal(str(val1))
        self._set_field_value(field2, alias2.upper(), result)
        
        if self.debug:
            print(f"    Subtract: {val2} - {val1} = {result}")
        
        return 'CONTINUE'
    
    def _exec_divide(self, field1: str, alias1: str, field2: str, alias2: str,
                     result_field: str, result_alias: str) -> Any:
        """DIVIDE <field> (<alias>) BY <field/literal> GIVING <field> (<alias>)"""
        val1 = self._get_field_value(field1, alias1.upper())
        
        # Second operand can be a field reference or a numeric literal
        if alias2:
            val2 = self._get_field_value(field2, alias2.upper())
        else:
            # It's a numeric literal
            try:
                val2 = Decimal(field2)
            except:
                val2 = 1  # Avoid division by zero
        
        # Handle None values
        val1 = val1 if val1 is not None else 0
        val2 = val2 if val2 is not None else 0
        
        if val2 == 0:
            result = Decimal('0')
        else:
            result = Decimal(str(val1)) / Decimal(str(val2))
        
        self._set_field_value(result_field, result_alias.upper(), result)
        
        if self.debug:
            print(f"    Divide: {val1} / {val2} = {result}")
        
        return 'CONTINUE'
    
    def _exec_set_operation(self, op_num: int, target_num: int) -> Any:
        """
        SET OPERATION <n> TO GO TO OPERATION <m>
        
        This is the runtime flow modification feature that COBOL dropped!
        It allows changing where a jump goes at runtime - in one English sentence.
        COBOL had ALTER which was deprecated and removed.
        Modern equivalent requires entire Strategy pattern or vtables.
        """
        self.operation_targets[op_num] = target_num
        
        if self.debug:
            print(f"    SET: Operation {op_num} will now go to operation {target_num}")
        
        return 'CONTINUE'
    
    def _exec_test(self, field_name: str, alias: str, test_value: str) -> Any:
        """TEST <field> (<alias>) AGAINST <value>"""
        alias = alias.upper()
        val = self._get_field_value(field_name, alias)
        
        # Parse test value
        if test_value.startswith('"') and test_value.endswith('"'):
            test_val = test_value[1:-1]
        elif re.match(r'^[\d.]+$', test_value):
            if '.' in test_value:
                test_val = Decimal(test_value)
            else:
                test_val = int(test_value)
        else:
            test_val = test_value
        
        if val == test_val:
            self.comparison_result = 'EQUAL'
        elif val > test_val:
            self.comparison_result = 'GREATER'
        else:
            self.comparison_result = 'LESS'
        
        if self.debug:
            print(f"    Test: {val} vs {test_val} = {self.comparison_result}")
    
    def _exec_rewind(self, alias: str) -> Any:
        """
        REWIND <alias> - Rewinds file to beginning
        
        From U1518 manual (page 97): "Rewinds current reel of an input file."
        This allows re-reading a file for multi-pass algorithms.
        """
        alias = alias.upper()
        
        if alias in self.files:
            self.files[alias].current_record = 0  # Reset to first record
            self.files[alias].is_eof = False
            self.last_read_eof = False  # Also reset the interpreter's EOF flag
            
            if self.debug:
                print(f"    Rewound file {alias} to beginning")
        else:
            if self.debug:
                print(f"    WARNING: Cannot rewind unknown file {alias}")
        
        return 'CONTINUE'
    
    def _exec_execute(self, start_op: int, end_op: int) -> Any:
        """
        EXECUTE OPERATION h1 [THROUGH OPERATION h2] - Subroutine mechanism!
        
        From U1518 manual (page 92): "Performs designated operation or 
        sequence of operations."
        
        This executes operations start_op through end_op as a subroutine,
        then returns to continue execution after the EXECUTE statement.
        
        This was a primitive but effective subroutine mechanism in 1958!
        """
        if self.debug:
            if start_op == end_op:
                print(f"    EXECUTE: Running operation {start_op} as subroutine")
            else:
                print(f"    EXECUTE: Running operations {start_op} through {end_op} as subroutine")
        
        # Execute the specified operations
        current_op = start_op
        max_iterations = 10000
        iterations = 0
        
        while current_op <= end_op and iterations < max_iterations:
            iterations += 1
            
            if current_op not in self.operations:
                if self.debug:
                    print(f"    WARNING: Operation {current_op} not found in EXECUTE")
                break
            
            # Execute all statements in this operation
            op = self.operations[current_op]
            self.current_operation = current_op
            
            if self.debug:
                print(f"    [EXECUTE] Operation {current_op}")
            
            for stmt in op.statements:
                result = self._execute_statement(stmt)
                
                # Handle control flow within EXECUTE
                if result == 'STOP':
                    # STOP within EXECUTE terminates entire program
                    return 'STOP'
                elif isinstance(result, int):
                    # Jump within the EXECUTE range continues there
                    if start_op <= result <= end_op:
                        current_op = result
                        break
                    else:
                        # Jump outside EXECUTE range - just execute that op and continue
                        if result in self.operations:
                            sub_op = self.operations[result]
                            self.current_operation = result
                            for sub_stmt in sub_op.statements:
                                sub_result = self._execute_statement(sub_stmt)
                                if sub_result == 'STOP':
                                    return 'STOP'
            else:
                # No jump, move to next operation in sequence
                current_op += 1
        
        if self.debug:
            print(f"    EXECUTE complete, returning to caller")
        
        # Return CONTINUE to proceed with next statement after EXECUTE
        return 'CONTINUE'
        
        return 'CONTINUE'
    
    def _get_field_value(self, field_name: str, alias: str) -> Any:
        """Get value of a field from a file's current record"""
        alias = alias.upper()
        
        if alias not in self.current_records:
            return None
        
        record = self.current_records[alias]
        field_name_upper = field_name.upper().replace('-', '_')
        field_name_orig = field_name.upper()
        
        # Try exact match first
        if field_name_orig in record.fields:
            return record.fields[field_name_orig].value
        if field_name_upper in record.fields:
            return record.fields[field_name_upper].value
        
        # Try case-insensitive match
        for fname, field in record.fields.items():
            if fname.upper() == field_name_upper or fname.upper() == field_name_orig:
                return field.value
        
        return None
    
    def _set_field_value(self, field_name: str, alias: str, value: Any):
        """Set value of a field in a file's current record"""
        alias = alias.upper()
        
        if alias not in self.current_records:
            # Create empty record
            self.current_records[alias] = FlowMaticRecord()
        
        record = self.current_records[alias]
        field_name_upper = field_name.upper()
        
        # Find existing field (case-insensitive)
        for fname in record.fields:
            if fname.upper() == field_name_upper:
                record.fields[fname].value = value
                return
        
        # Create new field
        record.set(field_name_upper, value)
    
    def get_output(self, alias: str) -> List[Dict[str, Any]]:
        """Get output records from a file"""
        alias = alias.upper()
        
        if alias not in self.files:
            return []
        
        file = self.files[alias]
        output = []
        
        for record in file.records:
            record_dict = {}
            for field_name, field in record.fields.items():
                record_dict[field_name] = field.value
            output.append(record_dict)
        
        return output
    
    def get_printer_output(self) -> List[str]:
        """Get High-Speed Printer output buffer"""
        return self.output_buffer


# ============================================================================
# Example Programs
# ============================================================================

def run_example():
    """Run example FLOW-MATIC programs"""
    
    # Example 1: Simple inventory matching (from original manual)
    print("=" * 70)
    print("FLOW-MATIC EXAMPLE 1: Inventory Matching")
    print("Based on U1518 FLOW-MATIC Programming System (1958)")
    print("=" * 70)
    
    inventory_program = """
    (0) INPUT INVENTORY FILE-A PRICE FILE-B ;
        OUTPUT PRICED-INV FILE-C .
    (1) READ-ITEM A ;
        READ-ITEM B .
    (2) COMPARE PRODUCT-NO (A) WITH PRODUCT-NO (B) ;
        IF LESS GO TO OPERATION 5 ;
        IF EQUAL GO TO OPERATION 3 ;
        OTHERWISE GO TO OPERATION 4 .
    (3) TRANSFER A TO C ;
        MOVE UNIT-PRICE (B) TO UNIT-PRICE (C) ;
        WRITE-ITEM C ;
        JUMP TO OPERATION 1 .
    (4) READ-ITEM B ;
        IF END OF DATA GO TO OPERATION 7 ;
        JUMP TO OPERATION 2 .
    (5) READ-ITEM A ;
        IF END OF DATA GO TO OPERATION 7 ;
        JUMP TO OPERATION 2 .
    (6) JUMP TO OPERATION 1 .
    (7) CLOSE-OUT FILES C ;
        STOP .
    """
    
    # Sample data
    inventory_records = [
        {'PRODUCT-NO': '001', 'DESCRIPTION': 'Widget A', 'QUANTITY': 100},
        {'PRODUCT-NO': '002', 'DESCRIPTION': 'Widget B', 'QUANTITY': 50},
        {'PRODUCT-NO': '004', 'DESCRIPTION': 'Widget D', 'QUANTITY': 200},
    ]
    
    price_records = [
        {'PRODUCT-NO': '001', 'UNIT-PRICE': Decimal('10.50')},
        {'PRODUCT-NO': '002', 'UNIT-PRICE': Decimal('25.00')},
        {'PRODUCT-NO': '003', 'UNIT-PRICE': Decimal('15.75')},  # No match in inventory
        {'PRODUCT-NO': '004', 'UNIT-PRICE': Decimal('5.00')},
    ]
    
    interpreter = FlowMaticInterpreter(debug=True)
    interpreter.load_program(inventory_program)
    interpreter.load_file('A', inventory_records)
    interpreter.load_file('B', price_records)
    interpreter.run()
    
    print("\n--- Output (File C) ---")
    for record in interpreter.get_output('C'):
        print(record)


if __name__ == '__main__':
    run_example()

