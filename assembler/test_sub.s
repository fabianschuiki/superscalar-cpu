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

    # Addition with negative numbers.
    ldi r0, 42
    ldi r1, -24
    ldi r2, -53
    add r1, r0  # -24+42 =  18 = 00010010
    add r2, r0  # -53+42 = -11 = 11110101

    # Subtraction with positive numbers.
    ldi r0, 19
    ldi r1, 24
    ldi r2, 13
    sub r1, r0  # 24-19 =  5 = 00000101
    sub r2, r0  # 13-19 = -6 = 11111010

    # Subtraction with negative RHS.
    ldi r0, 0
    sub r1, r2  # 5-(-6) = 11 = 00001011

    # Subtraction with negative LHS and positive RHS.
    ldi r0, -9
    ldi r1, 6
    sub r0, r1  # -9-6 = -15 = 11110001

    # Subtraction with negative LHS and RHS.
    ldi r1, -18
    ldi r2, -13
    sub r1, r0  # -18-(-15) = -3 = 11111101
    sub r2, r0  # -13-(-15) =  2 = 00000010

    nop
    nop

    # Clear r0-r2 to zero.
    mv r2, r3
    mv r1, r3
    mv r0, r3

    # Reverse Fibonacci sequence.
    ldi r0, 233
    ldi r1, 144
    sub r0, r1  # 89
    sub r1, r0  # 55
    sub r0, r1  # 34
    sub r1, r0  # 21
    sub r0, r1  # 13
    sub r1, r0  # 8
    sub r0, r1  # 5
    sub r1, r0  # 3
    sub r0, r1  # 2
    sub r1, r0  # 1
    sub r0, r1  # 1
    sub r1, r0  # 0
    halt
