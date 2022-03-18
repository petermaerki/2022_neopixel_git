# 2022_neopixel_git
Micropython and Neopixel experiments

## Interesting links

LED stipe used:
https://www.aliexpress.com/item/4001247224166.html?spm=a2g0o.order_list.0.0.21ef18028dd1yn

bei dir ist:
 * black pcb
 * 96leds ip67
 * 5m
 * USD 18.3
 * WS2812B

https://www.derunledlights.com/the-difference-between-addressable-rgb-led-strip-ws2811-ws2812b-ws2813-ws2815-sk6812-sk9822/
https://www.stripsledlight.com/what-different-of-apa102sk9822hd107sws2812b-sk6812ws2811ws2815ws2813/

https://youtu.be/QnvircC22hU
https://github.com/thehookup/Holiday_LEDs_2.0/blob/master/Quick%20Reference%20Sheet.pdf

## Enhance implementation

remove 'value'
create 3 curves for r, g, b
use only 5 bits and do not test for max.
