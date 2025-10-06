#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from termcolor import colored
from typing import *


# The different ways an instruction uses the RD operand.
class RdMode(Enum):
    Unused = auto()
    R = auto()
    W = auto()
    RW = auto()


# The different ways an instruction uses the RS or immediate operand.
class RsMode(Enum):
    Unused = auto()
    R8 = auto()  # single register
    R16 = auto()  # register pair
    Imm8 = auto()  # signless 8 bit immediate
    JImm8 = auto()  # jump target immediate
    SImm4 = auto()  # signed 4 bit immediate


# The different ways an instruction uses condition codes.
class CondMode(Enum):
    Unused = auto()
    Cond1 = auto()  # condition in RD operand bits
    Cond2 = auto()  # condition in func1 bits


# An instruction opcode and information about the instruction's format.
@dataclass(eq=False)
class Opcode:
    name: str
    rd: RdMode = RdMode.Unused
    rs: RsMode = RsMode.Unused
    cond: CondMode = CondMode.Unused
    func0: int | None = None  # bits 0..3
    func1: int | None = None  # bits 12..15
    func2: int | None = None  # bits 4..7
    func3: int | None = None  # bits 8..11


# Regular instruction definitions
OPCODES = [
    # Basics
    Opcode("nop", func0=0, func1=0, func2=0, func3=0),
    Opcode("ldi", rd=RdMode.W, rs=RsMode.Imm8, func0=8),
    Opcode("mv", rd=RdMode.W, rs=RsMode.R8, func0=0, func1=1),
    Opcode("cmv", rd=RdMode.RW, rs=RsMode.R8, cond=CondMode.Cond2, func0=2),
    Opcode("cldi", rd=RdMode.RW, rs=RsMode.SImm4, cond=CondMode.Cond2,
           func0=3),

    # Branches
    Opcode("j", rs=RsMode.JImm8, func0=9, func2=0),
    Opcode("jro", rs=RsMode.R8, func0=0, func1=2, func2=0),
    Opcode("jr", rs=RsMode.R16, func0=0, func1=3, func2=0),
    Opcode("b", rs=RsMode.JImm8, cond=CondMode.Cond1, func0=9),
    Opcode("bro", rs=RsMode.R8, cond=CondMode.Cond1, func0=0, func1=2),
    Opcode("br", rs=RsMode.R16, cond=CondMode.Cond1, func0=0, func1=3),

    # Control and Status Registers
    Opcode("lcdcw", rd=RdMode.R, func0=0, func1=4, func3=0),
    Opcode("lcddw", rd=RdMode.R, func0=0, func1=4, func3=1),
    Opcode("lcdcr", rd=RdMode.W, func0=0, func1=4, func3=2),
    Opcode("lcddr", rd=RdMode.W, func0=0, func1=4, func3=3),

    # Unary Arithmetic
    Opcode("not", rd=RdMode.RW, func0=1, func1=0, func3=0),
    Opcode("neg", rd=RdMode.RW, func0=1, func1=0, func3=1),
    Opcode("shll", rd=RdMode.RW, func0=1, func1=0, func3=2),
    Opcode("shlc", rd=RdMode.RW, func0=1, func1=0, func3=3),
    Opcode("shrl", rd=RdMode.RW, func0=1, func1=0, func3=4),
    Opcode("shrc", rd=RdMode.RW, func0=1, func1=0, func3=5),
    Opcode("shra", rd=RdMode.RW, func0=1, func1=0, func3=6),
    Opcode("fswap", rd=RdMode.RW, func0=1, func1=0, func3=7),
    Opcode("fr", rd=RdMode.W, func0=1, func1=0, func3=8),
    Opcode("fw", rd=RdMode.R, func0=1, func1=0, func3=9),

    # Binary Arithmetic
    Opcode("add", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=1),
    Opcode("addc", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=2),
    Opcode("sub", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=3),
    Opcode("subc", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=4),
    Opcode("and", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=5),
    Opcode("or", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=6),
    Opcode("xor", rd=RdMode.RW, rs=RsMode.R8, func0=1, func1=7),
    Opcode("cmp", rd=RdMode.R, rs=RsMode.R8, func0=1, func1=8),
    Opcode("test", rd=RdMode.R, rs=RsMode.R8, func0=1, func1=9),
    Opcode("addci", rd=RdMode.RW, rs=RsMode.SImm4, func0=1, func1=10),
    Opcode("xori", rd=RdMode.RW, rs=RsMode.SImm4, func0=1, func1=11),
    Opcode("cmpi", rd=RdMode.R, rs=RsMode.SImm4, func0=1, func1=12),
    Opcode("addi", rd=RdMode.RW, rs=RsMode.Imm8, func0=12),
    Opcode("andi", rd=RdMode.RW, rs=RsMode.Imm8, func0=13),
    Opcode("ori", rd=RdMode.RW, rs=RsMode.Imm8, func0=14),
    Opcode("testi", rd=RdMode.R, rs=RsMode.Imm8, func0=15),

    # Pseudo-instructions
    Opcode("halt", func0=9, func1=0, func2=0, func3=0),
]
OPCODES_BY_NAME = {d.name: d for d in OPCODES}

# Directives
D_ORG = Opcode("D_ORG")
D_LABEL = Opcode("D_LABEL")


# The different kinds of operand we support.
class OperandKind(Enum):
    Imm = auto()
    Reg = auto()
    RegPair = auto()
    Cond = auto()
    Label = auto()
    Offset = auto()


# An instruction operand, like a register or an immediate value.
@dataclass
class Operand:
    kind: OperandKind
    value: Any

    def __repr__(self) -> str:
        return f"{self.kind.name}:{self.value}"


# A condition code.
class Condition(Enum):
    C = auto()
    NC = auto()
    Z = auto()
    NZ = auto()
    S = auto()
    NS = auto()
    O = auto()
    NO = auto()
    EQ = auto()
    NE = auto()
    UGE = auto()
    ULT = auto()
    ULE = auto()
    UGT = auto()
    SLT = auto()
    SGE = auto()
    SLE = auto()
    SGT = auto()

    def __repr__(self) -> str:
        return self.name


CONDITION_BY_NAME = {cond.name.lower(): cond for cond in Condition}
CONDITION_ENCODING = {
    Condition.C: 0b0010,
    Condition.NC: 0b0011,
    Condition.Z: 0b0100,
    Condition.NZ: 0b0101,
    Condition.S: 0b0110,
    Condition.NS: 0b0111,
    Condition.O: 0b1000,
    Condition.NO: 0b1001,
    Condition.EQ: 0b0100,
    Condition.NE: 0b0101,
    Condition.UGE: 0b0010,
    Condition.ULT: 0b0011,
    Condition.ULE: 0b1010,
    Condition.UGT: 0b1011,
    Condition.SLT: 0b1100,
    Condition.SGE: 0b1101,
    Condition.SLE: 0b1110,
    Condition.SGT: 0b1111,
}


@dataclass
class Offset:
    name: str
    binding: Optional[Instruction] = None
    offset: Optional[int] = None

    def __repr__(self) -> str:
        return self.name


# An assembly instruction, represented by its opcode and list of operands.
@dataclass
class Instruction:
    opcode: Opcode
    operands: List[Operand] = field(default_factory=list)
    address: Optional[int] = None
    encoding: Optional[int] = None

    def __repr__(self) -> str:
        s = self.opcode.name.upper()
        for op in self.operands:
            s += " " + repr(op)
        return s


# Report an error and exit with an error code.
def error(message, *args):
    sys.stderr.write(
        colored("error:", "red", attrs=["bold"]) + " " +
        colored(message, attrs=["bold"]) + "\n")
    for arg in args:
        if arg is None:
            continue
        elif isinstance(arg, Instruction):
            pretty = AssemblyPrinter([arg]).print()
            sys.stderr.write(pretty)
        else:
            sys.stderr.write(arg + "\n")
    sys.exit(1)


# A parser that converts human-readable assembly text into a list of
# `Instruction` objects.
@dataclass
class AssemblyParser:
    program: List[Instruction] = field(default_factory=list)

    # Abort with an error message.
    def error(self, message):
        consumed = len(self.current_contents) - len(self.current_input)
        consumed_lines = self.current_contents[0:consumed].split("\n")
        line_num = len(consumed_lines)
        col_num = len(consumed_lines[-1])
        remaining_line = self.current_input.split("\n")[0]
        error(message, f"{self.current_file}:{line_num}:{col_num + 1}", "",
              f"  {consumed_lines[-1]}{remaining_line}", f"  {' '*col_num}^")

    # Parse an entire assembly file.
    def parse_file(self, file: str):
        self.current_file = file
        with open(file, "r") as i:
            self.current_input = i.read()
            self.current_contents = self.current_input
        self.parse_program()
        self.current_file = None
        self.current_input = None
        self.current_contents = None

    # Parse an entire program.
    def parse_program(self):
        self.skip()
        while len(self.current_input) > 0:
            inst = self.parse_instruction()
            self.program.append(inst)

    # Parse an instruction.
    def parse_instruction(self) -> Instruction:
        # Labels
        if m := self.consume_regex(r'([a-zA-Z0-9_]+):'):
            label = Operand(OperandKind.Label, m[1])
            return Instruction(D_LABEL, [label])

        # Directives
        if self.consume_identifier(r'\.org'):
            imm = self.parse_immediate()
            return Instruction(D_ORG, [imm])

        # Instructions
        if m := self.consume_regex(r'\b([a-zA-Z0-9_]+)\b'):
            name = m[1]
        else:
            self.error("expected instruction name")

        opcode = OPCODES_BY_NAME.get(name)
        if opcode is None:
            self.error("unknown instruction")

        operands = []
        needs_comma = False

        # Parse condition code.
        if opcode.cond != CondMode.Unused:
            self.parse_regex(r'\.')
            operands.append(self.parse_condition())

        # Parse RD operand.
        if opcode.rd != RdMode.Unused:
            operands.append(self.parse_register())
            needs_comma = True

        # Parse RS operand or immediate.
        if opcode.rs != RsMode.Unused:
            if needs_comma:
                self.parse_regex(r',')
            needs_comma = True
        if opcode.rs == RsMode.Unused:
            pass
        elif opcode.rs == RsMode.R8:
            operands.append(self.parse_register())
        elif opcode.rs == RsMode.R16:
            operands.append(self.parse_register_pair())
        elif opcode.rs in (RsMode.Imm8, RsMode.SImm4):
            operands.append(self.parse_immediate())
        elif opcode.rs == RsMode.JImm8:
            operands.append(self.parse_offset())
        else:
            assert False, f"unhandled {opcode.rs}"

        return Instruction(opcode, operands)

    # Parse a register operand, like `r0`.
    def parse_register(self) -> Operand:
        idx = int(self.parse_regex(r'r([0-6])\b', "expected a register")[1])
        return Operand(OperandKind.Reg, idx)

    # Parse a register pair, like `r1r0`.
    def parse_register_pair(self) -> Operand:
        m = self.parse_regex(r'r([0-6])r([0-6])\b',
                             "expected a 16 bit register pair")
        lo = int(m[2])
        hi = int(m[1])
        if hi != lo + 1:
            self.error(
                f"registers in 16 bit register pair must be consecutive; got {m[0]}"
            )
        return Operand(OperandKind.RegPair, lo)

    # Parse an immediate, like `42` or `0xbeef`.
    def parse_immediate(self) -> Operand:
        negative = False
        if m := self.consume_regex(r'[+-]', skip=False):
            negative = m[0] == '-'
        base = 10
        digits = r'[0-9_]+\b'
        if m := self.consume_regex(r'0[xob]', skip=False):
            if m[0] == "0x":
                base = 16
                digits = r'[0-9a-fA-F_]+\b'
            elif m[0] == "0o":
                base = 8
                digits = r'[0-7_]+\b'
            elif m[0] == "0b":
                base = 2
                digits = r'[01_]+\b'
        value = self.parse_regex(digits, f"expected base-{base} integer")
        value = int(value[0].replace("_", ""), base)
        if negative:
            value = -value
        return Operand(OperandKind.Imm, value)

    # Parse a relative jump offset, like `42` or `label`.
    def parse_offset(self) -> Operand:
        # Parse anything that looks like an integer with optional `+` or `-`
        # sign, or a label like `start` or `4f`.
        m = self.parse_regex(r'([+-])?([0-9a-zA-Z_]+)',
                             "expected integer or label")
        sign = m[1]
        text = m[2]

        # Handle integers.
        base = None
        if m := re.match(r'^[0-9_]+$', text):
            base = 10
        elif m := re.match(r'^0x[0-9a-fA-F_]+$', text):
            base = 16
        elif m := re.match(r'^0o[0-7_]+$', text):
            base = 8
        elif m := re.match(r'^0b[0-1_]+$', text):
            base = 2
        if base is not None:
            value = int(text.replace("_", ""), base)
            if sign == "-":
                value = -value
            return Operand(OperandKind.Imm, value)
        if sign is not None:
            self.error(f"expected integer after `{sign}`")

        # Otherwise this is a label.
        return Operand(OperandKind.Offset, Offset(text))

    # Parse a condition code, like `c` or `ugt`.
    def parse_condition(self) -> Operand:
        if m := self.consume_regex(r'[a-z]+'):
            if cond := CONDITION_BY_NAME.get(m[0]):
                return Operand(OperandKind.Cond, cond)
        self.error("expected condition code")

    # Skip over whitespace and comments.
    def skip(self):
        while True:
            # Skip whitespace.
            if self.consume_regex(r'\s+', skip=False):
                continue
            # Skip single-line comments, such as `#` and `//`.
            if self.consume_regex(r'(#|//).*[\n$]', skip=False):
                continue
            # Skip multi-line comments, such as `/*...*/`.
            if self.consume_regex(r'(?s)/\*.*\*/', skip=False):
                continue
            break

    # If a regular expression matches at the current position in the input,
    # consume the matched string and return the regex match object. If `skip` is
    # set to true, also skip over whitespace following the match.
    def consume_regex(self, regex, skip: bool = True) -> Optional[re.Match]:
        if m := re.match(regex, self.current_input):
            self.current_input = self.current_input[len(m[0]):]
            if skip:
                self.skip()
            return m
        return None

    # Consume an identifier, like `ldi` or `nop`.
    def consume_identifier(self, identifier: str) -> bool:
        if self.consume_regex(rf'{identifier}\b'):
            return True
        return False

    # Parse a regular expression. Print an error otherwise.
    def parse_regex(self,
                    regex,
                    error_message: Optional[str] = None) -> re.Match:
        if m := self.consume_regex(regex):
            return m
        self.error(error_message or f"expected '{regex}'")


# A printer that converts a list of `Instruction` objects into human-readable
# assembly text.
@dataclass
class AssemblyPrinter:
    program: List[Instruction]

    def print(self) -> str:
        self.emit_address = any(i.address is not None for i in self.program)
        self.emit_encoding = any(i.encoding is not None for i in self.program)
        self.output = ""
        for i in self.program:
            self.print_instruction(i)
            self.emit("\n")
        s = self.output
        self.output = None
        return s

    def print_instruction(self, inst: Instruction):
        # Print the address prefix.
        if self.emit_address:
            address = "????"
            if inst.address is not None:
                address = f"{inst.address:04X}"
            self.emit(f"{address}:  ")

        # Print the instruction encoding.
        if self.emit_encoding:
            encoding = "    "
            if inst.encoding is not None:
                encoding = f"{inst.encoding:04X}"
            self.emit(f"{encoding}  ")

        # Directives
        if inst.opcode == D_ORG:
            self.emit(".org ")
            self.print_operand(inst.operands[0], hint_addr=True)
            return

        if inst.opcode == D_LABEL:
            self.emit(inst.operands[0].value)
            self.emit(":")
            return

        # Actual instructions
        opcode = str(inst.opcode.name)

        # Append condition code directly to the opcode.
        operands = list(inst.operands)
        if inst.opcode.cond != CondMode.Unused:
            opcode += "."
            opcode += operands.pop(0).value.name.lower()

        opcode += " "
        self.print_opcode(opcode)

        # Print the RD operand.
        needs_comma = False
        if inst.opcode.rd != RdMode.Unused:
            self.print_operand(operands.pop(0))
            needs_comma = True

        # Print the RS operand or immediate.
        if inst.opcode.rs != RsMode.Unused:
            if needs_comma:
                self.emit(", ")
            if inst.opcode.rs == RsMode.JImm8:
                operand = operands.pop(0)
                self.print_operand(operand, hint_relative=True)
                self.print_target_comment(inst, operand)
            else:
                self.print_operand(operands.pop(0))

    def print_target_comment(self, inst: Instruction, operand: Operand):
        offset = None
        if isinstance(operand.value, Offset):
            offset = operand.value.offset
        else:
            offset = operand.value
        if inst.address is not None and offset is not None:
            self.emit(f"  # {inst.address+offset:04X}")

    def print_opcode(self, text: str):
        self.emit(f"    {text:<9s}")

    def print_operand(self,
                      operand: Operand,
                      hint_relative: bool = False,
                      hint_addr: bool = False):
        if operand.kind == OperandKind.Imm:
            if hint_addr:
                self.emit(f"0x{operand.value:04X}")
            elif operand.value >= 0 and hint_relative:
                self.emit(f"+{operand.value}")
            else:
                self.emit(f"{operand.value}")
        elif operand.kind == OperandKind.Reg:
            self.emit(f"r{operand.value}")
        elif operand.kind == OperandKind.RegPair:
            self.emit(f"r{operand.value + 1}r{operand.value}")
        elif operand.kind == OperandKind.Cond:
            self.emit(operand.value.name.lower())
        elif operand.kind == OperandKind.Offset:
            self.emit(operand.value.name)
        else:
            self.emit(f"<{operand}>")

    def emit(self, text: str):
        self.output += text


# Utility to resolve names in expressions.
@dataclass
class Resolver:
    # A map of label names to the directives that define them.
    labels: Dict[str, Instruction] = field(default_factory=dict)
    # A map of relative labels to the list of directives that define that label.
    relative_labels: Dict[str, List[Tuple[int, Instruction]]] = field(
        default_factory=dict)

    def resolve_program(self, program: List[Instruction]):
        # Register the labels in the program.
        for index, inst in enumerate(program):
            if inst.opcode == D_LABEL:
                self.register_label(index, inst)

        # Resolve the labels in instructions.
        for index, inst in enumerate(program):
            self.resolve_instruction(index, inst)

    def register_label(self, index: int, inst: Instruction):
        label: str = inst.operands[0].value

        # If the label consists only of digits, like `42:`, treat it as a
        # relative label. It may have multiple definitions and instructions
        # always refer to the closest definition before or after. We therefore
        # keep an entire list of these relative labels.
        if label.isdigit():
            self.relative_labels.setdefault(label, []).append((index, inst))
            return

        # Otherwise treat this as an absolute label with a unique name. If the
        # name already exists, emit an error.
        if label in self.labels:
            error(f"label `{label}` already defined", inst)
        self.labels[label] = inst

    def resolve_instruction(self, index: int, inst: Instruction):
        for operand in inst.operands:
            if operand.kind == OperandKind.Offset:
                self.resolve_offset(index, inst, operand.value)

    def resolve_offset(self, index: int, inst: Instruction, offset: Offset):
        # Handle relative labels of the form `2f` or `1b`. The `f` or `b` suffix
        # indicates whether we pick the first occurrence of the label before or
        # following the current instruction.
        if m := re.match(r'^([0-9]+)([bf])$', offset.name):
            label = m[1]
            labels = self.relative_labels.get(label) or []
            if m[2] == "f":
                # Use the first label with index after the current instruction.
                for label_index, label_inst in labels:
                    if label_index >= index:
                        offset.binding = label_inst
                        return
            else:
                # Use the first label with index before the current instruction.
                for label_index, label_inst in reversed(labels):
                    if label_index <= index:
                        offset.binding = label_inst
                        return
            side = "after" if m[2] == "f" else "before"
            error(f"unknown label `{label}` {side} instruction", inst)

        # Handle regular labels.
        if label_inst := self.labels.get(offset.name):
            offset.binding = label_inst
            return
        error(f"unknown label `{offset.name}`", inst)


# Utility to compute the exact addresses of instructions in the binary.
@dataclass
class Layouter:
    current_address: int = 0

    def layout_program(self, program: List[Instruction]):
        for inst in program:
            self.layout_instruction(inst)

    def layout_instruction(self, inst: Instruction):
        if inst.opcode == D_ORG:
            org_address = inst.operands[0].value
            if self.current_address > org_address:
                error(
                    f"org directive address 0x{org_address:04X} is behind current address 0x{self.current_address:04X}",
                    inst)
            self.current_address = org_address
            inst.address = org_address
            return

        if inst.opcode == D_LABEL:
            inst.address = self.current_address
            return

        inst.address = self.current_address
        self.current_address += 2


# Utility to evaluate the expressions in a program.
@dataclass
class Evaluator:

    def evaluate_program(self, program: List[Instruction]):
        for inst in program:
            self.evaluate_instruction(inst)

    def evaluate_instruction(self, inst: Instruction):
        for operand in inst.operands:
            if isinstance(operand.value, Offset):
                operand.value.offset = operand.value.binding.address - inst.address


# An encoder that computes the binary encoding for every instruction in a
# program.
class InstructionEncoder:

    def error(self, message: str):
        error(message, self.inst)

    def encode_program(self, program: List[Instruction]):
        for inst in program:
            self.inst = inst
            self.encoding = 0
            self.encode_instruction(inst)
            inst.encoding = self.encoding

    def encode_instruction(self, inst: Instruction):
        opcode = inst.opcode

        # Special handling for directives
        if opcode in (D_ORG, D_LABEL):
            self.encoding = None
            return

        # Encode func0 bits.
        assert opcode.func0 is not None, f"{opcode} missing func0"
        self.encode_bits(0, 4, opcode.func0)

        # Encode the condition code.
        covers_func1 = False
        covers_func2 = False
        operands = list(inst.operands)
        if opcode.cond == CondMode.Cond1:
            self.encode_cond1(operands.pop(0))
            covers_func2 = True
        elif opcode.cond == CondMode.Cond2:
            self.encode_cond2(operands.pop(0))
            covers_func1 = True

        # Encode RD operand or func2 bits.
        if opcode.rd != RdMode.Unused:
            self.encode_rd(operands.pop(0))
        elif not covers_func2:
            assert opcode.func2 is not None, f"{opcode} missing func2"
            self.encode_bits(4, 4, opcode.func2)

        # Encode RS operand, immediate, or func3 bits.
        if opcode.rs == RsMode.R8:
            self.encode_rs(operands.pop(0))
        elif opcode.rs == RsMode.R16:
            self.encode_rs16(operands.pop(0))
        elif opcode.rs == RsMode.Imm8:
            self.encode_imm8(operands.pop(0))
            covers_func1 = True
        elif opcode.rs == RsMode.JImm8:
            self.encode_simm8(operands.pop(0))
            covers_func1 = True
        elif opcode.rs == RsMode.SImm4:
            self.encode_simm4(operands.pop(0))
        else:
            assert opcode.func3 is not None, f"{opcode} missing func3"
            self.encode_bits(8, 4, opcode.func3)

        # Encode func1 bits if not covered by immediate.
        if not covers_func1:
            assert opcode.func1 is not None, f"{opcode} missing func1"
            self.encode_bits(12, 4, opcode.func1)

    # Store the `value` into the instruction bits from `offset` to
    # `offset+length`.
    def encode_bits(self, offset: int, length: int, value: int):
        assert value is not None
        assert (offset >= 0)
        assert (length >= 0)
        assert (offset + length <= 16)
        assert (value >= 0)
        assert (value < 2**length)
        mask = ((1 << length) - 1) << offset
        self.encoding &= ~mask
        self.encoding |= value << offset

    # Encode a register operand in the `rd` field.
    def encode_rd(self, operand: Operand):
        if operand.kind != OperandKind.Reg or operand.value < 0 or operand.value > 6:
            self.error(f"expected rd register operand; got {operand}")
        self.encode_bits(4, 4, operand.value + 1)

    # Encode a register operand in the `rs` field.
    def encode_rs(self, operand: Operand):
        if operand.kind != OperandKind.Reg or operand.value < 0 or operand.value > 6:
            self.error(f"expected rs register operand; got {operand}")
        self.encode_bits(8, 4, operand.value + 1)

    # Encode a 16 bit register operand in the `rs16` field.
    def encode_rs16(self, operand: Operand):
        if operand.kind != OperandKind.RegPair or operand.value < 0 or operand.value > 5:
            self.error(f"expected rs16 register operand; got {operand}")
        self.encode_bits(8, 4, operand.value + 1)

    # Encode an immediate operand in the 8 bit immediate field.
    def encode_imm8(self, operand: Operand):
        value = self.check_imm(operand, -128, 256)
        self.encode_bits(8, 8, value & 0xFF)

    # Encode a signed immediate operand in the 8 bit immediate field.
    def encode_simm8(self, operand: Operand):
        value = self.check_imm(operand, -128, 128)
        self.encode_bits(8, 8, value & 0xFF)

    # Encode a signed immediate operand in the 4 bit immediate field.
    def encode_simm4(self, operand: Operand):
        value = self.check_imm(operand, -8, 8)
        self.encode_bits(8, 4, value & 0xF)

    # Encode a condition code in the `rd` field of the instruction.
    def encode_cond1(self, operand: Operand):
        if operand.kind != OperandKind.Cond:
            self.error(f"expected cond operand; got {operand}")
        self.encode_bits(4, 4, CONDITION_ENCODING[operand.value])

    # Encode a condition code in the top four bits of the instruction.
    def encode_cond2(self, operand: Operand):
        if operand.kind != OperandKind.Cond:
            self.error(f"expected cond operand; got {operand}")
        self.encode_bits(12, 4, CONDITION_ENCODING[operand.value])

    # Error if an operand is not an immediate, or the immediate is less than
    # `lower` or greater than or equal to `upper`.
    def check_imm(self, operand: Operand, lower: int, upper: int) -> int:
        if operand.kind == OperandKind.Imm:
            value = operand.value
        elif operand.kind == OperandKind.Offset:
            value = operand.value.offset
        else:
            self.error(f"expected immediate operand; got {operand}")
        if value < lower or value >= upper:
            self.error(
                f"immediate value {value} is out of bounds; expected {lower} <= value < {upper}"
            )
        return value


# Convert a list of instructions to their binary representation. The
# instructions must have already been encoded with an `InstructionEncoder`.
def convert_program_to_bytes(program: List[Instruction],
                             output_size: Optional[int] = None) -> bytes:
    buffer = bytes()
    for inst in program:
        if inst.encoding is None or inst.address is None:
            continue
        if inst.address > len(buffer):
            buffer += bytes(inst.address - len(buffer))
        buffer += bytes([inst.encoding & 0xFF, (inst.encoding >> 8) & 0xFF])
    if output_size is not None:
        if len(buffer) > output_size:
            error(
                f"binary size {len(buffer)} exceeds configured output size {output_size}"
            )
        buffer += bytes(output_size - len(buffer))
    return buffer


# Print a blob of bytes as a hex dump.
def print_binary_hexdump(binary: bytes, bytes_per_line: int = 8):
    offset_width = len(f"{len(binary):x}")
    zeros = False
    for offset in range(0, len(binary), bytes_per_line):
        chunk = binary[offset:offset + bytes_per_line]
        if all(byte == 0 for byte in chunk):
            if not zeros:
                print(f"{'.'*offset_width}.  [zeros]")
            zeros = True
            continue
        zeros = False
        str_bytes = " ".join(f"{byte:02X}" for byte in chunk)
        str_chars = "".join(
            chr(byte) if byte in range(32, 128) else "." for byte in chunk)
        print(
            f"{offset:0{offset_width}X}:  {str_bytes:{3*bytes_per_line-1}}  {str_chars}"
        )
    print(f"{len(binary):0{offset_width}X}:  [end of binary]")


# Parse the command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument("inputs",
                    metavar="INPUT",
                    nargs="*",
                    help="input files to assemble")
parser.add_argument("-o", "--output", type=str, help="output file")
parser.add_argument("-s", "--size", type=int, help="size of the output binary")
parser.add_argument("-v",
                    "--print-assembly",
                    action="store_true",
                    help="print final assembly")
parser.add_argument("-x",
                    "--print-binary",
                    action="store_true",
                    help="print hexdump of final binary")
args = parser.parse_args()

# Parse the input files.
parser = AssemblyParser()
for i in args.inputs:
    parser.parse_file(i)

# Resolve the names of labels.
Resolver().resolve_program(parser.program)

# Compute the addresses of each instruction.
Layouter().layout_program(parser.program)

# Evaluate all expressions.
Evaluator().evaluate_program(parser.program)

# Compute the binary encoding of each instruction.
InstructionEncoder().encode_program(parser.program)

# Print the assembly if requested.
if args.print_assembly:
    print(AssemblyPrinter(parser.program).print())

# Collect the encoded instructions into a blob of bytes.
binary = convert_program_to_bytes(parser.program, args.size)

# Write the binary to an output file if requested.
if args.output:
    with open(args.output, "wb") as f:
        f.write(binary)

# Print a hexdump of the binary if no output file was provided or explicitly
# requested by the user.
if not args.output or args.print_binary:
    print_binary_hexdump(binary)
