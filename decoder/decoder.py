#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
import os


def unpack(value: int, offset: int, length: int) -> int:
    assert (offset >= 0)
    assert (length >= 0)
    assert (offset + length <= 16)
    return (value >> offset) & ((1 << length) - 1)


def pack(value: int, offset: int, length: int) -> int:
    assert (offset >= 0)
    assert (length >= 0)
    assert (offset + length <= 16)
    assert (value >= 0)
    assert (value < 2**length)
    return (value & ((1 << length) - 1)) << offset


class RdMode(IntEnum):
    Unused = 0b11
    R = 0b10
    W = 0b01
    RW = 0b00


class RsMode(IntEnum):
    R8 = 0b00
    R16 = 0b01
    Imm8 = 0b10
    Imm4 = 0b11


class FlagsMode(IntEnum):
    Unused = 0b11
    R = 0b10
    W = 0b01
    RW = 0b00


class PcMode(IntEnum):
    Step = 0b00
    RelJump = 0b01
    AbsJump = 0b10
    Reserved = 0b11


class FU(IntEnum):
    Move = 0b00
    ALU = 0b01


class ALUOp(IntEnum):
    ADD = 0b00000
    ADDC = 0b00001
    SUB = 0b00010
    SUBC = 0b00011
    NOT = 0b00100
    NEG = 0b00101
    SHLL = 0b00110
    SHLC = 0b00111
    SHRL = 0b01000
    SHRC = 0b01001
    SHRA = 0b01010
    FSWAP = 0b01100
    AND = 0b01101
    OR = 0b01110
    XOR = 0b01111
    CMV = 0b10000


@dataclass
class Decoded:
    rd: RdMode = RdMode.Unused
    rs: RsMode = RsMode.Imm4
    flags: FlagsMode = FlagsMode.Unused
    pc: PcMode = PcMode.Step
    fuid: FU = FU.Move
    fuop: int = 0


def alu_unary(op: ALUOp | int,
              flags: FlagsMode = FlagsMode.W,
              rd: RdMode = RdMode.RW) -> Decoded:
    return Decoded(rd=rd, flags=flags, fuid=FU.ALU, fuop=op)


def alu_binary(op: ALUOp | int,
               flags: FlagsMode = FlagsMode.W,
               rd: RdMode = RdMode.RW,
               rs: RsMode = RsMode.R8) -> Decoded:
    return Decoded(rd=rd, rs=rs, flags=flags, fuid=FU.ALU, fuop=op)


def decode(inst: int) -> Decoded:
    func0 = unpack(inst, 0, 4)
    func1 = unpack(inst, 12, 4)
    func2 = unpack(inst, 4, 4)
    func3 = unpack(inst, 8, 4)

    # Handle basic instructions (0..3=0)
    if func0 == 0:
        if inst == 0:  # nop
            return Decoded()
        if func1 == 1:  # mv
            return Decoded(rd=RdMode.W, rs=RsMode.R8, fuid=FU.Move)
        if func1 == 2 and func2 == 0:  # jro / jrelr
            return Decoded(rs=RsMode.R8, pc=PcMode.RelJump)
        if func1 == 3 and func2 == 0:  # jr / jabsr
            return Decoded(rs=RsMode.R16, pc=PcMode.AbsJump)

    # Handle ALU instructions (0..3=1)
    if func0 == 1:
        # Handle unary ops
        if func1 == 0:
            if func3 == 0: return alu_unary(ALUOp.NOT)
            if func3 == 1: return alu_unary(ALUOp.NEG)
            if func3 == 2: return alu_unary(ALUOp.SHLL)
            if func3 == 3: return alu_unary(ALUOp.SHLC, FlagsMode.RW)
            if func3 == 4: return alu_unary(ALUOp.SHRL)
            if func3 == 5: return alu_unary(ALUOp.SHRC, FlagsMode.RW)
            if func3 == 6: return alu_unary(ALUOp.SHRA)
            if func3 == 7: return alu_unary(ALUOp.FSWAP, FlagsMode.RW)
            if func3 == 8: return alu_unary(ALUOp.FSWAP, FlagsMode.R, RdMode.W)
            if func3 == 9: return alu_unary(ALUOp.FSWAP, FlagsMode.W, RdMode.R)

        # Handle binary ops
        if func1 == 1: return alu_binary(ALUOp.ADD)
        if func1 == 2: return alu_binary(ALUOp.ADDC, FlagsMode.RW)
        if func1 == 3: return alu_binary(ALUOp.SUB)
        if func1 == 4: return alu_binary(ALUOp.SUBC, FlagsMode.RW)
        if func1 == 5: return alu_binary(ALUOp.AND)
        if func1 == 6: return alu_binary(ALUOp.OR)
        if func1 == 7: return alu_binary(ALUOp.XOR)
        if func1 == 8: return alu_binary(ALUOp.SUB, rd=RdMode.R)  # cmp
        if func1 == 9: return alu_binary(ALUOp.AND, rd=RdMode.R)  # test
        if func1 == 10:  # addci
            return alu_binary(ALUOp.ADDC, FlagsMode.RW, rs=RsMode.Imm4)
        if func1 == 11:  # xori
            return alu_binary(ALUOp.XOR, rs=RsMode.Imm4)
        if func1 == 12:  # cmpi
            return alu_binary(ALUOp.SUB, rd=RdMode.R, rs=RsMode.Imm4)

    # Handle cmv (0..3=2)
    if func0 == 2:
        cond = func1  # condition is in 12..15
        return alu_binary(ALUOp.CMV | cond, FlagsMode.R)

    # Handle cldi (0..3=3)
    if func0 == 3:
        cond = func1  # condition is in 12..15
        return alu_binary(ALUOp.CMV | cond, FlagsMode.R, rs=RsMode.Imm4)

    # Handle instructions with 8 bit immediates (0..3=8..15)
    if func0 == 8:  # ldi
        return Decoded(rd=RdMode.W, rs=RsMode.Imm8, fuid=FU.Move)
    if func0 == 9 and func2 == 0:  # j / jreli
        return Decoded(rs=RsMode.Imm8, pc=PcMode.RelJump)
    if func0 == 12:  # addi
        return alu_binary(ALUOp.ADD, rs=RsMode.Imm8)
    if func0 == 13:  # andi
        return alu_binary(ALUOp.AND, rs=RsMode.Imm8)
    if func0 == 14:  # ori
        return alu_binary(ALUOp.OR, rs=RsMode.Imm8)
    if func0 == 15:  # testi
        return alu_binary(ALUOp.AND, rd=RdMode.R, rs=RsMode.Imm8)

    # If we get here the instruction is unknown. Ideally we should cause an
    # illegal instruction exception here. For the time being, simply set the PC
    # mode to the reserved value 3.
    return Decoded(pc=PcMode.Reserved)


rom0_bytes = bytearray(2**16)
rom1_bytes = bytearray(2**16)

for inst in range(2**16):
    decoded = decode(inst)

    rom0_bytes[inst] |= pack(decoded.rd, 0, 2)
    rom0_bytes[inst] |= pack(decoded.rs, 2, 2)
    rom0_bytes[inst] |= pack(decoded.flags, 4, 2)
    rom0_bytes[inst] |= pack(decoded.pc, 6, 2)

    rom1_bytes[inst] |= pack(decoded.fuop, 0, 6)
    rom1_bytes[inst] |= pack(decoded.fuid, 6, 2)


def write_rom(data: bytes, name: str):
    path = os.path.relpath(os.path.dirname(__file__))
    path = os.path.join(path, name)

    # If the file exists and is identical, no need to update it.
    if os.path.exists(path):
        with open(path, "rb") as f:
            if f.read() == data:
                print(f"Skipping unchanged {name}")
                return

    # Otherwise write the ROM data to disk.
    with open(path, "wb") as f:
        print(f"Writing {name}")
        f.write(data)


write_rom(rom0_bytes, "rom0.bin")
write_rom(rom1_bytes, "rom1.bin")
