#!/usr/bin/env python3
import pyftdi
import pyftdi.spi
from time import sleep
from dataclasses import dataclass
from termcolor import colored
import random


@dataclass
class Tester:
    # Outputs connected to the auxiliary chain.
    pullup: bool = False
    led_pass: bool = False
    led_fail: bool = False
    led_circle: int = 0
    clocks: int = 0

    def __init__(self, uri: str = "ftdi://::/1", freq: int = 100000):
        # Connect to the FT232H on the tester board.
        ctrl = pyftdi.spi.SpiController()
        ctrl.configure(uri)
        self.controller = ctrl

        # Setup the SPI and GPIO ports.
        spi = ctrl.get_port(cs=0, freq=freq, mode=0)
        gpio = ctrl.get_gpio()
        gpio.set_direction(0xF0, 0xF0)
        self.spi = spi
        self.gpio = gpio

        # Disable all control lines.
        self.update_gpio()

        # Disable all LEDs, clocks, and pullups.
        self.update_aux()

    # Change the shift control signals on the board. This function inverts the
    # polarity of the control signals to match their active-low nature in the
    # hardware.
    def update_gpio(self,
                    load: bool = False,
                    store: bool = False,
                    store_aux: bool = False):
        word = 0
        word |= (~load & 1) << 5
        word |= (~store & 1) << 4
        word |= (~store_aux & 1) << 6
        self.gpio.write(word)

    # Pulse the LOAD signal.
    def pulse_load(self):
        self.update_gpio(load=True)
        self.update_gpio()

    # Pulse the STORE signal.
    def pulse_store(self):
        self.update_gpio(store=True)
        self.update_gpio()

    # Pulse the STORE_AUX signal.
    def pulse_store_aux(self):
        self.update_gpio(store_aux=True)
        self.update_gpio()

    # Write raw data to the auxiliary shift chain.
    def write_aux_chain(self, data: bytes = [0, 0]):
        assert len(data) == 2, "aux chain requires 16 bits of data"
        self.spi.write(data)
        self.pulse_store_aux()

    # Write data to the output shift chain. Boards closer to the FT232H and
    # lower output bits appear first in the `data` array. Increasing indices in
    # `data` are further down the chain of testers.
    def write_output_chain(self, data: bytes):
        self.spi.write(list(reversed(data)))
        self.pulse_store()

    # Read raw data from the input shift chain. Same data ordering as for
    # `write_output_chain` applies.
    def read_input_chain(self, num_bytes: int):
        self.pulse_load()
        return self.spi.read(num_bytes)

    # Update the outputs connected to the auxiliary chain.
    def update_aux(self):
        data = [0, 0]
        data[0] |= (self.led_pass & 1) << 1
        data[0] |= (self.led_fail & 1) << 2
        data[0] |= (self.pullup & 1) << 3
        data[0] |= (self.clocks & 0xF) << 4
        data[1] = self.led_circle & 0xFF
        self.write_aux_chain(data)


# Test the GPR.
tester = Tester()
num_mismatches = 0
interactive = False


# Apply some input signals to the GPR.
def apply_inputs(wd: int = 0,
                 we: bool = False,
                 re1: bool = False,
                 re2: bool = False,
                 re3: bool = False):
    # Assemble the control signals.
    ctrl = 0
    ctrl |= (~we & 1) << 0
    ctrl |= (~re1 & 1) << 1
    ctrl |= (~re2 & 1) << 2
    ctrl |= (~re3 & 1) << 3

    # Write tester outputs / GPR inputs.
    outputs = [0] * 8
    outputs[0] = wd  # outputs 0 to 7
    outputs[2] = ctrl  # outputs 16 to 19
    tester.write_output_chain(outputs)

    print(
        f"inputs:  WD={wd:08b}  WE={we:b}  RE1={re1:b}  RE2={re2:b}  RE3={re3:b}"
    )


# Toggle the clock of the GPR.
def clock():
    if interactive:
        print("clock")
        input()
    tester.clocks = 0xF
    tester.update_aux()
    tester.clocks = 0x0
    tester.update_aux()


# Read and check the output signals of the GPR.
def check_outputs(rd1: int, rd2: int, rd3: int):
    # Read tester inputs / GPR outputs (with pullup).
    tester.pullup = True
    tester.update_aux()
    inputs_pu = tester.read_input_chain(8)

    # Read tester inputs / GPR outputs (with pulldown).
    tester.pullup = False
    tester.update_aux()
    inputs_pd = tester.read_input_chain(8)

    # Check the outputs.
    rd1_exp, rd1_act = check_output(rd1, inputs_pu[0], inputs_pd[0])
    rd2_exp, rd2_act = check_output(rd2, inputs_pu[1], inputs_pd[1])
    rd3_exp, rd3_act = check_output(rd3, inputs_pu[2], inputs_pd[2])

    print(
        f"outputs: RD1={rd1_act} ({rd1_exp})  RD2={rd2_act} ({rd2_exp})  RD3={rd3_act} ({rd3_exp})"
    )
    if interactive:
        input()


# Check a single RD output against an expected value.
def check_output(exp: int, act_pu: int, act_pd: int):
    # If the expected value is `None`, we expect all bits to be Z, otherwise
    # format the expected value as an 8 digit binary number.
    exp_str = f"{exp:08b}" if exp is not None else "ZZZZZZZZ"

    # Format the values with pullup and pulldown as an 8 digit binary number. If
    # both values agree on a digit, write that digit. If the values disagree on
    # a digit, write a "Z".
    act_pu = f"{act_pu:08b}"
    act_pd = f"{act_pd:08b}"
    act_str = "".join(pu if pu == pd else "Z"
                      for pu, pd in zip(act_pu, act_pd))

    # Compare actual and expected values. If they differ, count the mismatch.
    # Return the actual value colored red or green according to whether it
    # matches the expected value.
    global num_mismatches
    if act_str != exp_str:
        num_mismatches += 1
        return exp_str, colored(act_str, "red", attrs=["bold"])
    else:
        return exp_str, colored(act_str, "green")


# Write a zero to the register to reset it.
print()
print("Check write of 0x00")
apply_inputs(wd=0x00, we=True)
clock()

# Check that each RD port can be Z or show the zero we just wrote.
apply_inputs(re1=True)
check_outputs(0x00, None, None)
apply_inputs(re2=True)
check_outputs(None, 0x00, None)
apply_inputs(re3=True)
check_outputs(None, None, 0x00)

# Write all ones to the register and check that we can read those back.
print()
print("Check write of 0xFF")
apply_inputs(wd=0xFF, we=True)
clock()
apply_inputs(re1=True, re2=True, re3=True)
check_outputs(0xFF, 0xFF, 0xFF)


# Golden model for the register file. Allows us to just set the inputs, and it
# will keep track of what we expect the register to contain in the `stored_data`
# global variable. So if we decide to read through RE1, RE2, or RE3, it will
# check that we indeed read what the register is supposed to store.
def apply_and_check_golden_model(wd: int = 0,
                                 we: bool = False,
                                 re1: bool = False,
                                 re2: bool = False,
                                 re3: bool = False):
    global stored_data
    apply_inputs(wd, we, re1, re2, re3)
    clock()
    if we:
        stored_data = wd
    check_outputs(
        stored_data if re1 else None,
        stored_data if re2 else None,
        stored_data if re3 else None,
    )


# Perform a few manual checks with the golden model.
print()
print("Check against golden model (manual inputs)")
stored_data = 0xFF
apply_and_check_golden_model(re1=True)
apply_and_check_golden_model(wd=0x55, we=False, re2=True)
apply_and_check_golden_model(wd=0x55, we=True, re2=True)
apply_and_check_golden_model(wd=0xF0, we=False, re3=True)
apply_and_check_golden_model(wd=0xF0, we=True, re3=True)

# Apply a few random inputs and check against the golden model.
num_random_inputs = 250
print()
print("Check against golden model (random inputs)")
for i in range(num_random_inputs):
    tester.led_circle = (1 << (i * 8 // num_random_inputs + 1)) - 1
    apply_and_check_golden_model(
        wd=random.getrandbits(8),
        we=random.getrandbits(1),
        re1=random.getrandbits(1),
        re2=random.getrandbits(1),
        re3=random.getrandbits(1),
    )

# Clear back to zero for aesthetics.
print()
print("Clear to zero")
apply_inputs(wd=0x00, we=True)
clock()
apply_inputs()

# Show pass/fail on LED.
tester.led_fail = num_mismatches > 0
tester.led_pass = num_mismatches == 0
tester.led_circle = 0
tester.update_aux()
if num_mismatches == 0:
    print()
    print("  success: " + colored("all matched", "green", attrs=["bold"]))
    print()
else:
    print()
    print("  FAILED: " +
          colored(f"{num_mismatches} mismatches", "red", attrs=["bold"]))
    print()
    exit(1)
