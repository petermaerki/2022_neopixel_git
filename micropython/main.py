import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
import math
from machine import Pin


import machine, neopixel  # brauch aktuelles pyboard, es geht mit 1.18

taster = Pin("Y1", Pin.IN, Pin.PULL_UP)
taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

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
        self.increment = increment
        self.position = position
        self.lifetime = lifetime
        self.blink = blink


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


def create_random_pulse():
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


PREDEFINED_PULSES = [
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


class ShowPulses:
    def __init__(self):
        self.np = neopixel.NeoPixel(machine.Pin.board.Y12, n=5 * 96, bpp=3, timing=1)
        self.idle_counter = 1000
        self.counter = 0
        self.button_debounce = 0
        self.blinki = False
        self.pulse_list = []
        self.dinger_liste_fertige = PREDEFINED_PULSES

    @property
    def led_count(self):
        return self.np.n

    def run_forever(self):
        while True:
            self.calculate_next_step()
            # time.sleep(1.0)

    def calculate_next_step(self):
        if len(self.pulse_list) > 0:
            self.np.fill((0, 0, 0))
            for pulse in self.pulse_list:
                start_led = (pulse.position // SUBSTEPS) + 1
                stop_led = start_led + SUBSTEPS // pulse.length_wave_divider
                start_led = max(0, start_led)  # nur positive anzeigen
                stop_led = min(self.led_count, stop_led)
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
                        last_color = self.np[led]
                        red = min(value * pulse.color[0] + last_color[0], 255)
                        green = min(value * pulse.color[1] + last_color[1], 255)
                        blue = min(value * pulse.color[2] + last_color[2], 255)
                        self.np[led] = (red, green, blue)
                    if pulse.blink and self.blinki:
                        self.np[led] = (0, 0, 0)
                pulse.position = pulse.position + pulse.increment
                # print('ding.position % d' % ding.position)
                if (
                    pulse.position > self.led_count * SUBSTEPS and pulse.increment > 0
                ):  # bounce at the end
                    pulse.increment = -pulse.increment
                if (
                    pulse.position < -SUBSTEPS * SUBSTEPS // pulse.length_wave_divider
                    and pulse.increment < 0
                ):  # bounce at the start
                    pulse.increment = -pulse.increment
                # print('ding.position %d' % ding.position)
                pulse.lifetime -= 1
                # print('alter %d' % alter)
            self.np.write()
            self.blinki = not self.blinki
        self.counter += 1
        if self.counter % COUNTER_MAX == 0:
            # print('test auf alte')
            self.counter = 0
            neue_liste = []
            lifetimes = []
            for pulse in self.pulse_list:
                if pulse.lifetime > -DIMM_TIME:
                    neue_liste.append(pulse)
                    lifetimes.append(pulse.lifetime)
                else:
                    print("stirbt, es hat jetzt %d dinger" % (len(self.pulse_list) - 1))
            self.pulse_list = neue_liste
            if len(lifetimes) > 0:
                print("lebensdauer der %d dinger" % len(lifetimes), lifetimes)
        if taster.value() == 0:  # Taster gedrueckt
            # if len(self.dinger_liste) < anzahl_dinger_max: # limitiere die anzahl dinger
            self.button_debounce = 3
        if self.button_debounce > 0:  # debounce
            self.button_debounce -= 1
            if self.button_debounce == 1:
                if len(self.dinger_liste_fertige) > 0:
                    self.pulse_list.append(self.dinger_liste_fertige.pop(0))
                    # print('ding eingefuegt, es hat jetzt %d dinger' % len(self.dinger_liste))
                else:
                    self.pulse_list.append(create_random_pulse())
        if AUTO_ON:
            if random.random() < 0.0001:
                self.pulse_list.append(create_random_pulse())
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
        if len(self.pulse_list) == 0:
            self.idle_counter += 1
            print("idle_counter %d" % self.idle_counter)
            if self.idle_counter > 200:
                self.dinger_liste_fertige = PREDEFINED_PULSES
            time.sleep(0.1)
        else:
            self.idle_counter = 0


show_dinger = ShowPulses()
show_dinger.run_forever()
