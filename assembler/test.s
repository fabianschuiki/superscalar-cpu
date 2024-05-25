    # Hello!
    /* Here's some comment
       across multiple lines */

    # Clear registers to zero.
    ldi r0, 0x00  # load initial zero
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5
    jreli +18  # 0x0020

.org 0x20
    # ALU
    ldi r0, 9
    ldi r1, 10
    add r1, r0
    sub r0, r1
    addc r2, r3
    subc r4, r5
    not r0
    neg r0
    shll r0
    shlc r1
    shrl r2
    shrc r3
    shra r4
    and r0, r1
    or r2, r3
    xor r4, r5
    cmp r0, r1
    test r2, r2
    fswap r3
    cmv.c   r0, r1
    cmv.nc  r0, r1
    cmv.z   r0, r1
    cmv.nz  r0, r1
    cmv.s   r0, r1
    cmv.ns  r0, r1
    cmv.o   r0, r1
    cmv.no  r0, r1
    cmv.eq  r0, r1
    cmv.ne  r0, r1
    cmv.uge r0, r1
    cmv.ult r0, r1
    cmv.ule r0, r1
    cmv.ugt r0, r1
    cmv.slt r0, r1
    cmv.sge r0, r1
    cmv.sle r0, r1
    cmv.sgt r0, r1

    # Load some interesting patterns.
    ldi r0, 0xF0
    ldi r1, 0x12
    ldi r2, 0xBA
    ldi r3, 0x0F
    ldi r4, 0x81
    ldi r5, 0x42
    ldi r6, 0xFF

    # Test a relative jump with register.
    ldi r0, 6
    jrelr r0  # 0x002C
    nop
    nop

    # Test 16 bit absolute jump.
    ldi r0, 0x40
    ldi r1, 0xF0
    jabsr r0r1  # 0xF040
    halt  # never reached

.org 0xF040
    # Interesting pattern loop.
    ldi r0, 0x01
    ldi r1, 0x02
    ldi r2, 0x04
    ldi r3, 0x08
    ldi r4, 0x10
    ldi r5, 0x20
    ldi r6, 0x40
    nop
    ldi r0, 0x80
    ldi r1, 0x40
    ldi r2, 0x20
    ldi r3, 0x10
    ldi r4, 0x08
    ldi r5, 0x04
    ldi r6, 0x02
    nop
    jreli -32  # 0xF040
