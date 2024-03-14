    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5
    nop

    # Subtraction using `add` and `not`.
    ldi r0, 24  # r0 = 00011000
    ldi r1, 19  # r1 = 00010011
    not r1, r1  # r1 = 11101100
    add r0, r1  # r0 = 00000100
    ldi r1, 1
    add r0, r1  # r0 = 00000101 (5 = 24-19)
    ldi r1, 0
    nop

    # Divide signed number by 4 using arithmetic right shift. Each shift is a
    # division by two, rounded down.
    ldi r0, 84   # r0 = 01010100 (84)
    shra r0      # r0 = 00101010 (42)
    shra r0      # r0 = 00010101 (21 = 84/4)
    ldi r1, -84  # r1 = 10101100 (-84)
    shra r1      # r1 = 11010110 (-42)
    shra r1      # r1 = 11101011 (-21 = -84/4)
    halt
