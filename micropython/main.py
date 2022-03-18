import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
from pyb import Pin, ExtInt


import machine
from neopixel_int import NeoPixel

from portable_pulse import Pulse, DIMM_TIME

if False:
    import performance_test

    performance_test.test()


taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

# print (wave_array)
LED_CURRENT_MAX = 1200  # vorsicht: stromverbrauch
COUNTER_MAX = 100


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


PREDEFINED_SPEED_BPL = [5, 10, 20, 30, 80, 130, 200, 400, 500]
PREDEFINED_LENGTHS_L = [50, 30, 20, 10, 5, 2]
PREDEFINED_COLORS_GRB = [
    (0, 2, 0),  # red
    (1, 2, 0),  # orange
    (2, 2, 0),  # yellow
    (2, 1, 0),  # giftgruen
    (2, 0, 0),  # gruen
    (2, 0, 1),  # grausiggruen
    (2, 0, 2),  # cyan
    (1, 0, 2),  # komischblau
    (0, 0, 2),  # blau
    (0, 1, 2),  # komischblau 2
    (0, 2, 2),  # magenta
    (0, 2, 1),  # komischpink
    (2, 2, 2),  # weiss
]
PREDEFINED_LIFETIMES = [3000, 4000, 5000, 7000, 15000]

NP = NeoPixel(machine.Pin.board.Y12, n=5 * 96)


def create_random_pulse(duration_ms):
    length_l = random.choice(PREDEFINED_LENGTHS_L)
    speed_bpl = duration_ms // 200
    speed_bpl = min(20, max(1, speed_bpl))
    pulse = Pulse(
        strip_length_l=NP.n,
        length_l=length_l,
        color=random.choice(PREDEFINED_COLORS_GRB),
        # increment_auswahl = [3,5,10,20,30,80]
        # speed_bpl=random.choice(
        #     PREDEFINED_SPEED_BPL
        # ),  # beispiel: bei increment = subschritte: 1 led
        # [subschritte// 20]
        speed_bpl=speed_bpl,
        lifetime_b=random.choice(PREDEFINED_LIFETIMES) + DIMM_TIME,
        blink=random.random() < 0.05,
    )
    return pulse


def create_predefined_pulses():
    return [
        Pulse(
            strip_length_l=NP.n,
            color=(0, 2, 0),  # gruen
            length_l=10,
            speed_bpl=3,
            lifetime_b=1000,
            blink=False,
        ),
        Pulse(
            strip_length_l=NP.n,
            color=(0, 0, 2),  # blau
            length_l=5,
            speed_bpl=7,
            lifetime_b=1500,
            blink=False,
        ),
        Pulse(
            strip_length_l=NP.n,
            color=(2, 0, 0),  # red
            length_l=3,
            speed_bpl=1,  # 120,
            lifetime_b=2000,
            blink=False,
        ),
        Pulse(
            strip_length_l=NP.n,
            color=(2, 2, 0),  # yellow
            length_l=20,
            speed_bpl=6,
            lifetime_b=2000,
            blink=False,
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
        self._limit_pulses()

    def _led_current(self):
        led_current = 0
        for pulse in self.pulse_list:
            led_current += pulse.led_current
        return led_current

    def _limit_pulses(self):
        if self._led_current() > LED_CURRENT_MAX:
            del self.pulse_list[0]
            print("limit_pulses() to %d" % LED_CURRENT_MAX)

    def end_of_life(self):
        for pulse in self.pulse_list:
            if pulse.end_of_life():
                self.pulse_list.remove(pulse)
                # We have to leave the loop after manipulating the list
                print(
                    "pulse end_of_life(): %d remaining active pulses"
                    % len(self.pulse_list)
                )
                return

    def show(self, np):
        if len(self.pulse_list) == 0:
            time.sleep_ms(2)
            return

        np.clear(0)
        for pulse in self.pulse_list:
            pulse.show(np)
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

    def calculate_next_step(self):
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
            pulse = self.pulse_generator.get_next_pulse(duration_ms)
            self.pulse_list.append(pulse)
        if AUTO_ON:
            if random.random() < 0.0001:
                self.pulse_list.append(create_random_pulse())

        self.pulse_list.show(NP)

    def run_forever(self):
        while True:
            self.calculate_next_step()


show_dinger = ShowPulses()
show_dinger.run_forever()
