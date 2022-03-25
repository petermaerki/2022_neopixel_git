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
            ledstrip.clear(self.buf, 0)
            return

        # Watch out: This method may be monkey patched in the constructor!
        for i in range(len(self.buf)):
            self.buf[i] = 0

    def trace(self, i):
        buf = self.buf
        j = 3 * i
        v = (buf[j + 1], buf[j], buf[j + 2])
        v = tuple(map(int, v))
        print("%d:%s" % (i, str(v)))

    def add(self, i, factor_65536, color_rgb256):
        assert not LIB_LEDSTRIPE
        assert isinstance(factor_65536, int)
        assert 0 <= factor_65536 <= MAX_65536
        _color_rgb256 = tuple((c * factor_65536) // 65536 for c in color_rgb256)

        # Watch out: This method may be monkey patched in the constructor!
        # color: G R B
        buf = self.buf
        r, g, b = _color_rgb256
        j = 3 * i
        if r:
            buf[j + 1] = min(255, buf[j] + r)
        if g:
            buf[j] = min(255, buf[j + 1] + g)
        if b:
            buf[j + 2] = min(255, buf[j + 2] + b)

    def write(self):
        # BITSTREAM_TYPE_HIGH_LOW = 0
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)


"""
import machine
import neopixel_int
np = neopixel_int.NeoPixel(machine.Pin.board.Y12, n=5 * 96)
np.add(i=0, factor_65536=65000, color_rgb256=(255,0,0))
np.write()
"""
