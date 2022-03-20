import micropython

micropython.alloc_emergency_exception_buf(100)
import time
import random
from pyb import Pin, ExtInt


import machine
from neopixel_int import NeoPixel

from pulse_generator import PulseGenerator

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


NP = NeoPixel(machine.Pin.board.Y12, n=5 * 96)




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
        self.pulse_generator = PulseGenerator(np=NP)
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
            current_at_limit = self.pulse_list.current_at_limit()
            pulse = self.pulse_generator.get_next_pulse(duration_ms, current_at_limit)
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
