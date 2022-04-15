from portable_pulse import Pulse, DIMM_TIME_L, WaveformLong, WaveformPulse
import random



MIN_TIME_BEAT_MS = 40

# PREDEFINED_SPEED_DIVIDER_BPL = [5, 10, 1, 5, 2, 1, 6, 3, 10]
# PREDEFINED_LENGTHS_L = [50, 30, 20, 10, 5, 2]
PREDEFINED_COLORS_RGB256 = [
    (255, 127, 0),  # orange
    (0, 127, 255),  # komischblau
    (255, 255, 0),  # yellow
    (127, 255, 0),  # giftgruen
    (255, 0, 0),  # red
    (0, 255, 255),  # cyan
    (0, 0, 255),  # blau
    (0, 255, 0),  # gruen
    (127, 0, 255),  # komischblau 2
    (255, 0, 255),  # magenta
    (0, 255, 127),  # grausiggruen
    (255, 255, 255),  # weiss
    (255, 0, 127),  # komischpink

]
#PREDEFINED_LIFETIMES_L = [500, 800, 1200, 3000, 5000]
PREDEFINED_LIFETIMES_S = [5, 10, 20, 30, 40, 50, 60, 120, 180, 240, 300]

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
# <<<<<<< HEAD
        Pulse(
            strip_length_l=np.led_count,
            color_rgb256=(0, 255, 0),  # gruen
            waveform=WaveformPulse(10),
            speed_divider_bpl=3,
            lifetime_l=400,
        ),
        Pulse(
            strip_length_l=np.led_count,
            color_rgb256=(0, 0, 255),  # blau
            waveform=WaveformPulse(5),
            speed_divider_bpl=7,
            lifetime_l=800,
        ),
        Pulse(
            strip_length_l=np.led_count,
            color_rgb256=(255, 0, 0),  # red
            waveform=WaveformPulse(3),
            speed_divider_bpl=2,
            lifetime_l=800,
        ),
# <<<<<<< HEAD
        Pulse(
            strip_length_l=np.led_count,
            color_rgb256=(255, 255, 0),  # yellow
            waveform=WaveformPulse(20),
            speed_divider_bpl=6,
            lifetime_l=1200,
        ),
# =======
# >>>>>>> d3eb5fa (.)
# =======
        # Pulse(
        #     strip_length_l=np.n,
        #     color_rgb256=(0, 255, 0),  # gruen
        #     waveform=WaveformPulse(10),
        #     speed_divider_bpl=3,
        #     lifetime_l=400,
        # ),
        # Pulse(
        #     strip_length_l=np.n,
        #     color_rgb256=(0, 0, 255),  # blau
        #     waveform=WaveformPulse(5),
        #     speed_divider_bpl=7,
        #     lifetime_l=800,
        # ),
        # Pulse(
        #     strip_length_l=np.n,
        #     color_rgb256=(255, 0, 0),  # red
        #     waveform=WaveformPulse(3),
        #     speed_divider_bpl=2,
        #     lifetime_l=800,
        # ),
# >>>>>>> 63a3556 (.)
    ]


class PulseGenerator:
    def __init__(self, np):
        self._np = np
        self._waveform_long_01 = WaveformLong(1*96)
        self._waveform_long_02 = WaveformLong(2*96) 
        self._waveform_long_03 = WaveformLong(3*96) 
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
        lifetime_s = random.choice(PREDEFINED_LIFETIMES_S)
        lifetime_l = int(lifetime_s * 1000 / (MIN_TIME_BEAT_MS * speed_divider_bpl)) + DIMM_TIME_L
        print("Lifetime %d s, %d l" % (lifetime_s, lifetime_l))
# <<<<<<< HEAD
        return Pulse(
            strip_length_l=self._np.led_count,
# =======
        pulse = Pulse(
            strip_length_l=self._np.n,
# >>>>>>> 63a3556 (.)
            waveform=WaveformPulse(length_l),
            color_rgb256=random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=speed_divider_bpl,
            #lifetime_l=random.choice(PREDEFINED_LIFETIMES_L) + DIMM_TIME_L,
            lifetime_l=lifetime_l,
        )
        pulse.change_startposition_l(int(length_l*0.1))
        return(pulse)

    def get_radar_pulse(self, duration_ms, current_at_limit):
        length_l = 3
        speed_divider_bpl = random.randrange(1, 3)
        lifetime_s = random.randrange(10, 25)
        lifetime_l = int(lifetime_s * 1000 / (MIN_TIME_BEAT_MS * speed_divider_bpl)) + DIMM_TIME_L
        startposition_l = random.randrange(1, self._np.n//3)
        print("Radar pulse: length_l=%d, speed_divider_bpl=%d, lifetime_l=%d, startposition_l=%d" % (length_l, speed_divider_bpl, lifetime_l, startposition_l))
        pulse = Pulse(
            strip_length_l=self._np.n,
            waveform=WaveformPulse(length_l),
            color_rgb256=(0, 255, 0),
            speed_divider_bpl=speed_divider_bpl,
            lifetime_l=lifetime_l,
        )
        pulse.change_startposition_l(startposition_l)
        return(pulse)

    def get_monocolor_wave(self, duration_ms, current_at_limit):
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return Pulse(
# <<<<<<< HEAD
            strip_length_l=self._np.led_count,
            waveform=self._waveform_long,
# =======
            strip_length_l=self._np.n,
            waveform=self._waveform_long_01,
            color_rgb256= (0, 255, 0), #random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=1,
            lifetime_l=3 * self._np.n,
        )

    def get_multicolor_wave(self, duration_ms, current_at_limit):
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return Pulse(
            strip_length_l=self._np.n,
            waveform=self._waveform_long_01,
# >>>>>>> c1474d0 (div)
            color_rgb256= random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=1,
            lifetime_l=5 * self._np.n,
        )

    def get_next_wave_01(self, duration_ms, current_at_limit):
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return Pulse(
            strip_length_l=self._np.n,
            waveform=self._waveform_long_02,
            color_rgb256= random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=1,
            lifetime_l=5 * self._np.n,
        )

    def get_next_wave_02(self, duration_ms, current_at_limit):
        if current_at_limit:
            print("current_at_limit: send killer")
            return create_pulse_killer(self._np)
        return Pulse(
            strip_length_l=self._np.n,
            waveform=self._waveform_long_03,
            color_rgb256= random.choice(PREDEFINED_COLORS_RGB256),
            speed_divider_bpl=1,
            lifetime_l=5 * self._np.n,
        )