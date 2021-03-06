from portable_pulse import Pulse, DIMM_TIME_L
import random


PREDEFINED_SPEED_DIVIDER_BPL = [5, 10, 1, 5, 2, 1, 6, 3, 10]
PREDEFINED_LENGTHS_L = [50, 30, 20, 10, 5, 2]
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
PREDEFINED_LIFETIMES_L = [50, 100, 200, 600, 1500]


def create_pulse_killer(np):
    return Pulse(
        strip_length_l=np.n,
        color_rgb256=(255, 0, 0),  # red
        length_l=3,
        speed_divider_bpl=1,  # 120,
        lifetime_l=800,
        killer=True,
    )


def create_predefined_pulses(np):
    return [
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(0, 255, 0),  # gruen
            length_l=10,
            speed_divider_bpl=3,
            lifetime_l=400,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(0, 0, 255),  # blau
            length_l=5,
            speed_divider_bpl=7,
            lifetime_l=1500,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(255, 0, 0),  # red
            length_l=3,
            speed_divider_bpl=2,
            lifetime_l=800,
        ),
        Pulse(
            strip_length_l=np.n,
            color_rgb256=(255, 255, 0),  # yellow
            length_l=20,
            speed_divider_bpl=6,
            lifetime_l=1200,
        ),
    ]


def create_random_pulse(np, duration_ms):
    length_l = random.choice(PREDEFINED_LENGTHS_L)
    # speed_divider_bpl = duration_ms // 200
    # speed_divider_bpl = min(20, max(1, speed_divider_bpl))
    speed_divider_bpl = random.choice(PREDEFINED_SPEED_DIVIDER_BPL)
    pulse = Pulse(
        strip_length_l=np.n,
        length_l=length_l,
        color_rgb256=random.choice(PREDEFINED_COLORS_RGB256),
        speed_divider_bpl=speed_divider_bpl,
        lifetime_l=random.choice(PREDEFINED_LIFETIMES_L) + DIMM_TIME_L,
        # blink=random.random() < 0.05,
    )
    return pulse


class PulseGenerator:
    def __init__(self, np):
        self._np = np
        self.reset()

    def reset(self):
        self._queue = create_predefined_pulses(self._np)

    def get_next_pulse(self, duration_ms, current_at_limit):
        if len(self._queue) > 0:
            return self._queue.pop(0)
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return create_random_pulse(self._np, duration_ms)
