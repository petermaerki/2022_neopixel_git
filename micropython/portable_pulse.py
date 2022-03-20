"""
ABBREVIATION

led: distance from one led to another
b: "Beat" A write on the led strip
bpl: "Beats per Led" - the speed of the pulse
length_l: Length in leds.
length_b: Length in beats.
position_b: Position in beats.
position_l: Position of a led
position_lc: Position of a color within a led (G R B)

"""

import math
import neopixel_int

DIMM_TIME = 500
DIMM_TIME_FLOAT = float(DIMM_TIME)


def create_waveform256(lenght):
    """
    >>> waveform = create_waveform256(3)
    >>> waveform
    (10, 255, 10)

    >>> waveform = create_waveform256(12)
    >>> waveform
    (0, 1, 15, 63, 143, 221, 255, 221, 143, 63, 15, 1)
    """
    # wave_array is an array with integers to max 255/2, colors
    if lenght == 3:
        return (10, 255, 10)

    waveform256 = [0] * lenght
    for i in range(lenght):
        phase = i / lenght * 2 * math.pi
        value256 = int(255.0 * (-math.cos(phase) * 0.5 + 0.5) ** 2)
        assert 0 <= value256 < 256
        waveform256[i] = value256
    return tuple(waveform256)


class Pulse:
    """
    >>> np = neopixel_int.NeoPixel(None, 20)
    >>> p = Pulse(strip_length_l=np.n, color_grb256=(0,255,0), length_l=4, speed_bpl=3, lifetime_b=1000, blink=False)

    >>> p._position_b = 6
    >>> p.show(np)
    2:(0, 0, 0)
    3:(0, 62, 0)
    4:(0, 254, 0)
    5:(0, 62, 0)

    >>> p._position_b = 7
    >>> p.show(np)
    3:(0, 14, 0)
    4:(0, 220, 0)
    5:(0, 142, 0)
    6:(0, 0, 0)

    >>> p._position_b = -7
    >>> p.show(np)
    0:(0, 220, 0)
    1:(0, 14, 0)


    >>> np = neopixel_int.NeoPixel(None, 200)
    >>> p = Pulse(strip_length_l=np.n, color_grb256=(127, 0, 0), length_l=10, speed_bpl=3, lifetime_b=42, blink=False)
    >>> p._position_b = 46
    >>> p._lifetime_b = -56
    >>> p.show(np)
    16:(0, 0, 0)
    17:(6, 0, 0)
    18:(34, 0, 0)
    19:(78, 0, 0)
    20:(110, 0, 0)
    21:(102, 0, 0)
    22:(63, 0, 0)
    23:(22, 0, 0)
    24:(2, 0, 0)
    25:(0, 0, 0)
    """

    def __init__(self, strip_length_l, color_grb256, length_l, speed_bpl, lifetime_b, blink):
        self._color_grb256 = color_grb256
        self._on = True
        self.strip_length_l = strip_length_l
        self._lifetime_b = lifetime_b
        self._blink = blink
        self._length_l = length_l
        self._speed_bpl = speed_bpl
        self._waveform = create_waveform256(length_l * speed_bpl)
        self.led_current = self._length_l * sum(self._color_grb256)
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
        if not self._on:
            return

        if neopixel_int.LIB_LEDSTRIPE:
            first_led_relative_l = -(-self._position_b // self._speed_bpl)
            pos_begin_b = first_led_relative_l * self._speed_bpl - self._position_b

            # self._lifetime_b >= 0: lifetime_factor = 100
            # self._lifetime_b <= -DIMM_TIME: lifetime_factor = 0
            # lifetime_factor = max(0.0, min(1.0, 1.0 + self._lifetime_b/DIMM_TIME_FLOAT))
            lifetime_factor256 = max(0, min(100, 100 + (100 * self._lifetime_b) // DIMM_TIME))

            if False:
                for i in self._color_grb256:
                    assert isinstance(i, int)
                assert isinstance(lifetime_factor256, int)
                assert isinstance(first_led_relative_l, int)
                assert isinstance(pos_begin_b, int)
                assert isinstance(self._speed_bpl, int)
                for i in self._waveform:
                    assert isinstance(i, int)
                print("first_led_relative_l", first_led_relative_l, type(first_led_relative_l))
                print("lifetime_factor", lifetime_factor256, type(lifetime_factor256))
                print("self._color", self._color_grb256, type(self._color_grb256))
                print("self._waveform", self._waveform, type(self._waveform))
                print("pos_begin_b", pos_begin_b, type(pos_begin_b))
                print("self._speed_bpl", self._speed_bpl, type(self._speed_bpl))
            assert isinstance(self._waveform, tuple)
            assert isinstance(self._color_grb256, tuple)
            neopixel_int.ledstrip.pulse(
                np.buf,
                first_led_relative_l,
                lifetime_factor256,
                self._color_grb256,
                self._waveform,
                pos_begin_b,
                self._speed_bpl,
            )
            # np.write()
            # print([p for p in np.buf])
            return

        first_led_relative_l = -(-self._position_b // self._speed_bpl)
        pos_begin_b = first_led_relative_l * self._speed_bpl - self._position_b

        # self._lifetime_b >= 0: lifetime_factor = 256
        # self._lifetime_b <= -DIMM_TIME: lifetime_factor = 0
        lifetime_factor256 = max(0, min(255, 255 + int(256*self._lifetime_b/DIMM_TIME_FLOAT)))

        for i_led_0 in range(self._length_l):
            try:
                value256 = self._waveform[pos_begin_b + i_led_0 * self._speed_bpl]
            except KeyError:
                continue
            # TODO: Move to C-Code
            factor_65536 = value256*lifetime_factor256
            i_led = first_led_relative_l + i_led_0
            if not 0 <= i_led < self.strip_length_l:
                continue
            np.add(i_led, factor_65536, self._color_grb256)

            if False:
                print("self._length_l", self._length_l)
                print("factor_65536", factor_65536)
                print("first_led_relative_l", first_led_relative_l)
                print("lifetime_factor", lifetime_factor256)
                print("self._lifetime_b", self._lifetime_b)
                print("self._position_b", self._position_b)
                print("self._color", self._color_grb256)
                print("self._waveform", self._waveform)
                print("self._speed_bpl", self._speed_bpl)
            #   np.trace(i_led)
            if neopixel_int.MOCKED:
                np.trace(i_led)


if __name__ == "__main__":
    Pulse(
        strip_length_l=200,
        color_grb256=(0, 255, 0),  # gruen
        length_l=10,
        speed_bpl=5,
        lifetime_b=1000,
        blink=False,
    )

    import doctest

    doctest.testmod()
