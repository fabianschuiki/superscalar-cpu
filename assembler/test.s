    # Hello!
    /* Here's some comment
       across multiple lines */
1:
    jreli +32  # 0x0020
    jreli add  # 0x0020
    jreli 1f   # 0x0020
    jreli 1b   # 0x0000

.org 0x20
add:
1:
_start:

    # Basics
    nop
    mv  r0, r1
    ldi r0, 42

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

    cldi.c   r0, 4
    cldi.nc  r0, 4
    cldi.z   r0, 4
    cldi.nz  r0, 4
    cldi.s   r0, 4
    cldi.ns  r0, 4
    cldi.o   r0, 4
    cldi.no  r0, 4
    cldi.eq  r0, 4
    cldi.ne  r0, -4
    cldi.uge r0, -4
    cldi.ult r0, -4
    cldi.ule r0, -4
    cldi.ugt r0, -4
    cldi.slt r0, -4
    cldi.sge r0, -4
    cldi.sle r0, -4
    cldi.sgt r0, -4

    # Branches
    jreli -6
    jreli +6
    jrelr r0
    jabsr r1r0

    # Unary Arithmetic
    not   r0
    neg   r0
    shll  r0
    shlc  r0
    shrl  r0
    shrc  r0
    shra  r0
    fswap r0

    # Binary Arithmetic
    add   r0, r1
    addi  r0, 42
    addi  r0, -42
    addc  r0, r1
    addci r0, 5
    addci r0, -5
    sub   r0, r1
    subc  r0, r1
    and   r0, r1
    andi  r0, 42
    andi  r0, -42
    or    r0, r1
    ori   r0, 42
    ori   r0, -42
    xor   r0, r1
    xori  r0, 3
    xori  r0, -3
    cmp   r0, r1
    cmpi  r0, 4
    cmpi  r0, -4
    test  r0, r1
    testi r0, 42
    testi r0, -42

    halt
