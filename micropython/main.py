import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
import math
from machine import Pin


import machine, neopixel  # brauch aktuelles pyboard, es geht mit 1.18

radar = Pin("X7", Pin.IN, Pin.PULL_DOWN)

taster = Pin("Y1", Pin.IN, Pin.PULL_UP)
taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

AUTOMATISCH_LEUCHTE = False  # ohne automatik leuchtet es erst auf knopfdruck


ABDUNKELPHASE = 500

# wave_array is an array with integers to max 255/2, colors
SUBSCHRITTE = 100
WAVE_ARRAY = [0] * SUBSCHRITTE
for i in range(SUBSCHRITTE):
    phase = i / SUBSCHRITTE * 2 * math.pi
    WAVE_ARRAY[i] = int(0.5 * 255.0 * (-math.cos(phase) * 0.5 + 0.5) ** 2)
# print (wave_array)
ANZAHL_DINGER_MAX = 10  # vorsicht: stromverbrauch

COUNTER_MAX = 100


class Ding:
    def __init__(
        self, farbe, length_wave_divider, increment, position, lebensdauer, blink
    ):
        self.farbe = farbe
        self.length_wave_divider = length_wave_divider
        self.increment = increment
        self.position = position
        self.lebensdauer = lebensdauer
        self.blink = blink


def zufallsding():
    colors = [
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
    increment_auswahl = [5, 10, 20, 30, 80, 130, 200, 400, 500]
    laenge = random.choice([50, 30, 20, 10, 5, 2])
    length_wave_divider = SUBSCHRITTE // laenge
    ding = Ding(
        length_wave_divider=length_wave_divider,
        farbe=random.choice(colors),
        # increment_auswahl = [3,5,10,20,30,80]
        increment=random.choice(
            increment_auswahl
        ),  # beispiel: bei increment = subschritte: 1 led
        # [subschritte// 20]
        position=-(SUBSCHRITTE // length_wave_divider) * SUBSCHRITTE,
        lebensdauer=(random.choice([3000, 4000, 5000, 7000, 15000]) + ABDUNKELPHASE),
        blink=random.random() < 0.05,
    )
    return ding


dinger_liste_fertige_fix = [
    Ding(
        farbe=(0, 2, 0),  # gruen
        length_wave_divider=SUBSCHRITTE // 10,
        increment=3,
        position=-10 * SUBSCHRITTE,
        lebensdauer=1000,
        blink=False,
    ),
    Ding(
        farbe=(0, 0, 2),  # blau
        length_wave_divider=SUBSCHRITTE // 5,
        increment=13,
        position=-5 * SUBSCHRITTE,
        lebensdauer=1500,
        blink=False,
    ),
    Ding(
        farbe=(2, 0, 0),  # red
        length_wave_divider=SUBSCHRITTE // 3,
        increment=120,
        position=-3 * SUBSCHRITTE,
        lebensdauer=2000,
        blink=False,
    ),
    Ding(
        farbe=(2, 2, 0),  # yellow
        length_wave_divider=SUBSCHRITTE // 20,
        increment=70,
        position=-20 * SUBSCHRITTE,
        lebensdauer=2000,
        blink=False,
    ),
]


class ShowDinger:
    def __init__(self):
        self.np = neopixel.NeoPixel(machine.Pin.board.Y12, n=5 * 96, bpp=3, timing=1)
        self.idle_counter = 1000
        self.counter = 0
        self.ding_einfuegen = 0
        self.blinki = False
        self.dinger_liste = []
        self.dinger_liste_fertige = dinger_liste_fertige_fix

    @property
    def leds(self):
        return self.np.n

    def run_forever(self):
        while True:
            self.show_dinger()
            # time.sleep(1.0)

    def show_dinger(self):
        if len(self.dinger_liste) > 0:
            self.np.fill((0, 0, 0))
            for ding in self.dinger_liste:
                start_led = (ding.position // SUBSCHRITTE) + 1
                stop_led = start_led + SUBSCHRITTE // ding.length_wave_divider
                start_led = max(0, start_led)  # nur positive anzeigen
                stop_led = min(self.leds, stop_led)
                for led in range(start_led, stop_led):
                    # print('start_led % d, stop_led % s' % (start_led, stop_led))
                    wave_array_pos = (led * SUBSCHRITTE - ding.position) // (
                        SUBSCHRITTE // ding.length_wave_divider
                    )  # led - start_led) * ding.length_wave_divider
                    # print('ding.position % d start_led % d, wave_array_pos %d'%(ding.position, start_led, wave_array_pos))
                    if wave_array_pos < 0 or wave_array_pos > len(WAVE_ARRAY) - 1:
                        # print('wave_array_pos falsch %d' % wave_array_pos)
                        peter = 5
                    else:
                        value = WAVE_ARRAY[wave_array_pos]
                        if ding.lebensdauer < 0:
                            value = int(
                                value
                                + float(ding.lebensdauer) / float(ABDUNKELPHASE) * 127.0
                            )
                            value = max(0, value)
                        vorher = self.np[led]
                        farbe0 = min(value * ding.farbe[0] + vorher[0], 255)
                        farbe1 = min(value * ding.farbe[1] + vorher[1], 255)
                        farbe2 = min(value * ding.farbe[2] + vorher[2], 255)
                        self.np[led] = (farbe0, farbe1, farbe2)
                    if ding.blink and self.blinki:
                        self.np[led] = (0, 0, 0)
                ding.position = ding.position + ding.increment
                # print('ding.position % d' % ding.position)
                if (
                    ding.position > self.leds * SUBSCHRITTE and ding.increment > 0
                ):  # bounce at the end
                    ding.increment = -ding.increment
                if (
                    ding.position
                    < -SUBSCHRITTE * SUBSCHRITTE // ding.length_wave_divider
                    and ding.increment < 0
                ):  # bounce at the start
                    ding.increment = -ding.increment
                # print('ding.position %d' % ding.position)
                ding.lebensdauer -= 1
                # print('alter %d' % alter)
            self.np.write()
            self.blinki = not self.blinki
        self.counter += 1
        if self.counter % COUNTER_MAX == 0:
            # print('test auf alte')
            self.counter = 0
            neue_liste = []
            lebensdauern = []
            for ding in self.dinger_liste:
                if ding.lebensdauer > -ABDUNKELPHASE:
                    neue_liste.append(ding)
                    lebensdauern.append(ding.lebensdauer)
                else:
                    print(
                        "stirbt, es hat jetzt %d dinger" % (len(self.dinger_liste) - 1)
                    )
            self.dinger_liste = neue_liste
            if len(lebensdauern) > 0:
                print("lebensdauer der %d dinger" % len(lebensdauern), lebensdauern)
        if taster.value() == 0:  # Taster gedrueckt
            # if len(self.dinger_liste) < anzahl_dinger_max: # limitiere die anzahl dinger
            self.ding_einfuegen = 3
        if self.ding_einfuegen > 0:  # debounce
            self.ding_einfuegen -= 1
            if self.ding_einfuegen == 1:
                if len(self.dinger_liste_fertige) > 0:
                    self.dinger_liste.append(self.dinger_liste_fertige.pop(0))
                    # print('ding eingefuegt, es hat jetzt %d dinger' % len(self.dinger_liste))
                else:
                    self.dinger_liste.append(zufallsding())
        if AUTOMATISCH_LEUCHTE:
            if random.random() < 0.0001:
                self.dinger_liste.append(zufallsding())
        zuviele_dinger = len(self.dinger_liste) - ANZAHL_DINGER_MAX
        if zuviele_dinger > 0:  # zu viele, aeltester sterben lassen
            for i in range(zuviele_dinger):
                if self.dinger_liste[i].lebensdauer > 0:
                    self.dinger_liste[i].lebensdauer = 0
                    print("reduziere lebensdauer da %d zuviele dinger" % zuviele_dinger)
            if zuviele_dinger > 4:
                del self.dinger_liste[0]
                print("geloescht da %d zuviele dinger" % zuviele_dinger)
        if len(self.dinger_liste) == 0:
            self.idle_counter += 1
            print("idle_counter %d" % self.idle_counter)
            if self.idle_counter > 200:
                self.dinger_liste_fertige = dinger_liste_fertige_fix
            time.sleep(0.1)
        else:
            self.idle_counter = 0


show_dinger = ShowDinger()
show_dinger.run_forever()
