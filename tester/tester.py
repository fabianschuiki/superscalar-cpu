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

    # Update the circle LEDs to show progress.
    def set_progress_circle(self, current: int, end: int):
        self.led_circle = (1 << (current * 8 // end + 1)) - 1


# Check a single output against an expected value.
def check_output(exp: int, act_pu: int, act_pd: int, width: int = 8):
    # If the expected value is `None`, we expect all bits to be Z, otherwise
    # format the expected value as a binary number.
    exp_str = f"{exp:0{width}b}" if exp is not None else "Z" * width

    # Format the values with pullup and pulldown as a binary number. If both
    # values agree on a digit, write that digit. If the values disagree on a
    # digit, write a "Z".
    act_pu = f"{act_pu:0{width}b}"
    act_pd = f"{act_pd:0{width}b}"
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


# Test the GPR.
tester = Tester()
num_mismatches = 0


# Check that addition works.
def check(lhs: int, rhs: int, sub: int):
    # Write tester outputs / ALU inputs.
    outputs = [0] * 8
    outputs[0] = lhs  # outputs 0 to 7
    outputs[2] = rhs  # outputs 16 to 23
    outputs[4] = sub  # output 32
    tester.write_output_chain(outputs)

    # Read tester inputs / ALU outputs (with pullup).
    tester.pullup = True
    tester.update_aux()
    inputs_pu = tester.read_input_chain(8)

    # Read tester inputs / ALU outputs (with pulldown).
    tester.pullup = False
    tester.update_aux()
    inputs_pd = tester.read_input_chain(8)

    # Check the outputs.
    value = lhs + (~rhs & 0xFF) + 1 if sub else lhs + rhs
    result_exp, result_act = check_output(value & 0xFF, inputs_pu[0],
                                          inputs_pd[0])
    co_exp, co_act = check_output((value >> 8) & 0x1,
                                  inputs_pu[2] & 0x1,
                                  inputs_pd[2] & 0x1,
                                  width=1)

    print(f"{lhs:08b} {rhs:08b} {sub:01b} = " +
          f"{co_act} {result_act} ({co_exp} {result_exp})")


# Randomized testing.
num_checks = 1000
for i in range(num_checks):
    tester.set_progress_circle(i, num_checks)
    check(random.getrandbits(8), random.getrandbits(8), random.getrandbits(1))
check(0, 0, 0)

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
