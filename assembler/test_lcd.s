# Print a message to the LCD.

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
    nop                 # write takes 5 cycles
    nop
    nop

    # Clear the display.
    ldi r0, 0b00000001  # Clear Display (0 0 0 0 0 0 0 1)
    lcdcw r0
    nop
    nop
    nop

    # Turn the display on.
    ldi r0, 0b00001111  # Display on/off (0 0 0 0 1 D C B)
    lcdcw r0            # D=1: display on, C=1: cursor on, B=1: cursor blink
    nop
    nop
    nop

hello:
    # Write "Hello".
    ldi r0, 72   # "H"
    lcddw r0
    nop
    nop
    nop
    ldi r0, 101  # "e"
    lcddw r0
    nop
    nop
    nop
    ldi r0, 108  # "l"
    lcddw r0
    nop
    nop
    nop
    ldi r0, 108  # "l"
    lcddw r0
    nop
    nop
    nop
    ldi r0, 111  # "o"
    lcddw r0
    nop
    nop
    nop

digits:
    # Go to the second line.
    ldi r0, 0b11000000  # Set DDRAM Address (1 A6 A5 A4 A3 A2 A1 A0)
    lcdcw r0            # 0x00: line 1, 0x40: line 2
    nop
    nop

    # Write "0123456789" using a loop.
    ldi r0, 48   # "0"
    ldi r1, 10   # counter
1:
    lcddw r0     # write character
    nop          # padding for 5 write cycles
    addi r0, 1   # increment character
    addi r1, -1  # decrement counter
    b.nz 1b      # loop until counter is zero

end:
    # Clear registers and halt.
    mv r0, r6
    mv r1, r6
    halt
