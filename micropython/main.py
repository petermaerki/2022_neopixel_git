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
LED_CURRENT_MAX = 1200  # vorsicht: stromverbrauch
COUNTER_MAX = 100


class Pulse:
    def __init__(self, color, led_length, increment, lifetime, blink):
        self._color = color
        self._on = True
        # Speed
        self._lifetime = lifetime
        self._blink = blink
        self._led_length = led_length
        self._increment_substeps = increment
        self._position_substeps = -SUBSTEPS * led_length
        self.led_current = self._led_length * sum(self._color)

    def end_of_life(self):
        return self._lifetime < -DIMM_TIME

    def do_increment(self, led_count):
        if self._blink:
            self._on = not self._on

        self._lifetime -= 1
        self._position_substeps = self._position_substeps + self._increment_substeps

        if self._increment_substeps > 0:
            # Forward
            if self._position_substeps > SUBSTEPS * led_count:
                # bounce at the end
                self._increment_substeps = -self._increment_substeps
        else:
            # Backward
            if self._position_substeps < -SUBSTEPS * self._led_length:
                # bounce at the start
                self._increment_substeps = -self._increment_substeps

    def show(self, np, led_count):
        start_led = (self._position_substeps // SUBSTEPS) + 1
        stop_led = start_led + self._led_length
        start_led = max(0, start_led)  # nur positive anzeigen
        stop_led = min(led_count, stop_led)
        for led in range(start_led, stop_led):
            # print('start_led % d, stop_led % s' % (start_led, stop_led))
            wave_array_pos = (led * SUBSTEPS - self._position_substeps) // (
                self._led_length
            )  # led - start_led) * ding.length_wave_divider
            # print('ding.position % d start_led % d, wave_array_pos %d'%(ding.position, start_led, wave_array_pos))
            if wave_array_pos < 0 or wave_array_pos > len(PULSE_ARRAY) - 1:
                # print('wave_array_pos falsch %d' % wave_array_pos)
                peter = 5
            else:
                value = PULSE_ARRAY[wave_array_pos]
                if self._lifetime < 0:
                    value = int(
                        value + float(self._lifetime) / float(DIMM_TIME) * 127.0
                    )
                    value = max(0, value)
                last_color = np[led]
                red = min(value * self._color[0] + last_color[0], 255)
                green = min(value * self._color[1] + last_color[1], 255)
                blue = min(value * self._color[2] + last_color[2], 255)
                np[led] = (red, green, blue)
            if not self._on:
                np[led] = (0, 0, 0)


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
    led_length = random.choice(PREDEFINED_LENGTHS)
    pulse = Pulse(
        led_length=led_length,
        color=random.choice(PREDEFINED_COLORS),
        # increment_auswahl = [3,5,10,20,30,80]
        increment=random.choice(
            PREDEFINED_INCREMENTS
        ),  # beispiel: bei increment = subschritte: 1 led
        # [subschritte// 20]
        lifetime=(random.choice(PREDEFINED_LIFETIMES) + DIMM_TIME),
        blink=random.random() < 0.05,
    )
    return pulse


def create_predefined_pulses():
    return [
        Pulse(
            color=(0, 2, 0),  # gruen
            led_length=10,
            increment=3,
            lifetime=1000,
            blink=False,
        ),
        Pulse(
            color=(0, 0, 2),  # blau
            led_length=5,
            increment=13,
            lifetime=1500,
            blink=False,
        ),
        Pulse(
            color=(2, 0, 0),  # red
            led_length=3,
            increment=120,
            lifetime=2000,
            blink=False,
        ),
        Pulse(
            color=(2, 2, 0),  # yellow
            led_length=20,
            increment=70,
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
            return

        led_count = np.n

        np.fill((0, 0, 0))
        for pulse in self.pulse_list:
            pulse.show(np, led_count)
        np.write()

        for pulse in self.pulse_list:
            pulse.do_increment(led_count)


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
        self.np = neopixel.NeoPixel(machine.Pin.board.Y12, n=5 * 96, bpp=3, timing=1)
        self.pulse_list = ListPulses()
        self.pulse_generator = PulseGenerator()
        self.idle_time_resetter = IdleTimeResetter()
        self.np.write()

    def calculate_next_step(self):
        self.fade_out_trigger += 1
        if self.fade_out_trigger % COUNTER_MAX == 0:
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

        self.pulse_list.show(self.np)

    def run_forever(self):
        while True:
            self.calculate_next_step()


show_dinger = ShowPulses()
show_dinger.run_forever()
