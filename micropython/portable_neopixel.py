"""
CONCEPT

Everything 8 bit
color256: 0..255
factor_dimm256: 0..255
factor_waveform256: 0..255

factor_65536: 0..MAX_65536 # 65025

CALCULATION

factor_65536 = factor_waveform256*factor_dimm256
effective_color256 = (color256*factor_65536)//65536
"""


from machine import bitstream


MAX_65536 = 255 * 255  # 65025


class NeoPixel:
    def __init__(self, pin, led_count):
        self.pin = pin
        self.led_count = led_count
        self.buf = bytearray(3 * led_count)
        self.pin.init(pin.OUT)

    def write(self, ledstrip):
        ledstrip.copy(self.buf)
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)
