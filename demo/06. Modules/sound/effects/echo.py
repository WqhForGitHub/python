def echo_filter(sound, delay=0.5, decay=0.7):
    """Apply an echo effect to a sound."""
    print(f"Applying echo effect: delay={delay}s, decay={decay}")
    return f"echo({sound})"
