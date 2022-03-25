import gc
import time
import random
from pyb import Pin, ExtInt, Timer, LED
import machine
import micropython
import portable_neopixel as neopixel
from pulse_generator import PulseGenerator

micropython.alloc_emergency_exception_buf(100)

if False:
    import performance_test

    performance_test.test()

taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

# print (wave_array)
LED_CURRENT_MAX = 250  # vorsicht: stromverbrauch
COUNTER_MAX = 100

MIN_TIME_BEAT_US = 20000


class Button:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.ticks_us = None
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


button = Button("Y1")


MODE_PULSES = 0
MODE_WAVES = 1


class Mode:
    def __init__(self):
        self.led_green = LED(2)
        self.mode = MODE_PULSES
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
    cpu_freq_Hz = 168000000
    freq_timer_Hz = 1000000
    prescaler = int((cpu_freq_Hz / (2 * freq_timer_Hz)) - 1)
    timer_us = Timer(2, prescaler=prescaler, period=0x3FFFFFFF)
    timer_us.counter(0)
    return timer_us.counter


timer_us = init_timer_us()

AUTO_ON = False  # ohne automatik leuchtet es erst auf knopfdruck


NP = neopixel.NeoPixel(machine.Pin.board.Y12, n=5 * 96)


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

    def show(self, np):
        if len(self.pulse_list) == 0:
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
        self.pulse_generator = PulseGenerator(np=NP)
        self.idle_time_resetter = IdleTimeResetter()
        self._last_time_ms = time.ticks_ms()
        self._last_time_us = timer_us()
        NP.write()

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

        self.pulse_list.show(NP)

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
