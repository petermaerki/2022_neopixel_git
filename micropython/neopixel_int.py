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
    if False:
        import ledstrip
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

    def add(self, i, factor_65536, color256):
        assert isinstance(factor_65536, int)
        assert 0 <= factor_65536 < 65536
        # TODO: shift right
        _color256 = tuple((c*factor_65536)//65536 for c in color256)
        for c in _color256:
            assert 0 <= c < 256
        if LIB_LEDSTRIPE:
            ledstrip.add(self.buf, i, 1, _color256)
            return

        # Watch out: This method may be monkey patched in the constructor!
        # color: G R B
        buf = self.buf
        g, r, b = _color256
        j = 3 * i
        if g:
            buf[j + 1] = min(255, buf[j] + 1 * g)
        if r:
            buf[j] = min(255, buf[j+1] + 1 * r)
        if b:
            buf[j + 2] = min(255, buf[j+2] + 1 * b)

    def write(self):
        # BITSTREAM_TYPE_HIGH_LOW = 0
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)
