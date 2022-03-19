"""
ABBREVIATION

led: distance from one led to another
b: "Beat" A write on the led strip
bpl: "Beats per Led" - the speed of the pulse
length_l: Length in leds.
length_b: Length in beats.
position_b: Position in beats.

CONCEPTS


"""

import math
from neopixel_int import NeoPixel, MOCKED

DIMM_TIME = 500
DIMM_TIME_FLOAT = float(DIMM_TIME)


def create_waveform(lenght):
    """
    >>> waveform = create_waveform(3)
    >>> list(map(int, waveform))
    [32, 64, 32]

    >>> waveform = create_waveform(12)
    >>> list(map(int, waveform))
    [0, 0, 7, 31, 71, 110, 127, 110, 71, 31, 7, 0]
    """
    # wave_array is an array with integers to max 255/2, colors
    if lenght == 3:
        return [5, 128, 5]

    waveform = [0] * lenght
    for i in range(lenght):
        phase = i / lenght * 2 * math.pi
        waveform[i] = int(0.5 * 255.0 * (-math.cos(phase) * 0.5 + 0.5) ** 2)
    return waveform


class Pulse:
    """
    >>> np = NeoPixel(None, 20)
    >>> p = Pulse(strip_length_l=np.n, color=(0,2.0,0), length_l=4, speed_bpl=3, lifetime_b=1000, blink=False)

    >>> p._position_b = 6
    >>> p.show(np)
    2:[0, 0, 0]
    3:[0, 62, 0]
    4:[0, 254, 0]
    5:[0, 62, 0]

    >>> p._position_b = 7
    >>> p.show(np)
    3:[0, 76, 0]
    4:[0, 255, 0]
    5:[0, 204, 0]
    6:[0, 0, 0]

    >>> p._position_b = -7
    >>> p.show(np)
    0:[0, 220, 0]
    1:[0, 14, 0]
    """

    def __init__(self, strip_length_l, color, length_l, speed_bpl, lifetime_b, blink):
        self._color = color
        self._on = True
        self.strip_length_l = strip_length_l
        self._lifetime_b = lifetime_b
        self._blink = blink
        self._length_l = length_l
        self._speed_bpl = speed_bpl
        self._waveform = create_waveform(length_l * speed_bpl)
        self.led_current = self._length_l * sum(self._color)
        self._forward = True
        self._position_b = -length_l * speed_bpl
        self._start_b = 0
        self._end_b = (strip_length_l - length_l) * speed_bpl

    def end_of_life(self):
        return self._lifetime_b < -DIMM_TIME

    def do_increment(self):
        if self._blink:
            self._on = not self._on

        self._lifetime_b -= 1

        if self._forward:
            # Forward
            self._position_b += 1
            if self._position_b > self._end_b:
                # change direcction at the end
                self._forward = False
        else:
            # Backward
            self._position_b -= 1
            if self._position_b <= self._start_b:
                # change direcction at the start
                self._forward = True

    def show(self, np):
        first_led_relative_l = -(-self._position_b // self._speed_bpl)
        pos_begin_b = first_led_relative_l * self._speed_bpl - self._position_b

        for i_led_0 in range(self._length_l):
            if not self._on:
                continue
            try:
                value = self._waveform[pos_begin_b + i_led_0 * self._speed_bpl]
            except KeyError:
                continue
            if self._lifetime_b < 0:
                value = int(value + float(self._lifetime_b) / DIMM_TIME_FLOAT * 127.0)
                value = max(0, value)
            i_led = first_led_relative_l + i_led_0
            if not 0 <= i_led < self.strip_length_l:
                continue
            np.inc(i_led, value, self._color)

            if MOCKED:
                np.trace(i_led)


if __name__ == "__main__":
    Pulse(
        strip_length_l=200,
        color=(0, 2, 0),  # gruen
        length_l=10,
        speed_bpl=5,
        lifetime_b=1000,
        blink=False,
    )

    import doctest

    doctest.testmod()
