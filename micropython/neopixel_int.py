# NeoPixel driver for MicroPython
# MIT license; Copyright (c) 2016 Damien P. George, 2021 Jim Mussared

try:
    from machine import bitstream

    def create_bytearray(n):
        return bytearray(n)

    MOCKED = False
except:

    def create_bytearray(n):
        return n * [0]

    MOCKED = True


class NeoPixel:
    def __init__(self, pin, n):
        self.pin = pin
        self.n = n
        self.buf = create_bytearray(3 * n)
        if not MOCKED:
            self.pin.init(pin.OUT)
        self.clear()

    def clear(self):
        for i in range(len(self.buf)):
            self.buf[i] = 0

    def trace(self, i):
        buf = self.buf
        j = 3 * i
        v = (buf[j + 1], buf[j], buf[j + 2])
        v = list(map(int, v))
        print("%d:%s" % (i, str(v)))

    def add(self, i, value, color):
        # G R B
        buf = self.buf
        j = 3 * i
        r, g, b = color
        if r:
            buf[j + 1] = min(255, buf[j + 1] + value * r)
        if g:
            buf[j] = min(255, buf[j] + value * g)
        if b:
            buf[j + 2] = min(255, buf[j + 2] + value * b)

    def write(self):
        # BITSTREAM_TYPE_HIGH_LOW = 0
        bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)
