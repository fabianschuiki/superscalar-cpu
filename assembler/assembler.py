#!/usr/bin/env python3
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
    JABSR = auto()
    JRELI = auto()
    JRELR = auto()
    NOT = auto()
    NEG = auto()
    ADD = auto()
    SUB = auto()
    ADDC = auto()
    SUBC = auto()
    SHLL = auto()
    SHLC = auto()
    SHRL = auto()
    SHRC = auto()
    SHRA = auto()
    AND = auto()
    OR = auto()
    XOR = auto()

    # Pseudo-instructions
    HALT = auto()

    # Assembler directives
    D_ORG = auto()


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

        if self.consume_identifier("jabsr"):
            rs16 = self.parse_register_pair()
            return Instruction(Opcode.JABSR, [rs16])

        if self.consume_identifier("jreli"):
            imm = self.parse_immediate()
            return Instruction(Opcode.JRELI, [imm])

        if self.consume_identifier("jrelr"):
            rs = self.parse_register()
            return Instruction(Opcode.JRELR, [rs])

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

        if self.consume_identifier("or"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.OR, [rd, rs])

        if self.consume_identifier("xor"):
            rd = self.parse_register()
            self.parse_regex(r',')
            rs = self.parse_register()
            return Instruction(Opcode.XOR, [rd, rs])

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

    # Parse a register pair, like `r0r1`.
    def parse_register_pair(self) -> Operand:
        m = self.parse_regex(r'r([0-6])r([0-6])\b',
                             "expected a 16 bit register pair")
        lo = int(m[1])
        hi = int(m[2])
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

        if inst.opcode == Opcode.JABSR:
            self.print_opcode("jabsr ")
            self.print_operand(inst.operands[0])
            return

        if inst.opcode == Opcode.JRELI:
            self.print_opcode("jreli ")
            self.print_operand(inst.operands[0], hint_relative=True)
            if inst.address is not None:
                target_addr = inst.address + inst.operands[0].value
                self.emit(f"  # {target_addr:04X}")
            return

        if inst.opcode == Opcode.JRELR:
            self.print_opcode("jrelr ")
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

        if inst.opcode == Opcode.OR:
            self.print_opcode("or ")
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

        # Pseudo-instructions
        if inst.opcode == Opcode.HALT:
            self.print_opcode("halt")
            return

        # Directives
        if inst.opcode == Opcode.D_ORG:
            self.emit(".org ")
            self.print_operand(inst.operands[0], hint_addr=True)
            return

        self.emit(f"<{inst}>")

    def print_opcode(self, text: str):
        self.emit(f"    {text:<7s}")

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
            self.emit(f"r{operand.value}r{operand.value + 1}")

    def emit(self, text: str):
        self.output += text


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

        inst.address = self.current_address
        self.current_address += 2


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
            self.encode_bits(0, 4, 0x8)
            self.encode_rd(inst.operands[0])
            self.encode_imm8(inst.operands[1])
            return

        if inst.opcode == Opcode.MV:
            self.encode_bits(0, 4, 0x0)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            return

        if inst.opcode == Opcode.JABSR:
            self.encode_bits(0, 8, 0x02)
            self.encode_rs16(inst.operands[0])
            return

        if inst.opcode == Opcode.JRELI:
            self.encode_bits(0, 8, 0x09)
            self.encode_simm8(inst.operands[0])
            return

        if inst.opcode == Opcode.JRELR:
            self.encode_bits(0, 8, 0x01)
            self.encode_rs(inst.operands[0])
            return

        if inst.opcode == Opcode.NOT:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b0100)
            return

        if inst.opcode == Opcode.NEG:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b0101)
            return

        if inst.opcode == Opcode.ADD:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b0000)
            return

        if inst.opcode == Opcode.SUB:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b0010)
            return

        if inst.opcode == Opcode.ADDC:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b0001)
            return

        if inst.opcode == Opcode.SUBC:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b0011)
            return

        if inst.opcode == Opcode.SHLL:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b0110)
            return

        if inst.opcode == Opcode.SHLC:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b0111)
            return

        if inst.opcode == Opcode.SHRL:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b1000)
            return

        if inst.opcode == Opcode.SHRC:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b1001)
            return

        if inst.opcode == Opcode.SHRA:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_bits(12, 4, 0b1010)
            return

        if inst.opcode == Opcode.AND:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b1101)
            return

        if inst.opcode == Opcode.OR:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b1110)
            return

        if inst.opcode == Opcode.XOR:
            self.encode_bits(0, 4, 0x4)
            self.encode_rd(inst.operands[0])
            self.encode_rs(inst.operands[1])
            self.encode_bits(12, 4, 0b1111)
            return

        # Pseudo-instructions
        if inst.opcode == Opcode.HALT:
            self.encode_bits(0, 16, 0x0009)
            return

        # Directives
        if inst.opcode == Opcode.D_ORG:
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

    # Encode an immediate operand in the 8 bit immediate field
    def encode_imm8(self, operand: Operand):
        self.check_imm(operand, -128, 256)
        self.encode_bits(8, 8, operand.value & 0xFF)

    # Encode a signed immediate operand in the 8 bit immediate field
    def encode_simm8(self, operand: Operand):
        self.check_imm(operand, -128, 128)
        self.encode_bits(8, 8, operand.value & 0xFF)

    # Error if an operand is not an immediate, or the immediate is less than
    # `lower` or greater than or equal to `upper`.
    def check_imm(self, operand: Operand, lower: int, upper: int):
        if operand.kind != OperandKind.Imm:
            self.error(f"expected immediate operand; got {operand}")
        value = operand.value
        if value < lower or value >= upper:
            self.error(
                f"immediate value {value} is out of bounds; expected {lower} <= value < {upper}"
            )


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

# Compute the addresses of each instruction.
Layouter().layout_program(parser.program)

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
