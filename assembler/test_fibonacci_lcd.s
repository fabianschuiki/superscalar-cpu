# Print the 16 bit Fibonacci Sequence to the LCD.

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

init:
    # Configure the display.
    ldi r0, 0b00111000  # Function Set (0 0 1 DL N F - -)
    lcdcw r0            # DL=1: 8 bit, N=1: 2 lines, F=0: 5x8 font

    # Clear the display.
    ldi r0, 0b00000001  # Clear Display (0 0 0 0 0 0 0 1)
    lcdcw r0

    # Turn the display on.
    ldi r0, 0b00001111  # Display on/off (0 0 0 0 1 D C B)
    lcdcw r0            # D=1: display on, C=1: cursor on, B=1: cursor blink

hello:
    # Write "Fibonacci Sequence".
    ldi r0, 0x46  # "F"
    lcddw r0
    ldi r0, 0x69  # "i"
    lcddw r0
    ldi r0, 0x62  # "b"
    lcddw r0
    ldi r0, 0x6F  # "o"
    lcddw r0
    ldi r0, 0x6E  # "n"
    lcddw r0
    ldi r0, 0x61  # "a"
    lcddw r0
    ldi r0, 0x63  # "cc"
    lcddw r0
    lcddw r0
    ldi r0, 0x69  # "i"
    lcddw r0

    ldi r0, 0x20  # " "
    lcddw r0

    ldi r0, 0x53  # "S"
    lcddw r0
    ldi r0, 0x65  # "e"
    lcddw r0
    ldi r0, 0x71  # "q"
    lcddw r0
    ldi r0, 0x75  # "u"
    lcddw r0
    ldi r0, 0x65  # "e"
    lcddw r0
    ldi r0, 0x6E  # "n"
    lcddw r0
    ldi r0, 0x63  # "c"
    lcddw r0
    ldi r0, 0x65  # "e"
    lcddw r0

fibonacci:
    ldi r0, 1  # A = {r1,r0} = 1
    ldi r2, 1  # B = {r3,r2} = 1
    ldi r4, 2  # index = r4 = 2

    # Jump to the next line on the display. Line addresses:
    # - line 0: 0x00  (0x00 +  0)
    # - line 1: 0x40  (0x40 +  0)
    # - line 2: 0x14  (0x00 + 20)
    # - line 3: 0x54  (0x40 + 20)
newline:
    lcdcr r5        # read current display address
    andi r5, 0x7F   # ignore busy flag

    # Load r6 with the appropriate command for the LCD.
    testi r5, 0x40  # check if bit 6 set (0: on lines 0/2, 1: on lines 1/3)
    b.nz if_odd_line
if_even_line:
    ldi r6, 0b11000000  # goto line 1 (address 0x40) by default
    addi r5, -0x14      # are we on line 0 (<0x14) or 2 (>=0x14)?
    b.ult endif         # skip next if we are on line 0
    ldi r6, 0b11010100  # goto line 3 (address 0x54)
    j endif
if_odd_line:
    ldi r6, 0b10010100  # goto line 2 (address 0x14) by default
    addi r5, -0x54      # are we on line 1 (<0x54) or 3 (>=0x54)?
    b.ult endif         # skip next if we are on line 1
    ldi r6, 0b00000001  # goto line 0 with a clear display command
endif:
    # Execute the command prepared in r6.
    lcdcw r6

    # Print the current index and Fibonacci number.
    # Map values 0..9 to ASCII 0x30..0x39, values 10..15 to ASCII 0x41..0x46
print_index:
    mv r5, r4      # extract upper 4 bits of index
    shrl r5
    shrl r5
    shrl r5
    shrl r5
    addi r5, -10   # subtract 10; if r5 negative use 0..9, otherwise A..F
    b.ult 1f       # skip next if digit <10
    addi r5, 7     # add offset to go from 0x3A to 0x41
1:  addi r5, 0x3A  # add 10 plus 0x30 (ASCII code of "0")
    lcddw r5

    mv r5, r4      # extract lower 4 bits of index
    andi r5, 0xF
    addi r5, -10   # subtract 10; if r5 negative use 0..9, otherwise A..F
    b.ult 1f       # skip next if digit <10
    addi r5, 7     # add offset to go from 0x3A to 0x41
1:  addi r5, 0x3A  # add 10 plus 0x30 (ASCII code of "0")
    lcddw r5

    ldi r5, 0x3A   # print ": "
    lcddw r5
    ldi r5, 0x20
    lcddw r5

    # Small trampoline to get back to `newline`.
    j 1f
newline_hop:
    j newline
1:

    # Repeat of the above for the upper 8 bits of the Fibonacci number B (r3).
print_fib_hi:
    mv r5, r3
    shrl r5
    shrl r5
    shrl r5
    shrl r5
    addi r5, -10
    b.ult 1f
    addi r5, 7
1:  addi r5, 0x3A
    lcddw r5
    mv r5, r3
    andi r5, 0xF
    addi r5, -10
    b.ult 1f
    addi r5, 7
1:  addi r5, 0x3A
    lcddw r5

    # Repeat of the above for the lower 8 bits of the Fibonacci number B (r2).
print_fib_lo:
    mv r5, r2
    shrl r5
    shrl r5
    shrl r5
    shrl r5
    addi r5, -10
    b.ult 1f
    addi r5, 7
1:  addi r5, 0x3A
    lcddw r5
    mv r5, r2
    andi r5, 0xF
    addi r5, -10
    b.ult 1f
    addi r5, 7
1:  addi r5, 0x3A
    lcddw r5

    # Compute the next Fibonacci number in the sequence.
    mv   r5, r0
    mv   r0, r2
    add  r2, r5
    mv   r5, r1
    mv   r1, r3
    addc r3, r5

    b.c exit       # if the number overflowed 16 bits, exit
    addi r4, 1     # otherwise increment the index
    j newline_hop  # and repeat

exit:
    ldi r0, 0x20   # print " (max)"
    lcddw r0
    ldi r0, 0x28
    lcddw r0
    ldi r0, 0x6D
    lcddw r0
    ldi r0, 0x61
    lcddw r0
    ldi r0, 0x78
    lcddw r0
    ldi r0, 0x29
    lcddw r0

    # Last line should read: "18: B520 (max)"
    # 24th (0x18) Fibonacci number: 46368 (0xB520)
    halt
