import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
import math
from pyb import Pin, ExtInt


import machine, neopixel  # brauch aktuelles pyboard, es geht mit 1.18

taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)


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
DIMM_TIME = 500

# wave_array is an array with integers to max 255/2, colors
SUBSTEPS = 100
PULSE_ARRAY = [0] * SUBSTEPS
for i in range(SUBSTEPS):
    phase = i / SUBSTEPS * 2 * math.pi
    PULSE_ARRAY[i] = int(0.5 * 255.0 * (-math.cos(phase) * 0.5 + 0.5) ** 2)
# print (wave_array)
PULSE_COUNT_MAX = 10  # vorsicht: stromverbrauch
COUNTER_MAX = 100


class Pulse:
    def __init__(
        self, color, length_wave_divider, increment, position, lifetime, blink
    ):
        self.color = color
        self.length_wave_divider = length_wave_divider
        self._increment = increment
        self.position = position
        self.lifetime = lifetime
        self._blink = blink
        self.on = True

    def do_increment(self, led_count):
        if self._blink:
            self.on = not self.on

        self.position = self.position + self._increment
        # print('ding.position % d' % ding.position)
        if (
            self.position > led_count * SUBSTEPS and self._increment > 0
        ):  # bounce at the end
            self._increment = -self._increment
        if (
            self.position < -SUBSTEPS * SUBSTEPS // self.length_wave_divider
            and self._increment < 0
        ):  # bounce at the start
            self._increment = -self._increment
        # print('ding.position %d' % ding.position)
        self.lifetime -= 1
        # print('alter %d' % alter)


PREDEFINED_INCREMENTS = [5, 10, 20, 30, 80, 130, 200, 400, 500]
PREDEFINED_LENGTHS = [50, 30, 20, 10, 5, 2]
PREDEFINED_COLORS = [
    (2, 0, 0),  # red
    (2, 1, 0),  # orange
    (2, 2, 0),  # yellow
    (1, 2, 0),  # giftgruen
    (0, 2, 0),  # gruen
    (0, 2, 1),  # grausiggruen
    (0, 2, 2),  # cyan
    (0, 1, 2),  # komischblau
    (0, 0, 2),  # blau
    (1, 0, 2),  # komischblau 2
    (2, 0, 2),  # magenta
    (2, 0, 1),  # komischpink
    (2, 2, 2),  # weiss
]
PREDEFINED_LIFETIMES = [3000, 4000, 5000, 7000, 15000]


def create_random_pulse(duration_ms):
    length = random.choice(PREDEFINED_LENGTHS)
    length_wave_divider = SUBSTEPS // length
    pulse = Pulse(
        length_wave_divider=length_wave_divider,
        color=random.choice(PREDEFINED_COLORS),
        # increment_auswahl = [3,5,10,20,30,80]
        increment=random.choice(
            PREDEFINED_INCREMENTS
        ),  # beispiel: bei increment = subschritte: 1 led
        # [subschritte// 20]
        position=-(SUBSTEPS // length_wave_divider) * SUBSTEPS,
        lifetime=(random.choice(PREDEFINED_LIFETIMES) + DIMM_TIME),
        blink=random.random() < 0.05,
    )
    return pulse


def create_predefined_pulses():
    return [
        Pulse(
            color=(0, 2, 0),  # gruen
            length_wave_divider=SUBSTEPS // 10,
            increment=3,
            position=-10 * SUBSTEPS,
            lifetime=1000,
            blink=False,
        ),
        Pulse(
            color=(0, 0, 2),  # blau
            length_wave_divider=SUBSTEPS // 5,
            increment=13,
            position=-5 * SUBSTEPS,
            lifetime=1500,
            blink=False,
        ),
        Pulse(
            color=(2, 0, 0),  # red
            length_wave_divider=SUBSTEPS // 3,
            increment=120,
            position=-3 * SUBSTEPS,
            lifetime=2000,
            blink=False,
        ),
        Pulse(
            color=(2, 2, 0),  # yellow
            length_wave_divider=SUBSTEPS // 20,
            increment=70,
            position=-20 * SUBSTEPS,
            lifetime=2000,
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

    def fade_out(self):
        lifetimes = []
        neue_liste = []
        for pulse in self.pulse_list:
            if pulse.lifetime > -DIMM_TIME:
                neue_liste.append(pulse)
                lifetimes.append(pulse.lifetime)
            else:
                print("stirbt, es hat jetzt %d dinger" % (len(self.pulse_list) - 1))
        self.pulse_list = neue_liste
        if len(lifetimes) > 0:
            print("lebensdauer der %d dinger" % len(lifetimes), lifetimes)

    def show(self, np):
        if len(self.pulse_list) == 0:
            return

        led_count = np.n

        np.fill((0, 0, 0))
        for pulse in self.pulse_list:
            start_led = (pulse.position // SUBSTEPS) + 1
            stop_led = start_led + SUBSTEPS // pulse.length_wave_divider
            start_led = max(0, start_led)  # nur positive anzeigen
            stop_led = min(led_count, stop_led)
            for led in range(start_led, stop_led):
                # print('start_led % d, stop_led % s' % (start_led, stop_led))
                wave_array_pos = (led * SUBSTEPS - pulse.position) // (
                    SUBSTEPS // pulse.length_wave_divider
                )  # led - start_led) * ding.length_wave_divider
                # print('ding.position % d start_led % d, wave_array_pos %d'%(ding.position, start_led, wave_array_pos))
                if wave_array_pos < 0 or wave_array_pos > len(PULSE_ARRAY) - 1:
                    # print('wave_array_pos falsch %d' % wave_array_pos)
                    peter = 5
                else:
                    value = PULSE_ARRAY[wave_array_pos]
                    if pulse.lifetime < 0:
                        value = int(
                            value + float(pulse.lifetime) / float(DIMM_TIME) * 127.0
                        )
                        value = max(0, value)
                    last_color = np[led]
                    red = min(value * pulse.color[0] + last_color[0], 255)
                    green = min(value * pulse.color[1] + last_color[1], 255)
                    blue = min(value * pulse.color[2] + last_color[2], 255)
                    np[led] = (red, green, blue)
                if not pulse.on:
                    np[led] = (0, 0, 0)
        np.write()

        for pulse in self.pulse_list:
            pulse.do_increment(led_count)

    def limit_pulses(self):
        too_many_pulses = len(self.pulse_list) - PULSE_COUNT_MAX
        if too_many_pulses > 0:  # zu viele, aeltester sterben lassen
            for i in range(too_many_pulses):
                if self.pulse_list[i].lifetime > 0:
                    self.pulse_list[i].lifetime = 0
                    print(
                        "reduziere lebensdauer da %d zuviele dinger" % too_many_pulses
                    )
            if too_many_pulses > 4:
                del self.pulse_list[0]
                print("geloescht da %d zuviele dinger" % too_many_pulses)


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
        self.np = neopixel.NeoPixel(machine.Pin.board.Y12, n=5 * 96, bpp=3, timing=1)
        self.idle_counter = 1000
        self.fade_out_trigger = 0
        self.blinki = False
        self.pulse_list = ListPulses()
        self.pulse_generator = PulseGenerator()
        self.idle_time_resetter = IdleTimeResetter()

    def run_forever(self):
        while True:
            self.calculate_next_step()
            # time.sleep(1.0)

    def calculate_next_step(self):
        self.pulse_list.show(self.np)
        self.fade_out_trigger += 1
        if self.fade_out_trigger % COUNTER_MAX == 0:
            self.pulse_list.fade_out()
        duration_ms = button.get_button_pressed_ms()
        if duration_ms is not None:  # Taster gedrueckt
            print("Button %s ms" % duration_ms)
            pulse = self.pulse_generator.get_next_pulse(duration_ms)
            self.pulse_list.append(pulse)
        if AUTO_ON:
            if random.random() < 0.0001:
                self.pulse_list.append(create_random_pulse())
        self.pulse_list.limit_pulses()

        if self.pulse_list.is_empty():
            if self.idle_time_resetter.time_over():
                self.pulse_generator.reset()


show_dinger = ShowPulses()
show_dinger.run_forever()
