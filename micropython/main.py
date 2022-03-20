import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
from pyb import Pin, ExtInt


import machine
from neopixel_int import NeoPixel

from portable_pulse import Pulse, DIMM_TIME_L

if False:
    import performance_test

    performance_test.test()


taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

# print (wave_array)
LED_CURRENT_MAX = 50000  # vorsicht: stromverbrauch
COUNTER_MAX = 100

MIN_TIME_BEAT_MS = 1  # 50


class Button:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.ticks_ms = None
        self._button_pressed_ms = None
        ExtInt(
            self.pin,
            ExtInt.IRQ_RISING_FALLING,
            Pin.PULL_UP,
            callback=self._callback_button,
        )

    def get_button_pressed_ms(self):
        """
        return None: If button not pressed
        return duration_ms: if button was pressed
        """
        duration_ms = self._button_pressed_ms
        self._button_pressed_ms = None
        return duration_ms

    def _callback_button(self, dummy):
        # self.timer.init(period=10, mode=machine.Timer.ONE_SHOT, callback=self.callback_timer)
        ticks_ms = time.ticks_ms()
        while True:
            duration_ms = time.ticks_diff(time.ticks_ms(), ticks_ms)
            if duration_ms > 10:
                break
        unpressed = self.pin.value()
        if unpressed:
            if self.ticks_ms is None:
                return
            self._button_pressed_ms = time.ticks_diff(time.ticks_ms(), self.ticks_ms)
            self.ticks_ms = None
            return
        self.ticks_ms = time.ticks_ms()


button = Button("Y1")

AUTO_ON = False  # ohne automatik leuchtet es erst auf knopfdruck


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

NP = NeoPixel(machine.Pin.board.Y12, n=5 * 96)


def create_random_pulse(duration_ms):
    length_l = random.choice(PREDEFINED_LENGTHS_L)
    # speed_divider_bpl = duration_ms // 200
    # speed_divider_bpl = min(20, max(1, speed_divider_bpl))
    speed_divider_bpl = random.choice(PREDEFINED_SPEED_DIVIDER_BPL)
    pulse = Pulse(
        strip_length_l=NP.n,
        length_l=length_l,
        color_rgb256=random.choice(PREDEFINED_COLORS_RGB256),
        speed_divider_bpl=speed_divider_bpl,
        lifetime_l=random.choice(PREDEFINED_LIFETIMES_L) + DIMM_TIME_L,
        # blink=random.random() < 0.05,
    )
    return pulse


def create_pulse_killer():
    return Pulse(
        strip_length_l=NP.n,
        color_rgb256=(255, 0, 0),  # red
        length_l=3,
        speed_divider_bpl=1,  # 120,
        lifetime_l=800,
        killer=True,
    )


def create_predefined_pulses():
    return [
        Pulse(
            strip_length_l=NP.n,
            color_rgb256=(0, 255, 0),  # gruen
            length_l=10,
            speed_divider_bpl=3,
            lifetime_l=400,
        ),
        Pulse(
            strip_length_l=NP.n,
            color_rgb256=(0, 0, 255),  # blau
            length_l=5,
            speed_divider_bpl=7,
            lifetime_l=1500,
        ),
        Pulse(
            strip_length_l=NP.n,
            color_rgb256=(255, 0, 0),  # red
            length_l=3,
            speed_divider_bpl=2,
            lifetime_l=800,
        ),
        Pulse(
            strip_length_l=NP.n,
            color_rgb256=(255, 255, 0),  # yellow
            length_l=20,
            speed_divider_bpl=6,
            lifetime_l=1200,
        ),
    ]


class PulseGenerator:
    def __init__(self):
        self.reset()

    def reset(self):
        self._queue = create_predefined_pulses()

    def get_next_pulse(self, duration_ms):
        if len(self._queue) > 0:
            return self._queue.pop(0)
        return create_random_pulse(duration_ms)


class ListPulses:
    def __init__(self):
        self.pulse_list = []

    def is_empty(self):
        return len(self.pulse_list) == 0

    def append(self, pulse):
        self.pulse_list.append(pulse)

    def _led_current(self):
        led_current = 0
        for pulse in self.pulse_list:
            led_current += pulse.led_current
        return led_current

    def current_at_limit(self):
        return self._led_current() > LED_CURRENT_MAX

    def end_of_life(self):
        def purge_one_pulse():
            for pulse in self.pulse_list:
                if pulse.end_of_life():
                    self.pulse_list.remove(pulse)
                    # We have to leave the loop after manipulating the list
                    print(
                        "pulse end_of_life(): %d remaining active pulses"
                        % len(self.pulse_list)
                    )
                    return True
            return False

        while purge_one_pulse():
            pass

    def show(self, np):
        if len(self.pulse_list) == 0:
            time.sleep_ms(2)
            return

        np.clear(0)
        for pulse in self.pulse_list:
            pulse.show(np)
            pulse.interact(self.pulse_list)
        np.write()

        for pulse in self.pulse_list:
            pulse.do_increment()


class IdleTimeResetter:
    def __init__(self):
        self._last_idle_ticks_ms = None

    def time_over(self):
        if self._last_idle_ticks_ms is None:
            self._last_idle_ticks_ms = time.ticks_ms()
            return False

        idle_time_ms = time.ticks_diff(time.ticks_ms(), self._last_idle_ticks_ms)
        if idle_time_ms > 60 * 1000:
            self._last_idle_ticks_ms = None
            print("IdleTimeResetter: time_over")
            return True
        return False


class ShowPulses:
    def __init__(self):
        self.fade_out_trigger = 0
        self.pulse_list = ListPulses()
        self.pulse_generator = PulseGenerator()
        self.idle_time_resetter = IdleTimeResetter()
        self._last_time_ms = time.ticks_ms()
        NP.write()

    def calculate_next_beat(self):
        self.fade_out_trigger += 1
        if self.fade_out_trigger % COUNTER_MAX == 0:
            time_ms = time.ticks_ms()
            duration_ms = time.ticks_diff(time_ms, self._last_time_ms)
            self._last_time_ms = time_ms
            print("%0.2f beats per second" % (1000.0 * COUNTER_MAX / duration_ms))
            self.pulse_list.end_of_life()
            if self.pulse_list.is_empty():
                if self.idle_time_resetter.time_over():
                    self.pulse_generator.reset()

        duration_ms = button.get_button_pressed_ms()
        if duration_ms is not None:
            print("Button %s ms" % duration_ms)
            if self.pulse_list.current_at_limit():
                print("current_at_limit: send killer")
                pulse = create_pulse_killer()
            else:
                pulse = self.pulse_generator.get_next_pulse(duration_ms)
            self.pulse_list.append(pulse)
        if AUTO_ON:
            if random.random() < 0.0001:
                self.pulse_list.append(create_random_pulse())

        self.pulse_list.show(NP)

    def run_forever(self):
        while True:
            time_ms = time.ticks_ms()

            self.calculate_next_beat()

            slowdown_ms = MIN_TIME_BEAT_MS - time.ticks_diff(time.ticks_ms(), time_ms)
            if slowdown_ms > 0:
                print("slowdown_ms", slowdown_ms)
                time.sleep_ms(slowdown_ms)


show_dinger = ShowPulses()
show_dinger.run_forever()
