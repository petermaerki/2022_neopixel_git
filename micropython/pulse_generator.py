from portable_pulse import Pulse, DIMM_TIME_L, WaveformLong, WaveformPulse
import random


# PREDEFINED_SPEED_DIVIDER_BPL = [5, 10, 1, 5, 2, 1, 6, 3, 10]
# PREDEFINED_LENGTHS_L = [50, 30, 20, 10, 5, 2]
PREDEFINED_COLORS_RGB256 = [
    (255, 0, 0),  # red
    (255, 127, 0),  # orange
    (255, 255, 0),  # yellow
    (127, 255, 0),  # giftgruen
    (0, 255, 0),  # gruen
    (0, 255, 127),  # grausiggruen
    (0, 255, 255),  # cyan
    (0, 127, 255),  # komischblau
    (0, 0, 255),  # blau
    (127, 0, 255),  # komischblau 2
    (255, 0, 255),  # magenta
    (255, 0, 127),  # komischpink
    (255, 255, 255),  # weiss
]
PREDEFINED_LIFETIMES_L = [500, 800, 1200, 3000, 5000]


def create_pulse_killer(np):
    return Pulse(
        strip_length_l=np.n,
        color_rgb256=(255, 0, 0),  # red
        waveform=WaveformPulse(3),
        speed_divider_bpl=1,  # 120,
        lifetime_l=int(np.n * 1.3),
        killer=True,
    )


def create_predefined_pulses(np):
    return [
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(0, 255, 0),  # gruen
            waveform=WaveformPulse(10),
            speed_divider_bpl=3,
            lifetime_l=400,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(0, 0, 255),  # blau
            waveform=WaveformPulse(5),
            speed_divider_bpl=7,
            lifetime_l=1500,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(255, 0, 0),  # red
            waveform=WaveformPulse(3),
            speed_divider_bpl=2,
            lifetime_l=800,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(255, 255, 0),  # yellow
            waveform=WaveformPulse(20),
            speed_divider_bpl=6,
            lifetime_l=1200,
        ),
    ]


class PulseGenerator:
    def __init__(self, np):
        self._np = np
        self._waveform_long = WaveformLong(4*96)
        self.reset()

    def reset(self):
        self._queue = create_predefined_pulses(self._np)

    def get_next_pulse(self, duration_ms, current_at_limit):
        if len(self._queue) > 0:
            return self._queue.pop(0)
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)

        # length_l = random.choice(PREDEFINED_LENGTHS_L)
        # speed_divider_bpl = random.choice(PREDEFINED_SPEED_DIVIDER_BPL)
        length_l = max(2, duration_ms // 20)
        # duration_ms=10: speed_divider_bpl=1
        # duration_ms=2000: speed_divider_bpl=100
        speed_divider_bpl = duration_ms // 20
        speed_divider_bpl = min(15, max(1, speed_divider_bpl))
        print("length_l=%d, speed_divider_bpl=%d" % (length_l, speed_divider_bpl))
        return Pulse(
            strip_length_l=self._np.n,
            waveform=WaveformPulse(length_l),
            color_rgb256=random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=speed_divider_bpl,
            lifetime_l=random.choice(PREDEFINED_LIFETIMES_L) + DIMM_TIME_L,
        )

    def get_next_wave(self, duration_ms, current_at_limit):
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return Pulse(
            strip_length_l=self._np.n,
            waveform=self._waveform_long,
            color_rgb256= random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=1,
            lifetime_l=3 * self._np.n,
        )
