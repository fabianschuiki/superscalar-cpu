    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5
    nop
    nop

    # Add 24 bit numbers.
    # 10_000_000 + 6_000_000 = 16_000_000 ?
    #   0x989680 +  0x5B8D80 =   0xF42400 ?

    ldi r0, 0x80 # r0 = 10000000
    ldi r1, 0x96 # r1 = 10010110
    ldi r2, 0x98 # r2 = 10011000 {r2,r1,r0} = 10_000_000

    ldi r4, 0x80 # r4 = 10000000
    ldi r5, 0x8D # r5 = 10001101
    ldi r6, 0x5B # r6 = 01011011 {r6,r5,r4} = 6_000_000

    add  r0, r4  # r0 = 00000000
    addc r1, r5  # r1 = 00100100
    addc r2, r6  # r2 = 11110100 {r2,r1,r0} = 16_000_000

    # Subtract 24 bit numbers.
    # 16_000_000 -  800_000 = 15_200_000 ?
    #   0xF42400 - 0x0C3500 =   0xE7EF00 ?

    ldi r4, 0x00 # r4 = 00000000
    ldi r5, 0x35 # r5 = 00110101
    ldi r6, 0x0C # r6 = 00001100 {r6,r5,r4} = 800_000

    sub  r0, r4  # r0 = 00000000
    subc r1, r5  # r1 = 11101111
    subc r2, r6  # r2 = 11100111 {r2,r1,r0} = 15_200_000

    nop
    nop

    mv r0, r3
    mv r1, r3
    mv r2, r3
    mv r4, r3
    mv r5, r3
    mv r6, r3

    # 16 bit Fibonacci sequence forward.
    ldi r0, 233
    ldi r2, 144

    add  r2, r0 # r2 = 01111001
    addc r3, r1 # r3 = 00000001 {r3,r2} = 377
    add  r0, r2 # r0 = 01100010
    addc r1, r3 # r1 = 00000010 {r1,r0} = 610
    add  r2, r0 # r2 = 11011011
    addc r3, r1 # r3 = 00000011 {r3,r2} = 987
    add  r0, r2 # r0 = 00111101
    addc r1, r3 # r1 = 00000110 {r1,r0} = 1597
    add  r2, r0 # r2 = 00011000
    addc r3, r1 # r3 = 00001010 {r3,r2} = 2584
    add  r0, r2 # r0 = 01010101
    addc r1, r3 # r1 = 00010000 {r1,r0} = 4181

    # 16 bit Fibonacci sequence backward.
    ldi r0, 0b00100000
    ldi r1, 0b10110101 # {r1,r0} = 46368
    ldi r2, 0b11110001
    ldi r3, 0b01101111 # {r3,r2} = 28657

    sub  r0, r2 # r0 = 00101111
    subc r1, r3 # r1 = 01000101 {r1,r0} = 17711
    sub  r2, r0 # r2 = 11000010
    subc r3, r1 # r3 = 00101010 {r3,r2} = 10946
    sub  r0, r2 # r0 = 01101101
    subc r1, r3 # r1 = 00011010 {r1,r0} = 6765
    sub  r2, r0 # r2 = 01010101
    subc r3, r1 # r3 = 00010000 {r3,r2} = 4181
    sub  r0, r2 # r0 = 00011000
    subc r1, r3 # r1 = 00001010 {r1,r0} = 2584
    sub  r2, r0 # r2 = 00111101
    subc r3, r1 # r3 = 00000110 {r3,r2} = 1597

    halt
