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

    # Fibonacci sequence.
    ldi r1, 1   # 1
    mv r2, r1
    add r2, r0  # 1
    mv r3, r2
    add r3, r1  # 2
    mv r4, r3
    add r4, r2  # 3
    mv r5, r4
    add r5, r3  # 5
    mv r6, r5
    add r6, r4  # 8

    mv r0, r6
    add r0, r5  # 13
    mv r1, r0
    add r1, r6  # 21
    mv r2, r1
    add r2, r0  # 34
    mv r3, r2
    add r3, r1  # 55
    mv r4, r3
    add r4, r2  # 89
    mv r5, r4
    add r5, r3  # 144
    mv r6, r5
    add r6, r4  # 233

    nop
    nop

    # Infinite loop counting up.
    addi r0, 1
    addi r1, 2
    addi r2, 3
    addi r3, 4
    addi r4, 5
    addi r5, 6
    addi r6, 7
    jreli -14
