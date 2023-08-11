# Example based on pio_ws2812.py, but modified to use
# a DMA channel to push out the data to the PIO

# https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf
# https://raspberrypi.github.io/pico-sdk-doxygen/weblinks_page.html
# https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
# https://github.com/raspberrypi/pico-examples/tree/master/pio/ws2812


import array, time
from machine import Pin
from machine import Timer
import rp2
import uctypes
import rp2_dma as dma

PIO0_BASE = 0x50200000
PIO0_BASE_TXF0 = PIO0_BASE+0x10


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=8,
)
def ws2812():
    # fmt: off
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
    # fmt: on


# Create the StateMachine with the ws2812 program, outputting on Pin(2).
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(28))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)

# starts the transfer, using DMA channel 0
def dma_out(data, bytes_count):
    dma.init_channels()
    d0=dma.CHANNELS[0]
    d0.CTRL_TRIG_RAW = 0
    d0.AL1_CTRL = 0

    d0.TRANS_COUNT = bytes_count
    d0.READ_ADDR = uctypes.addressof(data)
    d0.WRITE_ADDR = PIO0_BASE_TXF0

    d0.CTRL_TRIG.INCR_READ = 1
    d0.CTRL_TRIG.INCR_WRITE = 0
    d0.CTRL_TRIG.DATA_SIZE = 0  # 0x0 → SIZE_BYTE
    d0.CTRL_TRIG.HIGH_PRIO = 1
    d0.CTRL_TRIG.EN = 1

if False:
    if True:
        d0=dma.CHANNELS[0]
        while d0.TRANS_COUNT > 0:
            print("TRANS_COUNT: 0x%04x" % d0.TRANS_COUNT)

    tim = Timer(period=25, mode=Timer.PERIODIC, callback=lambda t:dma_out())


class NeoPixel:
    def __init__(self, pin, led_count):
        # self.pin = pin
        self.led_count = led_count
        self.bytes_count = 3 * led_count
        self.buf = bytearray(self.bytes_count)
        # self.pin.init(pin.OUT)
        self.tim = Timer(period=25, mode=Timer.PERIODIC, callback=lambda t:dma_out(self.buf, self.bytes_count))

    def write(self, ledstrip):
        ledstrip.copy(self.buf)
        # bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)
