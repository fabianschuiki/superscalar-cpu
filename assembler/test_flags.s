    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5

    # Zero Flag
    add r0, r1  # Flags = 0010  r0 = 00000000
    ldi r0, 1
    add r0, r1  # Flags = 0000  r0 = 00000001

    # Flag Swapping
    ldi r0, 0b1101
    fswap r0  # Flags = 1101  r0 = 00000000
    fswap r1  # Flags = 0000  r1 = 00001101

    # Sign Flag
    ldi r0, 0b10000000
    ldi r1, 0
    add r0, r1  # Flags = 0100  r0 = 10000000

    # Overflow Flag
    ldi r0, 20    # r0 = 00010100
    ldi r1, 22    # r1 = 00010110
    add r0, r1    # r0 = 00101010 (42)  Flags = 0000

    ldi r0, -20   # r0 = 11101100
    ldi r1, -22   # r1 = 11101010
    add r0, r1    # r0 = 11010110 (-42)  Flags = 0101

    ldi r0, 100   # r0 = 01100100
    ldi r1, 101   # r1 = 01100101
    add r0, r1    # r0 = 11001001 (-55 / 201)  Flags = 1100

    ldi r0, -100  # r0 = 10011100
    ldi r1, -101  # r1 = 10011011
    add r0, r1    # r0 = 00110111 (55 / -201)  Flags = 1001

    ldi r0, -28   # r0 = 11100100
    ldi r1, -100  # r1 = 10011100
    add r0, r1    # r0 = 10000000 (-128)  Flags = 0101

    ldi r0, 27    # r0 = 00011011
    ldi r1, 100   # r1 = 01100100
    add r0, r1    # r0 = 01111111 (127)  Flags = 0000

    # Comparisons without changing registers
    ldi r0, 20
    ldi r1, 22
    cmp r0, r0  # Flags = 0011  ZF=1 => equal      CF=1 => greater-equal
    cmp r1, r0  # Flags = 0001  ZF=0 => not equal  CF=1 => greater-equal
    cmp r0, r1  # Flags = 0100  ZF=0 => not equal  CF=0 => less

    # Testing for zero or individual bits without changing registers
    ldi r0, 0b00001100
    ldi r1, 0b00000100
    ldi r2, 0b00000010
    test r3, r3  # Flags = 0010  ZF=1 => r3 is zero
    test r2, r2  # Flags = 0000  ZF=0 => r2 is non-zero
    test r0, r1  # Flags = 0000  ZF=0 => bit 2 in r0 set
    test r0, r2  # Flags = 0010  ZF=1 => bit 1 in r0 not set

    # Multiplication by repeated addition.
    ldi r0, 5
    ldi r1, 29
    ldi r2, 1

# loop:
    add r3, r1
    sub r0, r2  # ZF indicates whether r0 reached 0
    fswap r4    # r4 = {OF,SF,ZF,CF}
    shrl r4     # r4 = {OF,SF,ZF}
    and r4, r2  # r4 = ZF
    add r4, r2  # r4 = 2 if ZF else 1
    shll r4     # r4 = 4 if ZF else 2
    jrelr r4    # skip next if ZF
    jreli -16   # loop
    # r3 = 10010001 (5*29 = 145)
    ldi r1, 0
    ldi r2, 0
    ldi r3, 0
    ldi r4, 0
    halt
