# Test out-of-order result bus.

start:
    # Initialize registers, flags, and display.
    ldi r0, 0b00111000  # Function Set
    lcdcw r0
    ldi r1, 0
    ldi r2, 0
    ldi r3, 0
    ldi r0, 0b10001010  # Move cursor to address 10
    lcdcw r0
    ldi r4, 0
    ldi r5, 0
    ldi r6, 0
    ldi r0, 0
    fw r0

no_hazard:
    # Read cursor position without any hazard.
    lcdcr r0    # <-- r0 pending
    addi r1, 3  # ignores r0; no hazard
    shll r1     # ignores r0; no hazard
    xori r1, 1  # ignores r0; no hazard
    ori r1, 8   # ignores r0; no hazard
                # <-- r0=10
    mv r1, r0   # reads r0
    # Result: r0=10 and r1=10

raw_hazard:
    # Read cursor position with read-after-write (RAW) hazard.
    lcdcr r2    # <-- r2 pending
                # <-- r2=10 (if hazard handled)
    mv r3, r2   # reads r2; RAW hazard
    nop         # wait for LCD
    nop         # wait for LCD
    nop         # wait for LCD
                # <-- r2=10 (if hazard not handled)
    # Result: r2=10, and r3=10 if hazard handled correctly, r3=0 otherwise

waw_hazard:
    # Read cursor position with write-after-write (WAW) hazard.
    lcdcr r4    # <-- r4 pending
                # <-- r4=10 (if hazard handled)
    ldi r4, 16  # writes r4; WAW hazard
    nop         # wait for LCD
    nop         # wait for LCD
    nop         # wait for LCD
                # <-- r4=10 (if hazard not handled)
    mv r5, r4   # reads r4
    # Result: r4/r5=16 if hazard handled correctly, r4/r5=10 otherwise

    halt
