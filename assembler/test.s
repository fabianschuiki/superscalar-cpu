    # Hello!
    /* Here's some comment
       across multiple lines */
1:
    j   +32  # 0x0020
    j   add  # 0x0020
    j   1f   # 0x0020
    j   1b   # 0x0000
    b.z +24  # 0x0020
    b.z add  # 0x0020
    b.z 1f   # 0x0020
    b.z 1b   # 0x0000

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
    j   -6
    j   +6
    jro r0
    jr  r1r0

    b.c   42
    b.nc  42
    b.z   42
    b.nz  42
    b.s   42
    b.ns  42
    b.o   42
    b.no  42
    b.eq  42
    b.ne  -42
    b.uge -42
    b.ult -42
    b.ule -42
    b.ugt -42
    b.slt -42
    b.sge -42
    b.sle -42
    b.sgt -42

    bro.c   r0
    bro.nc  r0
    bro.z   r0
    bro.nz  r0
    bro.s   r0
    bro.ns  r0
    bro.o   r0
    bro.no  r0
    bro.eq  r0
    bro.ne  r0
    bro.uge r0
    bro.ult r0
    bro.ule r0
    bro.ugt r0
    bro.slt r0
    bro.sge r0
    bro.sle r0
    bro.sgt r0

    br.c   r1r0
    br.nc  r1r0
    br.z   r1r0
    br.nz  r1r0
    br.s   r1r0
    br.ns  r1r0
    br.o   r1r0
    br.no  r1r0
    br.eq  r1r0
    br.ne  r1r0
    br.uge r1r0
    br.ult r1r0
    br.ule r1r0
    br.ugt r1r0
    br.slt r1r0
    br.sge r1r0
    br.sle r1r0
    br.sgt r1r0

    # Control and Status Registers
    lcdcw r0
    lcddw r0

    # Unary Arithmetic
    not   r0
    neg   r0
    shll  r0
    shlc  r0
    shrl  r0
    shrc  r0
    shra  r0
    fswap r0
    fr    r0
    fw    r0

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
