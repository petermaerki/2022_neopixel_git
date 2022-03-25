import portable_pulse

if __name__ == "__main__":
    waveform = portable_pulse.WaveformLong(length_l=128)
    print(waveform.buf)
