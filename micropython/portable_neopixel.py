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


try:
    MOCKED = True
    from machine import bitstream

    MOCKED = False

    def create_bytearray(n):
        return bytearray(n)


except:

    def create_bytearray(n):
        return n * [0]


try:
    LIB_LEDSTRIPE = False
    import ledstrip
    LIB_LEDSTRIPE = True
except:
    pass


MAX_65536 = 255 * 255  # 65025


class NeoPixel:
    def __init__(self, pin, n):
        self.pin = pin
        self.n = n
        self.buf = create_bytearray(3 * n)
        if not MOCKED:
            self.pin.init(pin.OUT)

        self.clear(0)

    def clear(self, _color=0):
        if LIB_LEDSTRIPE:
            ledstrip.int_clear(self.buf, 0)
            return

    def write(self):
        ledstrip.int_copy(self.buf)
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)


"""
import machine
import neopixel_int
np = neopixel_int.NeoPixel(machine.Pin.board.Y12, n=5 * 96)
np.add(i=0, factor_65536=65000, color_rgb256=(255,0,0))
np.write()
"""
