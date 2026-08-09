def format_duration(total_seconds: float) -> str:
    """130 -> "2 min 10 sec", 120 -> "2 mins", 35 -> "35 sec" — people don't
    think in raw seconds, so notification text should read in the units a
    person would actually use."""
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
    if seconds and not hours:
        parts.append(f"{seconds} sec")
    return " ".join(parts) if parts else "0 sec"
