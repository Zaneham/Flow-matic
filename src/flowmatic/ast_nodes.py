"""
FLOW-MATIC Abstract Syntax Tree Node Classes
=============================================
Based on: U1518 FLOW-MATIC Programming System (1958)
          Remington Rand UNIVAC Division

Each node class represents a construct in the FLOW-MATIC language.
All nodes implement:
  - __str__(): String representation for debugging
  - __repr__(): Same as __str__
  - execute(context): Execute the node in a given context

This follows the same pattern as the Plankalkül implementation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from enum import Enum
import copy


class FlowMaticError(Exception):
    """Base exception for FLOW-MATIC errors"""
    pass


class ParseError(FlowMaticError):
    """Raised when parsing fails"""
    def __init__(self, message: str, line: int = None, col: int = None):
        self.line = line
        self.col = col
        loc = f" at line {line}" if line else ""
        super().__init__(f"Parse error{loc}: {message}")


class ExecutionError(FlowMaticError):
    """Raised when execution fails"""
    def __init__(self, message: str, operation: int = None):
        self.operation = operation
        loc = f" in operation {operation}" if operation else ""
        super().__init__(f"Execution error{loc}: {message}")


# =============================================================================
# Execution Context
# =============================================================================

class ExecutionContext:
    """
    Execution context for FLOW-MATIC programs.
    
    Tracks:
    - Files and their records
    - Current record for each file
    - Comparison results
    - Operation targets (for SET OPERATION)
    """
    
    def __init__(self):
        self.files: Dict[str, 'FileContext'] = {}
        self.current_records: Dict[str, Dict[str, Any]] = {}
        self.comparison_result: Optional[str] = None  # EQUAL, GREATER, LESS
        self.operation_targets: Dict[int, int] = {}  # SET OPERATION modifications
        self.last_read_file: Optional[str] = None
        self.last_read_eof: bool = False
        self.printer_output: List[str] = []
        
    def __str__(self):
        return f"ExecutionContext(files={list(self.files.keys())}, comparison={self.comparison_result})"


@dataclass
class FileContext:
    """Context for a single file"""
    name: str
    alias: str
    mode: str  # INPUT, OUTPUT, HSP
    records: List[Dict[str, Any]] = field(default_factory=list)
    current_index: int = 0
    is_eof: bool = False
    
    def read(self) -> Optional[Dict[str, Any]]:
        """Read next record, return None if EOF"""
        if self.current_index >= len(self.records):
            self.is_eof = True
            return None
        record = self.records[self.current_index]
        self.current_index += 1
        return record
    
    def write(self, record: Dict[str, Any]):
        """Write a record"""
        self.records.append(copy.deepcopy(record))


# =============================================================================
# AST Node Base Class
# =============================================================================

class ASTNode:
    """Base class for all AST nodes"""
    
    def execute(self, ctx: ExecutionContext) -> Any:
        raise NotImplementedError(f"{self.__class__.__name__}.execute() not implemented")
    
    def __str__(self):
        return f"{self.__class__.__name__}()"
    
    def __repr__(self):
        return self.__str__()


# =============================================================================
# Program Structure Nodes
# =============================================================================

@dataclass
class Program(ASTNode):
    """
    Complete FLOW-MATIC program.
    
    Program ::= Operation0 { Operation }
    """
    file_definitions: 'FileDefinitions'
    operations: Dict[int, 'Operation']
    
    def __str__(self):
        return f"Program(files={self.file_definitions}, ops={list(self.operations.keys())})"
    
    def execute(self, ctx: ExecutionContext) -> ExecutionContext:
        """Execute the entire program"""
        # First, set up files from Operation 0
        self.file_definitions.execute(ctx)
        
        # Then execute operations starting from 1
        current_op = 1
        max_iterations = 100000
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            if current_op not in self.operations:
                break
            
            op = self.operations[current_op]
            result = op.execute(ctx)
            
            if result == 'STOP':
                break
            elif isinstance(result, int):
                current_op = result
            else:
                current_op += 1
        
        return ctx


@dataclass
class FileDefinitions(ASTNode):
    """
    File definitions from Operation 0.
    
    FileDefinitions ::= { FileDefinition ';' }
    """
    definitions: List['FileDefinition']
    
    def __str__(self):
        return f"FileDefinitions({self.definitions})"
    
    def execute(self, ctx: ExecutionContext):
        for defn in self.definitions:
            defn.execute(ctx)


@dataclass
class FileDefinition(ASTNode):
    """Single file definition"""
    name: str
    alias: str
    mode: str  # INPUT, OUTPUT, HSP
    
    def __str__(self):
        return f"FileDefinition({self.mode} {self.name} FILE-{self.alias})"
    
    def execute(self, ctx: ExecutionContext):
        ctx.files[self.alias] = FileContext(
            name=self.name,
            alias=self.alias,
            mode=self.mode
        )


@dataclass
class Operation(ASTNode):
    """
    A numbered operation block.
    
    Operation ::= '(' NUMBER ')' StatementList '.'
    """
    number: int
    statements: List['Statement']
    
    def __str__(self):
        return f"Operation({self.number}, {len(self.statements)} stmts)"
    
    def execute(self, ctx: ExecutionContext) -> Union[str, int, None]:
        """
        Execute all statements in this operation.
        Returns:
            'STOP' - Program should stop
            int - Jump to this operation number
            None - Continue to next operation
        """
        for stmt in self.statements:
            result = stmt.execute(ctx)
            if result == 'STOP':
                return 'STOP'
            elif isinstance(result, int):
                return result
        return None


# =============================================================================
# Statement Nodes
# =============================================================================

class Statement(ASTNode):
    """Base class for statements"""
    pass


@dataclass
class ReadItem(Statement):
    """
    READ-ITEM statement.
    
    ReadItem ::= 'READ-ITEM' LETTER
    """
    file_alias: str
    
    def __str__(self):
        return f"ReadItem({self.file_alias})"
    
    def execute(self, ctx: ExecutionContext):
        alias = self.file_alias.upper()
        ctx.last_read_file = alias
        ctx.last_read_eof = False
        
        if alias not in ctx.files:
            raise ExecutionError(f"File {alias} not defined")
        
        file_ctx = ctx.files[alias]
        record = file_ctx.read()
        
        if record is None:
            ctx.last_read_eof = True
        else:
            ctx.current_records[alias] = copy.deepcopy(record)
        
        return None


@dataclass
class WriteItem(Statement):
    """
    WRITE-ITEM statement.
    
    WriteItem ::= 'WRITE-ITEM' LETTER
    """
    file_alias: str
    
    def __str__(self):
        return f"WriteItem({self.file_alias})"
    
    def execute(self, ctx: ExecutionContext):
        alias = self.file_alias.upper()
        
        if alias not in ctx.files:
            ctx.files[alias] = FileContext(
                name=f"OUTPUT-{alias}",
                alias=alias,
                mode='OUTPUT'
            )
        
        if alias in ctx.current_records:
            ctx.files[alias].write(ctx.current_records[alias])
        
        return None


@dataclass
class PrintItem(Statement):
    """
    PRINT-ITEM statement (HSP output).
    
    PrintItem ::= 'PRINT-ITEM' LETTER
    """
    file_alias: str
    
    def __str__(self):
        return f"PrintItem({self.file_alias})"
    
    def execute(self, ctx: ExecutionContext):
        alias = self.file_alias.upper()
        
        if alias in ctx.current_records:
            record = ctx.current_records[alias]
            line = " | ".join(f"{k}={v}" for k, v in record.items())
            ctx.printer_output.append(line)
        
        return None


@dataclass
class Compare(Statement):
    """
    COMPARE statement.
    
    Compare ::= 'COMPARE' FieldRef 'WITH' FieldRef
    """
    field1: 'FieldRef'
    field2: 'FieldRef'
    
    def __str__(self):
        return f"Compare({self.field1} WITH {self.field2})"
    
    def execute(self, ctx: ExecutionContext):
        val1 = self.field1.get_value(ctx)
        val2 = self.field2.get_value(ctx)
        
        # Handle None values
        if val1 is None:
            val1 = '' if isinstance(val2, str) else 0
        if val2 is None:
            val2 = '' if isinstance(val1, str) else 0
        
        if val1 == val2:
            ctx.comparison_result = 'EQUAL'
        elif val1 > val2:
            ctx.comparison_result = 'GREATER'
        else:
            ctx.comparison_result = 'LESS'
        
        return None


@dataclass
class IfEqual(Statement):
    """IF EQUAL GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"IfEqual(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        if ctx.comparison_result == 'EQUAL':
            return self.target
        return None


@dataclass
class IfGreater(Statement):
    """IF GREATER GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"IfGreater(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        if ctx.comparison_result == 'GREATER':
            return self.target
        return None


@dataclass
class IfLess(Statement):
    """IF LESS GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"IfLess(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        if ctx.comparison_result == 'LESS':
            return self.target
        return None


@dataclass
class IfEndOfData(Statement):
    """IF END OF DATA GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"IfEndOfData(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        if ctx.last_read_eof:
            return self.target
        return None


@dataclass
class Otherwise(Statement):
    """OTHERWISE GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"Otherwise(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        return self.target


@dataclass
class Jump(Statement):
    """JUMP TO OPERATION n / GO TO OPERATION n"""
    target: int
    
    def __str__(self):
        return f"Jump(-> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        # Check if this operation has been modified by SET OPERATION
        # (This is the feature COBOL killed!)
        return self.target


@dataclass
class Transfer(Statement):
    """
    TRANSFER statement - copy entire record.
    
    Transfer ::= 'TRANSFER' LETTER 'TO' LETTER
    """
    from_alias: str
    to_alias: str
    
    def __str__(self):
        return f"Transfer({self.from_alias} -> {self.to_alias})"
    
    def execute(self, ctx: ExecutionContext):
        from_alias = self.from_alias.upper()
        to_alias = self.to_alias.upper()
        
        if from_alias in ctx.current_records:
            ctx.current_records[to_alias] = copy.deepcopy(ctx.current_records[from_alias])
        
        return None


@dataclass
class Move(Statement):
    """
    MOVE statement.
    
    Move ::= 'MOVE' Value 'TO' FieldRef
    """
    value: 'Value'
    target: 'FieldRef'
    
    def __str__(self):
        return f"Move({self.value} -> {self.target})"
    
    def execute(self, ctx: ExecutionContext):
        val = self.value.get_value(ctx)
        self.target.set_value(ctx, val)
        return None


@dataclass
class Add(Statement):
    """ADD field TO field [GIVING field]"""
    field1: 'FieldRef'
    field2: 'FieldRef'
    result_field: Optional['FieldRef'] = None
    
    def __str__(self):
        if self.result_field:
            return f"Add({self.field1} + {self.field2} -> {self.result_field})"
        return f"Add({self.field1} + {self.field2} -> {self.field2})"
    
    def execute(self, ctx: ExecutionContext):
        val1 = self.field1.get_value(ctx) or 0
        val2 = self.field2.get_value(ctx) or 0
        result = Decimal(str(val1)) + Decimal(str(val2))
        
        target = self.result_field if self.result_field else self.field2
        target.set_value(ctx, result)
        return None


@dataclass
class Subtract(Statement):
    """SUBTRACT field FROM field [GIVING field]"""
    field1: 'FieldRef'
    field2: 'FieldRef'
    result_field: Optional['FieldRef'] = None
    
    def __str__(self):
        if self.result_field:
            return f"Subtract({self.field2} - {self.field1} -> {self.result_field})"
        return f"Subtract({self.field2} - {self.field1} -> {self.field2})"
    
    def execute(self, ctx: ExecutionContext):
        val1 = self.field1.get_value(ctx) or 0
        val2 = self.field2.get_value(ctx) or 0
        result = Decimal(str(val2)) - Decimal(str(val1))
        
        target = self.result_field if self.result_field else self.field2
        target.set_value(ctx, result)
        return None


@dataclass
class Multiply(Statement):
    """MULTIPLY field BY field GIVING field"""
    field1: 'FieldRef'
    field2: 'FieldRef'
    result_field: 'FieldRef'
    
    def __str__(self):
        return f"Multiply({self.field1} * {self.field2} -> {self.result_field})"
    
    def execute(self, ctx: ExecutionContext):
        val1 = self.field1.get_value(ctx) or 0
        val2 = self.field2.get_value(ctx) or 0
        result = Decimal(str(val1)) * Decimal(str(val2))
        self.result_field.set_value(ctx, result)
        return None


@dataclass
class Divide(Statement):
    """DIVIDE field BY field GIVING field"""
    field1: 'FieldRef'
    field2: 'FieldRef'
    result_field: 'FieldRef'
    
    def __str__(self):
        return f"Divide({self.field1} / {self.field2} -> {self.result_field})"
    
    def execute(self, ctx: ExecutionContext):
        val1 = self.field1.get_value(ctx) or 0
        val2 = self.field2.get_value(ctx) or 0
        
        if val2 == 0:
            result = Decimal('0')
        else:
            result = Decimal(str(val1)) / Decimal(str(val2))
        
        self.result_field.set_value(ctx, result)
        return None


@dataclass
class SetOperation(Statement):
    """
    SET OPERATION - Runtime flow modification.
    
    THIS IS THE FEATURE COBOL KILLED!
    
    SetOperation ::= 'SET' 'OPERATION' NUMBER 'TO' 'GO' 'TO' 'OPERATION' NUMBER
    
    This allows changing where a jump goes AT RUNTIME.
    Modern equivalent requires Strategy pattern or vtables.
    """
    operation_num: int
    target_num: int
    
    def __str__(self):
        return f"SetOperation({self.operation_num} -> {self.target_num})"
    
    def execute(self, ctx: ExecutionContext):
        ctx.operation_targets[self.operation_num] = self.target_num
        return None


@dataclass
class Test(Statement):
    """
    TEST statement.
    
    Test ::= 'TEST' FieldRef 'AGAINST' Value
    """
    field: 'FieldRef'
    value: 'Value'
    
    def __str__(self):
        return f"Test({self.field} AGAINST {self.value})"
    
    def execute(self, ctx: ExecutionContext):
        field_val = self.field.get_value(ctx)
        test_val = self.value.get_value(ctx)
        
        if field_val is None:
            field_val = '' if isinstance(test_val, str) else 0
        
        if field_val == test_val:
            ctx.comparison_result = 'EQUAL'
        elif field_val > test_val:
            ctx.comparison_result = 'GREATER'
        else:
            ctx.comparison_result = 'LESS'
        
        return None


@dataclass
class CloseOut(Statement):
    """CLOSE-OUT FILES"""
    file_aliases: List[str]
    
    def __str__(self):
        return f"CloseOut({self.file_aliases})"
    
    def execute(self, ctx: ExecutionContext):
        # In the original FLOW-MATIC, this would flush buffers
        return None


@dataclass
class Stop(Statement):
    """STOP statement"""
    
    def __str__(self):
        return "Stop()"
    
    def execute(self, ctx: ExecutionContext):
        return 'STOP'


# =============================================================================
# Value Nodes
# =============================================================================

class Value(ASTNode):
    """Base class for values"""
    
    def get_value(self, ctx: ExecutionContext) -> Any:
        raise NotImplementedError()


@dataclass
class FieldRef(Value):
    """
    Field reference: FIELD-NAME (ALIAS)
    
    FieldRef ::= IDENTIFIER '(' LETTER ')'
    """
    field_name: str
    file_alias: str
    
    def __str__(self):
        return f"{self.field_name}({self.file_alias})"
    
    def get_value(self, ctx: ExecutionContext) -> Any:
        alias = self.file_alias.upper()
        name = self.field_name.upper()
        
        if alias not in ctx.current_records:
            return None
        
        record = ctx.current_records[alias]
        
        # Try exact match
        if name in record:
            return record[name]
        
        # Try with dashes converted to underscores
        name_underscore = name.replace('-', '_')
        if name_underscore in record:
            return record[name_underscore]
        
        # Case-insensitive search
        for key in record:
            if key.upper() == name or key.upper() == name_underscore:
                return record[key]
        
        return None
    
    def set_value(self, ctx: ExecutionContext, value: Any):
        alias = self.file_alias.upper()
        name = self.field_name.upper()
        
        if alias not in ctx.current_records:
            ctx.current_records[alias] = {}
        
        ctx.current_records[alias][name] = value


@dataclass
class NumericLiteral(Value):
    """Numeric literal value"""
    value: Decimal
    
    def __str__(self):
        return f"Num({self.value})"
    
    def get_value(self, ctx: ExecutionContext) -> Decimal:
        return self.value


@dataclass
class StringLiteral(Value):
    """String literal value"""
    value: str
    
    def __str__(self):
        return f'Str("{self.value}")'
    
    def get_value(self, ctx: ExecutionContext) -> str:
        return self.value


@dataclass
class Zeros(Value):
    """ZEROS / ZEROES special value"""
    
    def __str__(self):
        return "Zeros()"
    
    def get_value(self, ctx: ExecutionContext):
        return 0


@dataclass
class Spaces(Value):
    """SPACES special value"""
    
    def __str__(self):
        return "Spaces()"
    
    def get_value(self, ctx: ExecutionContext) -> str:
        return ""

