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

import portable_neopixel as neopixel

DIMM_TIME_L = 40
DIMM_TIME_FLOAT = float(DIMM_TIME_L)

def calculate_waveform_point256(l, lenght):
    phase = l / lenght * 2 * math.pi
    value256 = int(254.0 * (-math.cos(phase) * 0.5 + 0.5) ** 2) + 1
    assert 0 <= value256 < 256
    return value256

def create_waveform256(lenght):
    """
    >>> create_waveform256(1)
    (255,)

    >>> create_waveform256(2)
    (255, 255)

    >>> create_waveform256(3)
    (10, 255, 10)

    >>> create_waveform256(12)
    (1, 2, 16, 64, 143, 222, 255, 222, 143, 64, 16, 2)
    """
    # wave_array is an array with integers to max 255/2, colors
    if lenght == 1:
        return (255,)

    if lenght == 2:
        return (255, 255)

    if lenght == 3:
        return (10, 255, 10)

    return tuple(calculate_waveform_point256(l, lenght) for l in range(lenght))


class Pulse:
    """
    >>> np = neopixel.NeoPixel(None, 20)
    >>> p = Pulse(strip_length_l=np.n, color_rgb256=(0,255,0), length_l=4, speed_divider_bpl=3, lifetime_l=30, blink=False)

    >>> p._position_b = 6
    >>> p.show(np)
    2:(0, 0, 0)
    3:(0, 63, 0)
    4:(0, 253, 0)
    5:(0, 63, 0)

    >>> p._position_b = 7
    >>> p.show(np)
    3:(0, 15, 0)
    4:(0, 220, 0)
    5:(0, 141, 0)
    6:(0, 1, 0)
    >>> p._position_b = -7
    >>> p.show(np)
    0:(0, 220, 0)
    1:(0, 15, 0)

    >>> np = neopixel.NeoPixel(None, 200)
    >>> p = Pulse(strip_length_l=np.n, color_rgb256=(127, 0, 0), length_l=10, speed_divider_bpl=3, lifetime_l=42, blink=False)
    >>> p._position_b = 46
    >>> p._lifetime_b = -56
    >>> p.show(np)
    16:(0, 0, 0)
    17:(4, 0, 0)
    18:(20, 0, 0)
    19:(46, 0, 0)
    20:(65, 0, 0)
    21:(61, 0, 0)
    22:(37, 0, 0)
    23:(13, 0, 0)
    24:(1, 0, 0)
    25:(0, 0, 0)
    """

    def __init__(
        self,
        strip_length_l,
        color_rgb256,
        length_l,
        speed_divider_bpl,
        lifetime_l,
        blink=False,
        killer=False,
    ):
        self.hit = False
        self._on = True
        self._color_rgb256 = color_rgb256
        self.strip_length_l = strip_length_l
        self._lifetime_b = lifetime_l * speed_divider_bpl
        self.length_l = length_l
        self._speed_divider_bpl = speed_divider_bpl
        self._waveform256 = create_waveform256(length_l * speed_divider_bpl)
        self._blink = blink
        self._killer = killer
        self.led_current = self.length_l
        self._forward = True
        self._position_b = -length_l * speed_divider_bpl
        self._start_b = 0
        self._end_b = (strip_length_l - length_l) * speed_divider_bpl

    @property
    def position_start_l(self):
        return self._position_b // self._speed_divider_bpl

    def end_of_life(self):
        return self._lifetime_b < -DIMM_TIME_L * self._speed_divider_bpl

    def interact(self, pulse_list):
        if not self._killer:
            return
        # We are the killer
        self_start_l = self.position_start_l
        for pulse in pulse_list:
            if pulse == self:
                continue
            if pulse.hit:
                continue
            pulse_start_l = pulse.position_start_l
            sign1 = self_start_l > pulse_start_l + pulse.length_l
            sign2 = pulse_start_l > self_start_l + self.length_l
            if sign1 == sign2:
                print("hit")
                pulse.strike()

    def do_increment(self):
        if self._blink or self._killer:
            self._on = not self._on

        self._lifetime_b -= 1

        if self.hit:
            # Do not move anymore
            return

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

    def strike(self):
        self.hit = True
        self._blink = True
        if self._lifetime_b > 0:
            self._lifetime_b = 0

    def show(self, np):
        if not self._on:
            return

        first_led_relative_l = -(-self._position_b // self._speed_divider_bpl)
        pos_begin_b = first_led_relative_l * self._speed_divider_bpl - self._position_b

        # self._lifetime_b >= 0: lifetime_factor256 = 256
        # self._lifetime_b <= -DIMM_TIME_L*self._speed_divider_bpl: lifetime_factor256 = 0
        lifetime_factor256 = 255 + (255 * self._lifetime_b) // (
            DIMM_TIME_L * self._speed_divider_bpl
        )
        lifetime_factor256 = max(0, lifetime_factor256)
        lifetime_factor256 = min(255, lifetime_factor256)

        if neopixel.LIB_LEDSTRIPE:
            assert isinstance(self._waveform256, tuple)
            assert isinstance(self._color_rgb256, tuple)
            neopixel.ledstrip.pulse(
                np.buf,
                first_led_relative_l,
                lifetime_factor256,
                self._color_rgb256,
                self._waveform256,
                pos_begin_b,
                self._speed_divider_bpl,
            )
            return

        for i_led_0 in range(self.length_l):
            try:
                value256 = self._waveform256[
                    pos_begin_b + i_led_0 * self._speed_divider_bpl
                ]
            except KeyError:
                continue
            # TODO: Move to C-Code
            factor_65536 = value256 * lifetime_factor256
            i_led = first_led_relative_l + i_led_0
            if not 0 <= i_led < self.strip_length_l:
                continue
            np.add(i_led, factor_65536, self._color_rgb256)

            if neopixel.MOCKED:
                np.trace(i_led)


if __name__ == "__main__":
    Pulse(
        strip_length_l=200,
        color_rgb256=(0, 255, 0),  # gruen
        length_l=10,
        speed_divider_bpl=5,
        lifetime_l=1000,
        blink=False,
    )

    import doctest

    doctest.testmod()
