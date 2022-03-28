import gc
import time
import random
from pyb import Pin, ExtInt, Timer, LED
import machine
import micropython
import portable_neopixel as neopixel

from pulse_generator import PulseGenerator, MIN_TIME_BEAT_MS
micropython.alloc_emergency_exception_buf(100)

if False:
    import performance_test

    performance_test.test()

taster_gnd = Pin("Y2", Pin.OUT)
taster_gnd.value(0)

# print (wave_array)
LED_CURRENT_MAX = 750  # vorsicht: stromverbrauch
COUNTER_MAX = 50

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
        ticks_ms = timer_ms.get()
        while True:
            duration_ms = timer_ms.get() - ticks_ms
            if duration_ms > 10:
                break
        unpressed = self.pin.value()
        if unpressed:
            if self.ticks_ms is None:
                return
            self._button_pressed_ms = (timer_ms.get() - self.ticks_ms)
            self.ticks_ms = None
            return
        self.ticks_ms = timer_ms.get()


button = Button("Y1")


MODE_PULSES = 0
MODE_MONOCOLOR_WAVES = 1
MODE_MULTICOLOR_WAVES = 2
MODE_UNDEFINED_01 = 3
MODE_UNDEFINED_02 = 4
MODES = 5

class timer_ms():
    def __init__(self):
        # The method `bitstream` disrupts the timer, therefore
        # ticks_ms, ticks_cpu etc. would not work.
        cpu_freq_Hz = 168000000
        freq_timer_Hz = 2000
        prescaler = int((cpu_freq_Hz / (2 * freq_timer_Hz)) - 1)
        self.timer_ms = Timer(2, prescaler=prescaler, period=0x3FFFFFFF)
        self.timer_ms.counter(0)
    def get(self):
        return self.timer_ms.counter() // 2
    def check_overflow(self):
        if self.timer_ms.counter() >= 2147483648: # 2**31
            # Avoid timer overflow after about 12 days
            print("machine.reset() to avoid timer overflow")
            time.sleep(1.0)
            machine.reset()

timer_ms = timer_ms()

class Mode:
    def __init__(self):
        self.led_red = LED(1)
        self.led_green = LED(2)
        self.led_yellow = LED(3)
        self.led_blue = LED(4)
        self.reset()

    def set(self, mode):
        self.mode = mode
        self.led_red.off()
        self.led_green.off()
        self.led_yellow.off()
        self.led_blue.off()
        if self.mode == MODE_MONOCOLOR_WAVES:
            self.led_green.on()
        if self.mode == MODE_MULTICOLOR_WAVES:
            self.led_yellow.on()
        if self.mode == MODE_UNDEFINED_01:
            self.led_blue.on()
        if self.mode == MODE_UNDEFINED_02:
            self.led_red.on()
        print("Mode: %s" % self.mode)

    def next_mode(self):
        self.set((self.mode + 1) % MODES)

    def button_next_mode(self):
        self.auto_mode_change = False
        self.next_mode()

    def check_auto_mode(self):
        if self.auto_mode_change:
            change_every_ms = 30000
            if self.next_auto_mode_change_ms == None:
                self.next_auto_mode_change_ms = timer_ms.get() + change_every_ms
            if timer_ms.get() > self.next_auto_mode_change_ms:
                self.next_auto_mode_change_ms = timer_ms.get() + change_every_ms
                self.set((self.mode + 1) % MODES)
                print(self.next_auto_mode_change_ms)

    def reset(self):
        self.set(MODE_PULSES)
        self.next_auto_mode_change_ms = None
        self.auto_mode_change = True
        print("mode.reset() done")

mode = Mode()

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
        self._last_idle_ticks_ms = None

    def time_over(self):
        if self._last_idle_ticks_ms is None:
            self._last_idle_ticks_ms = timer_ms.get()
            return False

        idle_time_ms = timer_ms.get() - self._last_idle_ticks_ms
        if idle_time_ms > 60 * 1000:
            self._last_idle_ticks_ms = None
            print("IdleTimeResetter: time_over")
            mode.reset()
            return True
        return False


class ShowPulses:
    def __init__(self):
        self.fade_out_trigger = 0
        self.pulse_list = ListPulses()
        self.pulse_generator = PulseGenerator(np=NP)
        self.idle_time_resetter = IdleTimeResetter()
        self._last_time_ms = time.ticks_ms()
        self._last_time_ms = timer_ms.get()
        NP.write()

    def calculate_next_beat(self):
        self.fade_out_trigger += 1
        if self.fade_out_trigger % COUNTER_MAX == 0:
            time_ms = timer_ms.get()
            duration_ms = time_ms - self._last_time_ms
            self._last_time_ms = timer_ms.get()

            print(
                "%0.0f beats per second, led_current=%d, mem_free=%d"
                % (
                    1000.0 * COUNTER_MAX / duration_ms,
                    self.pulse_list.led_current(),
                    gc.mem_free(),
                )
            )
            self.pulse_list.end_of_life()
            if self.pulse_list.is_empty():
                if self.idle_time_resetter.time_over():
                    self.pulse_generator.reset()
            else:
                mode.check_auto_mode()

        duration_ms = button.get_button_pressed_ms()
        if duration_ms is not None:
            print("Button %d ms" % duration_ms)
            if duration_ms > 3000:
                mode.button_next_mode()
                return

            current_at_limit = self.pulse_list.current_at_limit()
            if mode.mode == MODE_PULSES:
                pulse = self.pulse_generator.get_next_pulse(
                    duration_ms, current_at_limit
                )
            if mode.mode == MODE_MONOCOLOR_WAVES:
                pulse = self.pulse_generator.get_monocolor_wave(
                    duration_ms, current_at_limit
                )
            if mode.mode == MODE_MULTICOLOR_WAVES:
                pulse = self.pulse_generator.get_multicolor_wave(
                    duration_ms, current_at_limit
                )
            if mode.mode == MODE_UNDEFINED_01:
                pulse = self.pulse_generator.get_next_wave_01(
                    duration_ms, current_at_limit
                )
            if mode.mode == MODE_UNDEFINED_02:
                pulse = self.pulse_generator.get_next_wave_02(
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
            time_ms = timer_ms.get()

            self.calculate_next_beat()

            slowdown_ms = MIN_TIME_BEAT_MS + time_ms - timer_ms.get()
            if slowdown_ms > 0:
                # print("slowdown_ms", slowdown_ms)
                time.sleep_ms(slowdown_ms)
                timer_ms.check_overflow()



show_dinger = ShowPulses()
show_dinger.run_forever()
