    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5

    # Test individual flag condition codes.
    ldi r0, 0b1001
    fswap r0  # CF=1 ZF=0 SF=0 OF=1
    ldi r0, 1
    cmv.c  r1, r0  # r1 = 1
    cmv.nc r2, r0  # r2 = 0
    cmv.z  r3, r0  # r3 = 0
    cmv.nz r4, r0  # r4 = 1
    ldi r1, 0
    ldi r4, 0
    cmv.s  r1, r0  # r1 = 0
    cmv.ns r2, r0  # r2 = 1
    cmv.o  r3, r0  # r3 = 1
    cmv.no r4, r0  # r4 = 0
    ldi r2, 0
    ldi r3, 0
    ldi r0, 0
    nop

    # Test unsigned comparisons.
    ldi r0, 1
    ldi r1, 200
    ldi r2, 201
    cmp r1, r2      # Flags = 0100
    cmv.ult r3, r0  # r3 = 1  (!CF)
    cmv.ule r4, r0  # r4 = 1  (!CF | ZF)
    cmv.uge r5, r0  # r5 = 0  (CF)
    cmv.ugt r6, r0  # r6 = 0  (CF & !ZF)
    ldi r3, 0
    ldi r4, 0
    ldi r1, 201
    cmp r1, r2      # Flags = 0011
    cmv.ult r3, r0  # r3 = 0  (!CF)
    cmv.ule r4, r0  # r4 = 1  (!CF | ZF)
    cmv.uge r5, r0  # r5 = 1  (CF)
    cmv.ugt r6, r0  # r6 = 0  (CF & !ZF)
    ldi r4, 0
    ldi r5, 0
    ldi r2, 200
    cmp r1, r2      # Flags = 0001
    cmv.ult r3, r0  # r3 = 0  (!CF)
    cmv.ule r4, r0  # r4 = 0  (!CF | ZF)
    cmv.uge r5, r0  # r5 = 1  (CF)
    cmv.ugt r6, r0  # r6 = 1  (CF & !ZF)
    ldi r5, 0
    ldi r6, 0
    ldi r0, 0
    ldi r1, 0
    ldi r2, 0
    nop

    # Test signed comparisons.
    ldi r0, 1
    ldi r1, -127
    ldi r2, 127
    cmp r1, r2      # Flags = 1001
    cmv.slt r3, r0  # r3 = 1  (SF != OF)
    cmv.sle r4, r0  # r4 = 1  (ZF | (SF != OF))
    cmv.sge r5, r0  # r5 = 0  (SF == OF)
    cmv.sgt r6, r0  # r6 = 0  (!ZF & (SF == OF))
    ldi r3, 0
    ldi r4, 0
    ldi r2, -127
    cmp r1, r2      # Flags = 0011
    cmv.slt r3, r0  # r3 = 0  (SF != OF)
    cmv.sle r4, r0  # r4 = 1  (ZF | (SF != OF))
    cmv.sge r5, r0  # r5 = 1  (SF == OF)
    cmv.sgt r6, r0  # r6 = 0  (!ZF & (SF == OF))
    ldi r4, 0
    ldi r5, 0
    ldi r1, 127
    cmp r1, r2      # Flags = 1100
    cmv.slt r3, r0  # r3 = 0  (SF != OF)
    cmv.sle r4, r0  # r4 = 0  (ZF | (SF != OF))
    cmv.sge r5, r0  # r5 = 1  (SF == OF)
    cmv.sgt r6, r0  # r6 = 1  (!ZF & (SF == OF))
    ldi r5, 0
    ldi r6, 0
    ldi r0, 0
    ldi r1, 0
    ldi r2, 0
    nop

    # Multiplication by repeated addition.
    ldi r0, 3
    ldi r1, 42
    ldi r3, 1
    ldi r4, -6
    ldi r5, 2
# loop:
    add r2, r1
    sub r0, r3    # ZF indicates whether r0 reached 0
    cmv.z r4, r5  # r4 = 2 if ZF else -6
    jrelr r4      # "exit" if ZF else "loop"
# exit:
    ldi r1, 0
    ldi r3, 0
    ldi r4, 0
    ldi r5, 0
    # r2 = 01111110 (3*42 = 126)
    ldi r2, 0
    nop

    # Compute the maximum value across registers.
    ldi r0, 1
    ldi r1, 13
    ldi r2, 9
    ldi r3, 76
    ldi r4, 42
    ldi r5, 143
    ldi r6, 128
    cmp r0, r1      # 1 < 13
    cmv.ult r0, r1  # r0 = 13
    cmp r0, r2      # 13 < 9
    cmv.ult r0, r2  # r0 = 13
    cmp r0, r3      # 13 < 76
    cmv.ult r0, r3  # r0 = 76
    cmp r0, r4      # 76 < 42
    cmv.ult r0, r4  # r0 = 76
    cmp r0, r5      # 76 < 143
    cmv.ult r0, r5  # r0 = 143
    cmp r0, r6      # 143 < 128
    cmv.ult r0, r6  # r0 = 143
    ldi r6, 0
    mv r5, r6
    mv r4, r6
    mv r3, r6
    mv r2, r6
    mv r1, r6
    mv r0, r6
    nop

    # Compute the largest 16 bit number in the Fibonacci sequence.
    # a = {r1,r0}
    # b = {r3,r2}
    # c = {r5,r4}
    ldi r2, 1  # b = 1
    ldi r6, -16
# loop2:
    mv r4, r0     # c = a
    mv r5, r1
    mv r0, r2     # a = b
    mv r1, r3
    add  r2, r4   # b += c
    addc r3, r5   # CF set on overflow
    ldi r5, 2
    cmv.c r6, r5  # r6 = 2 if CF else -16
    jrelr r6      # "exit2" if CF else "loop2"
# exit2:
    # a = {r1,r0} = 10110101_00100000 (46368)
    ldi r6, 0
    mv r5, r6
    mv r4, r6
    mv r3, r6
    mv r2, r6
    halt
