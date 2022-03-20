import ledstrip


from builtins import bytearray
b = bytearray(b'abcdef')
print(b)
ledstrip.clear(b, ord('x'))
print(b)

b = bytearray(20*b'\0')
first_led = 2
factor = 70
color = (10, 100, 10)
waveform = (12, 40, 256, 200, 128, 50, 64)
#                   1          2       3
waveform_pos_begin_b = 2
speed_bpl = 2
ledstrip.pulse(b, first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
print([b for b in b])

