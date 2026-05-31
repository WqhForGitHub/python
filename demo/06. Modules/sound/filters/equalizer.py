def equalizer_filter(sound, frequency, gain):
    """Apply an equalizer filter."""
    print(f"Applying equalizer: freq={frequency}Hz, gain={gain}dB")
    return f"equalize({sound})"
