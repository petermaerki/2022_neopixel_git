# NeoPixel driver for MicroPython
# MIT license; Copyright (c) 2016 Damien P. George, 2021 Jim Mussared

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
    import ledstripe
    LIB_LEDSTRIPE = True
except:
    pass

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
            ledstripe.clear(self.buf, 0)
            return

        # Watch out: This method may be monkey patched in the constructor!
        for i in range(len(self.buf)):
            self.buf[i] = 0

    def trace(self, i):
        buf = self.buf
        j = 3 * i
        v = (buf[j + 1], buf[j], buf[j + 2])
        v = list(map(int, v))
        print("%d:%s" % (i, str(v)))

    def inc(self, i, value, color):
        assert 0.0 <= value <= 256.0
        _color = tuple(int(c*value) for c in color)
        if LIB_LEDSTRIPE:
            ledstripe.inc(self.buf, i, 1, _color)
            return

        # Watch out: This method may be monkey patched in the constructor!
        # color: G R B
        buf = self.buf
        r, g, b = _color
        j = 3 * i
        if r:
            buf[j + 1] = min(255, buf[j] + 1 * r)
        if g:
            buf[j] = min(255, buf[j+1] + 1 * g)
        if b:
            buf[j + 2] = min(255, buf[j+2] + 1 * b)

    def write(self):
        # BITSTREAM_TYPE_HIGH_LOW = 0
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)
