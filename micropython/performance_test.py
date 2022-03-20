"""
NEOPIXEL
164.6 us: NP[1] = 1
103.9 us: d = NP[1]
199.4 us: NP[1] = min(NP[1], 255)
INTEGER
7.9 us: d=min(d, 1)
1.2 us: d = d + 1
1.3 us: d *= 1
1.3 us: d //= 1
FLOAT
9.4 us: x=min(x, 1.0)
5.0 us: x = x + 1.1
5.0 us: x *= 1.1
5.0 us: x /= 1.1
6.6 us: d = int(x)


LED STRIP PERFORMANCE

All dark
  110 beats per second
1 pulse with 10 pixel
  87 beats per second
limit_pulses() to 1200
  8.5 beats per second
"""
import time
import math

import machine
import neopixel
import builtins


class Timeit:
    DURATION_US = 1000000

    def __init__(self, calibration_per_cycle_us=0):
        self._calibration_per_cycle_us = calibration_per_cycle_us
        self._i = 0
        self._end_ticks_us = time.ticks_us() + 1000000

    def go(self):
        self._i += 1
        return time.ticks_diff(self._end_ticks_us, time.ticks_us()) > 0

    def time(self, cmd):
        per_cycle_us = Timeit.DURATION_US / self._i - self._calibration_per_cycle_us
        print("%0.1f us: %s" % (per_cycle_us, cmd))
        return per_cycle_us


def test():
    t = Timeit()
    while t.go():
        pass
    calib = t.time("<calib>")

    print("BYTEARRY micropython")
    buf = builtins.bytearray(300)

    t = Timeit(calib)
    color = (1, 2, 3)
    while t.go():
        r, g, b = color
    t.time("r, g, b = color")

    t = Timeit(calib)
    while t.go():
        value = 2
        i = 3
        r, g, b = color
        j = 3 * i
        if r:
            buf[j + 1] = min(255, buf[j + 1] + value * r)
        if g:
            buf[j] = min(255, buf[j] + value * g)
        if b:
            buf[j + 2] = min(255, buf[j + 2] + value * b)
    t.time("display buf 'micropython'")

    print("BYTEARRY hans")
    t = Timeit(calib)
    while t.go():
        buf.add(42, 1, color)
    t.time("display buf 'micropython': buf.add(i, 1, color)")

    t = Timeit(calib)
    while t.go():
        buf.add(42, 1, 1)
    t.time("buf.add(i, 1, 1)")

    t = Timeit(calib)
    while t.go():
        buf.add(42, 1, (1, 2, 3))
    t.time("slow tuple: buf.add(i, 1, (1, 2, 3))")

    print("NEOPIXEL")
    NP = neopixel.NeoPixel(machine.Pin.board.Y10, n=5 * 96, bpp=3, timing=1)
    t = Timeit(calib)
    while t.go():
        NP[1] = (1, 2, 3)
    t.time("NP[1] = 1")

    t = Timeit(calib)
    while t.go():
        d = NP[1]
    t.time("d = NP[1]")

    t = Timeit(calib)
    while t.go():
        last_color = NP[7]
        red = min(6 * last_color[0], 255)
        green = min(6 * last_color[1], 255)
        blue = min(6 * last_color[2], 255)
        NP[7] = (red, green, blue)
    t.time("NP[1] = min(NP[1], 255)")

    print("INTEGER")
    d = 1
    t = Timeit(calib)
    while t.go():
        d = min(d, 1)
    t.time("d=min(d, 1)")

    t = Timeit(calib)
    while t.go():
        d = d + 1
    t.time("d = d + 1")

    t = Timeit(calib)
    while t.go():
        d *= 1
    t.time("d *= 1")

    t = Timeit(calib)
    while t.go():
        d //= 1
    t.time("d //= 1")

    print("FLOAT")
    x = 0.5
    t = Timeit(calib)
    while t.go():
        x = min(x, 1.0)
    t.time("x=min(x, 1.0)")

    x = 0.5
    t = Timeit(calib)
    while t.go():
        x = x + 1.1
    t.time("x = x + 1.1")

    x = 0.5
    t = Timeit(calib)
    while t.go():
        x *= 1.1
    t.time("x *= 1.1")

    x = 0.5
    t = Timeit(calib)
    while t.go():
        x /= 1.1
    t.time("x /= 1.1")

    x = 0.5
    t = Timeit(calib)
    while t.go():
        d = int(x)
    t.time("d = int(x)")

