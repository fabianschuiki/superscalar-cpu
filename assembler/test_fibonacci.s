# Compute the largest 16 bit Fibonacci number in r1r0.

start:
    # Clear registers to zero.
    ldi r0, 0
    mv r1, r0
    mv r2, r1
    mv r3, r2
    mv r4, r3
    mv r5, r4
    mv r6, r5

    # Clear the flags.
    fswap r0
    mv r0, r1

    # Initialize variables a and b with the first two Fibonacci numbers 0 and 1.
    # a = {r1,r0}
    # b = {r3,r2}
    # c = {r5,r4}
    ldi r2, 1     # b = 1

    # Loop until addition overflows. Variable a then contains the largest number
    # that hasn't overflowed yet.
    ldi r6, -14   # relative offset to "loop"
loop:
    mv r4, r0     # c = a
    mv r5, r1
    mv r0, r2     # a = b
    mv r1, r3
    add  r2, r4   # b += c
    addc r3, r5   # CF set on overflow
    cldi.c r6, 2  # r6 = 2 if CF else -14
    jrelr r6      # goto "exit" if CF else "loop"

exit:
    # Clear all registers except for the result.
    ldi r6, 0
    mv r5, r6
    mv r4, r6
    mv r3, r6
    mv r2, r6

    # A = {r1,r0} now contains the result 46368 (10110101_00100000).
    halt
