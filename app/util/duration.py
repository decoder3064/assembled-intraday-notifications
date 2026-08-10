def format_duration(total_seconds: float) -> str:
    """Turns a duration in seconds into a readable string, e.g. 130 -> "2 min 10 sec"."""
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
