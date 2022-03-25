import ledstrip


from builtins import bytearray

b = bytearray(20*b'\0')
first_led = 2
factor = 70
color = (255, 0, 0)
waveform = (12, 40, 128, 256, 64)
#                   1    2    3
waveform_pos_begin_b = 2
speed_bpl = 1
ledstrip.pulse(b, first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
print("bytearray")
print([v for v in b])
print("[0, 0, 0, 0, 0, 0, 0, 34, 0, 0, 69, 0, 0, 17, 0, 0, 0, 0, 0, 0] expected")


# The same but with int16
first_led = 0
factor = 255
color = (255, 0, 0)
waveform = (256,)
waveform_pos_begin_b = 0
speed_bpl = 1

ledstrip.int_clear(None, None)
ledstrip.int_pulse(None, first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
b = bytearray(6*b'\0')
ledstrip.int_copy(b)
print("int_pulse 1")
print([v for v in b])
print("[0, 254, 0, 0, 0, 0] expected")

color = (0, 255, 0)
waveform = (-150,)
ledstrip.int_pulse(None, first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
ledstrip.int_copy(b)
print("int_pulse 2")
print([v for v in b])
print("[0, 106, 0, 0, 0, 0] expected")

color = (0, 0, 255)
waveform = (-150,)
ledstrip.int_pulse(None, first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
ledstrip.int_copy(b)
print("int_pulse 3")
print([v for v in b])
print("[0, 0, 0, 0, 0, 0] expected")

print("int_clear")
ledstrip.int_clear(None, None)
ledstrip.int_copy(b)
print([v for v in b])
print("[0, 0, 0, 0, 0, 0] expected")
