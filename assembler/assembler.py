#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from termcolor import colored
from typing import *


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


# An instruction opcode.
class Opcode(Enum):
    # Actual instructions
    NOP = auto()
    LDI = auto()
    MV = auto()
    JR = auto()
    J = auto()
    JRO = auto()
    BR = auto()
    B = auto()
    BRO = auto()
    LCDCW = auto()
    LCDDW = auto()
    LCDCR = auto()
    LCDDR = auto()
    NOT = auto()
    NEG = auto()
    ADD = auto()
    ADDI = auto()
    SUB = auto()
    ADDC = auto()
    ADDCI = auto()
    SUBC = auto()
    SHLL = auto()
    SHLC = auto()
    SHRL = auto()
    SHRC = auto()
    SHRA = auto()
    AND = auto()
    ANDI = auto()
    OR = auto()
    ORI = auto()
    XOR = auto()
    XORI = auto()
    CMP = auto()
    CMPI = auto()
    TEST = auto()
    TESTI = auto()
    FSWAP = auto()
    FR = auto()
    FW = auto()
    CMV = auto()
    CLDI = auto()

    # Pseudo-instructions
    HALT = auto()

    # Assembler directives
    D_ORG = auto()
    D_LABEL = auto()


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
        s = self.opcode.name
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
            return Instruction(Opcode.D_LABEL, [label])

        # Actual instructions
        if self.consume_identifier("nop"):
            return Instruction(Opcode.NOP)

        if self.consume_identifier("ldi"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.LDI, [rd, imm])

        if self.consume_identifier("mv"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.MV, [rd, rs])

        if self.consume_identifier("jr"):
            rs16 = self.parse_register_pair()
            return Instruction(Opcode.JR, [rs16])

        if self.consume_identifier("j"):
            offset = self.parse_offset()
            return Instruction(Opcode.J, [offset])

        if self.consume_identifier("jro"):
            rs = self.parse_register()
            return Instruction(Opcode.JRO, [rs])

        if self.consume_identifier("br"):
            self.parse_regex(r'\.')
            cond = self.parse_condition()
            rs16 = self.parse_register_pair()
            return Instruction(Opcode.BR, [cond, rs16])

        if self.consume_identifier("b"):
            self.parse_regex(r'\.')
            cond = self.parse_condition()
            offset = self.parse_offset()
            return Instruction(Opcode.B, [cond, offset])

        if self.consume_identifier("bro"):
            self.parse_regex(r'\.')
            cond = self.parse_condition()
            rs = self.parse_register()
            return Instruction(Opcode.BRO, [cond, rs])

        if self.consume_identifier("lcdcw"):
            rd = self.parse_register()
            return Instruction(Opcode.LCDCW, [rd])

        if self.consume_identifier("lcddw"):
            rd = self.parse_register()
            return Instruction(Opcode.LCDDW, [rd])

        if self.consume_identifier("lcdcr"):
            rd = self.parse_register()
            return Instruction(Opcode.LCDCR, [rd])

        if self.consume_identifier("lcddr"):
            rd = self.parse_register()
            return Instruction(Opcode.LCDDR, [rd])

        if self.consume_identifier("not"):
            rd = self.parse_register()
            return Instruction(Opcode.NOT, [rd])

        if self.consume_identifier("neg"):
            rd = self.parse_register()
            return Instruction(Opcode.NEG, [rd])

        if self.consume_identifier("add"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.ADD, [rd, rs])

        if self.consume_identifier("addi"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.ADDI, [rd, imm])

        if self.consume_identifier("sub"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.SUB, [rd, rs])

        if self.consume_identifier("addc"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.ADDC, [rd, rs])

        if self.consume_identifier("addci"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.ADDCI, [rd, imm])

        if self.consume_identifier("subc"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.SUBC, [rd, rs])

        if self.consume_identifier("shll"):
            rd = self.parse_register()
            return Instruction(Opcode.SHLL, [rd])

        if self.consume_identifier("shlc"):
            rd = self.parse_register()
            return Instruction(Opcode.SHLC, [rd])

        if self.consume_identifier("shrl"):
            rd = self.parse_register()
            return Instruction(Opcode.SHRL, [rd])

        if self.consume_identifier("shrc"):
            rd = self.parse_register()
            return Instruction(Opcode.SHRC, [rd])

        if self.consume_identifier("shra"):
            rd = self.parse_register()
            return Instruction(Opcode.SHRA, [rd])

        if self.consume_identifier("and"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.AND, [rd, rs])

        if self.consume_identifier("andi"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.ANDI, [rd, imm])

        if self.consume_identifier("or"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.OR, [rd, rs])

        if self.consume_identifier("ori"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.ORI, [rd, imm])

        if self.consume_identifier("xor"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.XOR, [rd, rs])

        if self.consume_identifier("xori"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.XORI, [rd, imm])

        if self.consume_identifier("cmp"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.CMP, [rd, rs])

        if self.consume_identifier("cmpi"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.CMPI, [rd, imm])

        if self.consume_identifier("test"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.TEST, [rd, rs])

        if self.consume_identifier("testi"):
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.TESTI, [rd, imm])

        if self.consume_identifier("fswap"):
            rd = self.parse_register()
            return Instruction(Opcode.FSWAP, [rd])

        if self.consume_identifier("fr"):
            rd = self.parse_register()
            return Instruction(Opcode.FR, [rd])

        if self.consume_identifier("fw"):
            rd = self.parse_register()
            return Instruction(Opcode.FW, [rd])

        if self.consume_identifier("cmv"):
            self.parse_regex(r'\.')
            cond = self.parse_condition()
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.CMV, [cond, rd, rs])

        if self.consume_identifier("cldi"):
            self.parse_regex(r'\.')
            cond = self.parse_condition()
            rd = self.parse_register()
            self.parse_regex(r',')
            imm = self.parse_immediate()
            return Instruction(Opcode.CLDI, [cond, rd, imm])

        # Pseudo-instructions
        if self.consume_identifier("halt"):
            return Instruction(Opcode.HALT)

        # Directives
        if self.consume_identifier(r'\.org'):
            imm = self.parse_immediate()
            return Instruction(Opcode.D_ORG, [imm])

        self.error("unknown instruction")

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

        # Actual instructions
        if inst.opcode == Opcode.NOP:
            self.print_opcode("nop")
            return

        if inst.opcode == Opcode.LDI:
            self.print_opcode("ldi ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.MV:
            self.print_opcode("mv ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.JR:
            self.print_opcode("jr ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.J:
            self.print_opcode("j ")
            self.print_operand(inst.operands[0], hint_relative=True)
            self.print_target_comment(inst, inst.operands[0])
            return

        if inst.opcode == Opcode.JRO:
            self.print_opcode("jro ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.BR:
            cond = inst.operands[0].value.name.lower()
            self.print_opcode(f"br.{cond} ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.B:
            cond = inst.operands[0].value.name.lower()
            self.print_opcode(f"b.{cond} ")
            self.print_operand(inst.operands[1], hint_relative=True)
            self.print_target_comment(inst, inst.operands[1])
            return

        if inst.opcode == Opcode.BRO:
            cond = inst.operands[0].value.name.lower()
            self.print_opcode(f"bro.{cond} ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.LCDCW:
            self.print_opcode("lcdcw ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDDW:
            self.print_opcode("lcddw ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDCR:
            self.print_opcode("lcdcr ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDDR:
            self.print_opcode("lcddr ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.NOT:
            self.print_opcode("not ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.NEG:
            self.print_opcode("neg ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.ADD:
            self.print_opcode("add ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDI:
            self.print_opcode("addi ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.SUB:
            self.print_opcode("sub ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDC:
            self.print_opcode("addc ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDCI:
            self.print_opcode("addci ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.SUBC:
            self.print_opcode("subc ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.SHLL:
            self.print_opcode("shll ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.SHLC:
            self.print_opcode("shlc ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRL:
            self.print_opcode("shrl ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRC:
            self.print_opcode("shrc ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRA:
            self.print_opcode("shra ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.AND:
            self.print_opcode("and ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.ANDI:
            self.print_opcode("andi ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.OR:
            self.print_opcode("or ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.ORI:
            self.print_opcode("ori ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.XOR:
            self.print_opcode("xor ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.XORI:
            self.print_opcode("xori ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.CMP:
            self.print_opcode("cmp ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.CMPI:
            self.print_opcode("cmpi ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.TEST:
            self.print_opcode("test ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.TESTI:
            self.print_opcode("testi ")
            self.print_operand(inst.operands[0])
            self.emit(", ")
            self.print_operand(inst.operands[1])
            return

        if inst.opcode == Opcode.FSWAP:
            self.print_opcode("fswap ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.FR:
            self.print_opcode("fr ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.FW:
            self.print_opcode("fw ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.CMV:
            cond = inst.operands[0].value.name.lower()
            self.print_opcode(f"cmv.{cond} ")
            self.print_operand(inst.operands[1])
            self.emit(", ")
            self.print_operand(inst.operands[2])
            return

        if inst.opcode == Opcode.CLDI:
            cond = inst.operands[0].value.name.lower()
            self.print_opcode(f"cldi.{cond} ")
            self.print_operand(inst.operands[1])
            self.emit(", ")
            self.print_operand(inst.operands[2])
            return

        # Pseudo-instructions
        if inst.opcode == Opcode.HALT:
            self.print_opcode("halt")
            return

        # Directives
        if inst.opcode == Opcode.D_ORG:
            self.emit(".org ")
            self.print_operand(inst.operands[0], hint_addr=True)
            return

        if inst.opcode == Opcode.D_LABEL:
            self.emit(inst.operands[0].value)
            self.emit(":")
            return

        self.emit(f"<{inst}>")

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
            if inst.opcode == Opcode.D_LABEL:
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
        if inst.opcode == Opcode.D_ORG:
            org_address = inst.operands[0].value
            if self.current_address > org_address:
                error(
                    f"org directive address 0x{org_address:04X} is behind current address 0x{self.current_address:04X}",
                    inst)
            self.current_address = org_address
            inst.address = org_address
            return

        if inst.opcode == Opcode.D_LABEL:
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
        # Actual instructions
        if inst.opcode == Opcode.NOP:
            self.encode_bits(0, 16, 0x0000)
            return

        if inst.opcode == Opcode.LDI:
            self.encode_bits(0, 4, 8)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.MV:
            self.encode_bits(0, 4, 0)
            self.encode_bits(12, 4, 1)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.JR:
            self.encode_bits(0, 4, 0)
            self.encode_bits(4, 4, 0)
            self.encode_bits(12, 4, 3)
            self.encode_rs16(inst.operands[0])
            return

        if inst.opcode == Opcode.J:
            self.encode_bits(0, 4, 9)
            self.encode_bits(4, 4, 0)
            self.encode_simm8(inst.operands[0])
            return

        if inst.opcode == Opcode.JRO:
            self.encode_bits(0, 4, 0)
            self.encode_bits(4, 4, 0)
            self.encode_bits(12, 4, 2)
            self.encode_rs(inst.operands[0])
            return

        if inst.opcode == Opcode.BR:
            self.encode_bits(0, 4, 0)
            self.encode_cond1(inst.operands[0])
            self.encode_bits(12, 4, 3)
            self.encode_rs16(inst.operands[1])
            return

        if inst.opcode == Opcode.B:
            self.encode_bits(0, 4, 9)
            self.encode_cond1(inst.operands[0])
            self.encode_simm8(inst.operands[1])
            return

        if inst.opcode == Opcode.BRO:
            self.encode_bits(0, 4, 0)
            self.encode_cond1(inst.operands[0])
            self.encode_bits(12, 4, 2)
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.LCDCW:
            self.encode_bits(0, 4, 0)
            self.encode_bits(12, 4, 4)
            self.encode_bits(8, 4, 0)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDDW:
            self.encode_bits(0, 4, 0)
            self.encode_bits(12, 4, 4)
            self.encode_bits(8, 4, 1)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDCR:
            self.encode_bits(0, 4, 0)
            self.encode_bits(12, 4, 4)
            self.encode_bits(8, 4, 2)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.LCDDR:
            self.encode_bits(0, 4, 0)
            self.encode_bits(12, 4, 4)
            self.encode_bits(8, 4, 3)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.NOT:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 0)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.NEG:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 1)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.ADD:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 1)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDI:
            self.encode_bits(0, 4, 12)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.SUB:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 3)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDC:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 2)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.ADDCI:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 10)
            self.encode_rd(inst.operands[0])
            self.encode_simm4(inst.operands[1])
            return

        if inst.opcode == Opcode.SUBC:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.SHLL:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 2)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.SHLC:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 3)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRL:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 4)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRC:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 5)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.SHRA:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 6)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.AND:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 5)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.ANDI:
            self.encode_bits(0, 4, 13)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.OR:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 6)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.ORI:
            self.encode_bits(0, 4, 14)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.XOR:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 7)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.XORI:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 11)
            self.encode_rd(inst.operands[0])
            self.encode_simm4(inst.operands[1])
            return

        if inst.opcode == Opcode.CMP:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 8)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.CMPI:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 12)
            self.encode_rd(inst.operands[0])
            self.encode_simm4(inst.operands[1])
            return

        if inst.opcode == Opcode.TEST:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 9)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.TESTI:
            self.encode_bits(0, 4, 15)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.FSWAP:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 7)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.FR:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 8)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.FW:
            self.encode_bits(0, 4, 1)
            self.encode_bits(12, 4, 0)
            self.encode_bits(8, 4, 9)
            self.encode_rd(inst.operands[0])
            return

        if inst.opcode == Opcode.CMV:
            self.encode_bits(0, 4, 2)
            self.encode_cond2(inst.operands[0])
            self.encode_rd(inst.operands[1])
            self.encode_rs(inst.operands[2])
            return

        if inst.opcode == Opcode.CLDI:
            self.encode_bits(0, 4, 3)
            self.encode_cond2(inst.operands[0])
            self.encode_rd(inst.operands[1])
            self.encode_simm4(inst.operands[2])
            return

        # Pseudo-instructions
        if inst.opcode == Opcode.HALT:
            self.encode_bits(0, 16, 0x0009)
            return

        # Directives
        if inst.opcode in (Opcode.D_ORG, Opcode.D_LABEL):
            self.encoding = None
            return

        self.error("unencodable instruction")

    # Store the `value` into the instruction bits from `offset` to
    # `offset+length`.
    def encode_bits(self, offset: int, length: int, value: int):
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
