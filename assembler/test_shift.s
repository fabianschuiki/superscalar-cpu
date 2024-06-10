    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5
    nop

    # 1) Negate numbers
    ldi r0, 1
    ldi r1, 10
    ldi r2, 100
    neg r0 # r0 = 11111111 (-1)
    neg r1 # r1 = 11110110 (-10)
    neg r2 # r2 = 10011100 (-100)
    nop

    # 2) 16 bit left shift (through carry flag)
    mv r2, r6
    mv r1, r6
    ldi r0, 0b10111101
    shll r0 # r0 = 01111010 CF=1
    shlc r1 # r1 = 00000001 CF=0
    shll r0 # r0 = 11110100 CF=0
    shlc r1 # r1 = 00000010 CF=0
    shll r0 # r0 = 11101000 CF=1
    shlc r1 # r1 = 00000101 CF=0
    shll r0 # r0 = 11010000 CF=1
    shlc r1 # r1 = 00001011 CF=0
    nop

    # 3) 16 bit right shift (through carry flag)
    shrl r1 # r1 = 00000101 CF=1
    shrc r0 # r0 = 11101000 CF=0
    shrl r1 # r1 = 00000010 CF=1
    shrc r0 # r0 = 11110100 CF=0
    shrl r1 # r1 = 00000001 CF=0
    shrc r0 # r0 = 01111010 CF=0
    shrl r1 # r1 = 00000000 CF=1
    shrc r0 # r0 = 10111101 CF=0
    nop

    # 4) Bit-reverse a number
    ldi r0, 0b01010111
    mv r2, r0
    shrl r2 # r2 = 00101011 CF=1
    shlc r1 # r1 = 00000001 CF=0
    shrl r2 # r2 = 00010101 CF=1
    shlc r1 # r1 = 00000011 CF=0
    shrl r2 # r2 = 00001010 CF=1
    shlc r1 # r1 = 00000111 CF=0
    shrl r2 # r2 = 00000101 CF=0
    shlc r1 # r1 = 00001110 CF=0
    shrl r2 # r2 = 00000010 CF=1
    shlc r1 # r1 = 00011101 CF=0
    shrl r2 # r2 = 00000001 CF=0
    shlc r1 # r1 = 00111010 CF=0
    shrl r2 # r2 = 00000000 CF=1
    shlc r1 # r1 = 01110101 CF=0
    shrl r2 # r2 = 00000000 CF=0
    shlc r1 # r1 = 11101010 CF=0  r1 = rev(r0)
    nop

    # 5) Popcount
    mv r1, r6
    mv r0, r6

    ldi r0, 0b10010110 # 4 ones
    mv r2, r0
    shll r2     # r2 = 00101100 CF=1
    addc r1, r6 # r1 = 00000001 (1)
    shll r2     # r2 = 01011000 CF=0
    addc r1, r6 # r1 = 00000001 (1)
    shll r2     # r2 = 10110000 CF=0
    addc r1, r6 # r1 = 00000001 (1)
    shll r2     # r2 = 01100000 CF=1
    addc r1, r6 # r1 = 00000010 (2)
    shll r2     # r2 = 11000000 CF=0
    addc r1, r6 # r1 = 00000010 (2)
    shll r2     # r2 = 10000000 CF=1
    addc r1, r6 # r1 = 00000011 (3)
    shll r2     # r2 = 00000000 CF=1
    addc r1, r6 # r1 = 00000100 (4)
    shll r2     # r2 = 00000000 CF=0
    addc r1, r6 # r1 = 00000100 (4)  r1 = popcount(r0)

    ldi r2, 0b11110111 # 7 ones
    mv r4, r2
    shrl r4     # r4 = 01111011 CF=1
    addc r3, r6 # r3 = 00000001 (1)
    shrl r4     # r4 = 00111101 CF=1
    addc r3, r6 # r3 = 00000010 (2)
    shrl r4     # r4 = 00011110 CF=1
    addc r3, r6 # r3 = 00000011 (3)
    shrl r4     # r4 = 00001111 CF=0
    addc r3, r6 # r3 = 00000011 (3)
    shrl r4     # r4 = 00000111 CF=1
    addc r3, r6 # r3 = 00000100 (4)
    shrl r4     # r4 = 00000011 CF=1
    addc r3, r6 # r3 = 00000101 (5)
    shrl r4     # r4 = 00000001 CF=1
    addc r3, r6 # r3 = 00000110 (6)
    shrl r4     # r4 = 00000000 CF=1
    addc r3, r6 # r3 = 00000111 (7)  r3 = popcount(r2)

    nop

    # 6) Ping-pong bit pattern loop
    mv r3, r6
    mv r2, r6
    mv r1, r6
    ldi r0, 1
loop:
    shll r0 # r0 = 00000010
    shll r0 # r0 = 00000100
    shll r0 # r0 = 00001000
    shll r0 # r0 = 00010000
    shll r0 # r0 = 00100000
    shll r0 # r0 = 01000000
    shll r0 # r0 = 10000000
    nop
    shrl r0 # r0 = 01000000
    shrl r0 # r0 = 00100000
    shrl r0 # r0 = 00010000
    shrl r0 # r0 = 00001000
    shrl r0 # r0 = 00000100
    shrl r0 # r0 = 00000010
    shrl r0 # r0 = 00000001
    jreli loop
