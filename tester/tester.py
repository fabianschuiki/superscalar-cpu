#!/usr/bin/env python3
import pyftdi
import pyftdi.spi
from time import sleep
from dataclasses import dataclass
from termcolor import colored


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


def format_bits(byte: int, z: int) -> str:
    result = ""
    for i in range(8):
        if z & (1 << i):
            result += "Z"
        elif byte & (1 << i):
            result += "1"
        else:
            result += "0"
    return result


def print_blocks(prefix: str, dataA: bytes, dataB: bytes):
    blocks = [
        format_bits(byteA, byteA ^ byteB)
        for byteA, byteB in zip(dataA, dataB)
    ]
    print(prefix + " ".join(blocks[::2]))
    print(prefix + " ".join(blocks[1::2]))


# Test the 4 bit multiplier.
tester = Tester()
num_mismatches = 0

# Loop over all input combinations.
for A in range(16):
    # Show progress on circle LEDs.
    bar = A // 2 + 1  # e.g. A//2=3 -> bar=4
    bar = 1 << bar  # e.g. 0b00001000
    bar -= 1  # e.g. 0b00000111  (3 LEDs lit)
    tester.led_circle = bar
    tester.update_aux()

    for B in range(16):
        # Write outputs.
        data = [0] * 8
        data[0] = A
        data[2] = B
        tester.write_output_chain(data)
        # print_blocks("out: ", data, data)

        # Read inputs (with pullup).
        tester.pullup = True
        tester.update_aux()
        data_pu = tester.read_input_chain(8)

        # Read inputs (with pulldown).
        tester.pullup = False
        tester.update_aux()
        data_pd = tester.read_input_chain(8)

        # print_blocks("in:  ", data_pu, data_pd)

        # Check that the multiplier does the right thing.
        assert data_pu[7] == data_pd[7], "multiplier output disconnected?"
        Zexp = A * B
        Zact = data_pu[7]
        if Zact != Zexp:
            num_mismatches += 1

        # Print a summary.
        color, attrs = ("red", ["bold"]) if Zact != Zexp else ("green", None)
        Zact_bin = colored(f"{Zact:08b}", color, attrs=attrs)
        Zact_dec = colored(f"{Zact}", color, attrs=attrs)
        print(
            f"{A:04b} {B:04b} {Zact_bin} ({Zexp:08b})  {A}*{B}={Zact_dec} ({Zexp})"
        )

# Show pass/fail on LED.
tester.led_fail = num_mismatches > 0
tester.led_pass = num_mismatches == 0
tester.led_circle = 0
tester.update_aux()
assert num_mismatches == 0, f"{num_mismatches} mismatches"
