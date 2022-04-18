import ledstrip


from builtins import bytearray

l = ledstrip.Ledstrip(1004)


# The same but with int16
first_led = 0
factor = 255
color = (255, 0, 0)
waveform = (256,)
waveform_pos_begin_b = 0
speed_bpl = 1

l.clear()
l.pulse(first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
b = bytearray(6*b'\0')
l.copy(b)
print("l.pulse 1")
print([v for v in b])
print("[0, 254, 0, 0, 0, 0] expected")

color = (0, 255, 0)
waveform = (-150,)
l.pulse(first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
l.copy(b)
print("l.pulse 2")
print([v for v in b])
print("[0, 106, 0, 0, 0, 0] expected")

color = (0, 0, 255)
waveform = (-150,)
l.pulse(first_led, factor, color, waveform, waveform_pos_begin_b, speed_bpl)
l.copy(b)
print("l.pulse 3")
print([v for v in b])
print("[0, 0, 0, 0, 0, 0] expected")

print("l.clear")
l.clear()
l.copy(b)
print([v for v in b])
print("[0, 0, 0, 0, 0, 0] expected")

