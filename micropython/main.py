import os
import gc
import time
import random
import machine
import micropython
# import portable_neopixel as neopixel
# <<<<<<< HEAD
from pulse_generator import PulseGenerator
# =======
# >>>>>>> c1474d0 (div)

from pulse_generator import PulseGenerator, MIN_TIME_BEAT_MS, PREDEFINED_COLORS_RGB256

import ledstrip_rp2 as ledstrip
import rp2_ws2821 as neopixel
PIN_BUTTON = machine.Pin(27)
PIN_LED = machine.Pin(28)
class LED:
    def __init__(self, dummy): pass
    def on(self): pass
    def off(self): pass


micropython.alloc_emergency_exception_buf(100)

if False:
    import performance_test

    performance_test.test()


# print (wave_array)
LED_CURRENT_MAX = 250  # vorsicht: stromverbrauch
COUNTER_MAX = 100

MIN_TIME_BEAT_US = 20000
MIN_TIME_BEAT_US = 1


class Button:
    def __init__(self, pin):
        self.pin = PIN_BUTTON
        self.ticks_us = None
        self._button_pressed_ms = None
        self._pulses = 3

    def get_button_pressed_ms(self):
        """
        return None: If button not pressed
        return duration_ms: if button was pressed
        """
        if self._pulses > 0:
            self._pulses -= 1
            return 600
        duration_ms = self._button_pressed_ms
        self._button_pressed_ms = None
        return duration_ms

    def _callback_button(self, dummy):
        # self.timer.init(period=10, mode=machine.Timer.ONE_SHOT, callback=self.callback_timer)
        ticks_us = timer_us()
        while True:
            duration_us = timer_us() - ticks_us
            if duration_us > 10000:
                break
        unpressed = self.pin.value()
        if unpressed:
            if self.ticks_us is None:
                return
            self._button_pressed_ms = (timer_us() - self.ticks_us) // 1000
            self.ticks_us = None
            return
        self.ticks_us = timer_us()


button = Button(PIN_BUTTON)


MODE_PULSES = 0
MODE_WAVES = 1


class Mode:
    def __init__(self):
        self.led_green = LED(2)
        self.mode = MODE_WAVES
        self.toggle_mode()

    def set(self, mode):
        self.mode = mode
        if self.mode == MODE_WAVES:
            self.led_green.on()
        else:
            self.led_green.off()

    def toggle_mode(self):
        if self.mode == MODE_WAVES:
            self.set(MODE_PULSES)
        else:
            self.set(MODE_WAVES)


mode = Mode()


def init_timer_us():
    # The method `bitstream` disrupts the timer, therefore
    # ticks_ms, ticks_cpu etc. would not work.
    return time.ticks_us


timer_us = init_timer_us()

AUTO_ON = False  # ohne automatik leuchtet es erst auf knopfdruck


led_count = 5 * 96
NEOPIXEL = neopixel.NeoPixel(pin=PIN_LED, led_count=led_count)
LEDSTRIP = ledstrip.Ledstrip(led_count)
LEDSTRIP.clear()


class ListPulses:
    def __init__(self):
        self.pulse_list = []

    def is_empty(self):
        return len(self.pulse_list) == 0

    def append(self, pulse):
        self.pulse_list.append(pulse)

    def led_current(self):
        led_current = 0
        for pulse in self.pulse_list:
            led_current += pulse.led_current
        return led_current

    def current_at_limit(self):
        return self.led_current() > LED_CURRENT_MAX

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

    def show(self):
        if len(self.pulse_list) == 0:
            return

        LEDSTRIP.clear()
        for pulse in self.pulse_list:
            pulse.show(np=NEOPIXEL, ledstrip=LEDSTRIP)
            pulse.interact(self.pulse_list)
        NEOPIXEL.write(ledstrip=LEDSTRIP)

        for pulse in self.pulse_list:
            pulse.do_increment()


class IdleTimeResetter:
    def __init__(self):
        self._last_idle_ticks_us = None

    def time_over(self):
        if self._last_idle_ticks_us is None:
            self._last_idle_ticks_us = timer_us()
            return False

        idle_time_us = timer_us() - self._last_idle_ticks_us
        if idle_time_us > 60 * 1000 * 1000:
            self._last_idle_ticks_us = None
            print("IdleTimeResetter: time_over")
            mode.set(MODE_PULSES)
            return True
        return False


class ShowPulses:
    def __init__(self):
        self.fade_out_trigger = 0
        self.pulse_list = ListPulses()
        self.pulse_generator = PulseGenerator(np=NEOPIXEL)
        self.idle_time_resetter = IdleTimeResetter()
        self._last_time_ms = time.ticks_ms()
        self._last_time_us = timer_us()
        NEOPIXEL.write(ledstrip=LEDSTRIP)

    def calculate_next_beat(self):
        self.fade_out_trigger += 1
        if self.fade_out_trigger % COUNTER_MAX == 0:
            time_us = timer_us()
            duration_ms = time_us - self._last_time_us
            self._last_time_us = timer_us()

            print(
                "%0.2f beats per second, led_current=%d, mem_free=%d"
                % (
                    1000000.0 * COUNTER_MAX / duration_ms,
                    self.pulse_list.led_current(),
                    gc.mem_free(),
                )
            )
            self.pulse_list.end_of_life()
            if self.pulse_list.is_empty():
                if self.idle_time_resetter.time_over():
                    self.pulse_generator.reset()

        duration_ms = button.get_button_pressed_ms()
        if duration_ms is not None:
            print("Button %d ms" % duration_ms)
            if duration_ms > 3000:
                mode.toggle_mode()
                return

            current_at_limit = self.pulse_list.current_at_limit()
            if mode.mode == MODE_PULSES:
                pulse = self.pulse_generator.get_next_pulse(
                    duration_ms, current_at_limit
                )
            else:
                pulse = self.pulse_generator.get_next_wave(
                    duration_ms, current_at_limit
                )
            # print("pulse", pulse._waveform256)
            self.pulse_list.append(pulse)

        if AUTO_ON:
            if random.random() < 0.0001:
                self.pulse_list.append(create_random_pulse())

        self.pulse_list.show()

    def run_forever(self):
        while True:
            time_us = timer_us()

            self.calculate_next_beat()

            slowdown_us = MIN_TIME_BEAT_US + time_us - timer_us()
            if slowdown_us > 0:
                # print("slowdown_us", slowdown_us)
                time.sleep_us(slowdown_us)
                if time_us >= 2147483648:  # 2**31
                    # Reset timer after ~8 minutes
                    timer_us(0)


show_dinger = ShowPulses()
show_dinger.run_forever()

