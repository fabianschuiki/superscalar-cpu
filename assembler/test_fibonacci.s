# Compute the largest 16 bit Fibonacci number in r1r0.

start:
    # Clear registers and flags to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5
    fw r0

    # Initialize variables B and A with the first two Fibonacci numbers 0 and 1.
    # Then loop until addition overflows, adding into A and B in turns.
    # A = {r1,r0}
    # B = {r3,r2}
    ldi r0, 1     # A = 1
loop:
    add  r2, r0   # B += A
    addc r3, r1   # CF set if B overflowed
    b.c  done_a   # break on overflow, result in A

    add  r0, r2   # A += B
    addc r1, r3   # CF set if A overflowed
    b.nc loop     # loop while no overflow; else result in B

done_b:
    # If we get here, the last valid result was in B. Move it to A.
    mv r0, r2     # A = B
    mv r1, r3

done_a:
    # Once we get here, the last valid result was in A. Clear all other
    # registers.
    mv r3, r6
    mv r2, r6
    # A = {r1,r0} now contains the result 46368 (10110101_00100000).

    # Count the number of bits in the result.
popcount:
    # Lower byte.
    mv r2, r0
    shll r2      # shift top bit into CF
1:
    addci r3, 0  # add CF to r3
    shll r2      # shift top bit into CF, ZF set if done
    b.nz 1b
    addci r3, 0  # add CF to r3

    # Upper byte.
    mv r2, r1
    shll r2      # shift top bit into CF
1:
    addci r3, 0  # add CF to r3
    shll r2      # shift top bit into CF, ZF set if done
    b.nz 1b
    addci r3, 0  # add CF to r3

    # Check that the result has 6 bits set. If it doesn't, halt.
    cmpi r3, 6        # check that r3 is 6
    b.eq popcount_ok  # continue if equal, otherwise halt
    ldi r6, 0x0F      # show error code in r6 and halt
    halt
popcount_ok:
    mv r3, r6

    # Check that the correct bits are 0 and 1 using only one extra register.
bitcheck:
    # Lower byte.
    mv r2, r0
    xori r2, -1    # invert using an xor op
    andi r2, 0x20  # check ones
    b.nz bitcheck_fail
    mv r2, r0
    andi r2, 0xDF  # check zeros
    b.nz bitcheck_fail

    # Upper byte.
    mv r2, r1
    xori r2, -1    # invert using an xor op
    andi r2, 0xB5  # check ones
    b.nz bitcheck_fail
    mv r2, r1
    andi r2, 0x4A  # check zeros
    b.nz bitcheck_fail

    # At this point all is well. Use a jump, just because we can.
    j bitcheck_ok

bitcheck_fail:
    ldi r6, 0xF0  # show error code in r6 and halt
    halt

bitcheck_ok:
    ldi r6, 1  # show success as 1 in r6
    halt
