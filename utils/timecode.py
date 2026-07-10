"""Shared time-formatting helpers.

Centralizes the HH:MM:SS conversions that were previously duplicated across the
video info panel and the main window so they stay consistent everywhere.
"""


def seconds_to_hms(seconds: float, decimals: int = 1) -> str:
    """Format a number of seconds as ``HH:MM:SS`` (optionally with a fraction).

    ``decimals`` controls the fractional digits on the seconds component:
    ``0`` gives ``00:01:05``, ``1`` gives ``00:01:05.4``, ``2`` gives
    ``00:01:05.40``. Negative inputs are clamped to zero.
    """
    if seconds < 0:
        seconds = 0.0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if decimals <= 0:
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}"

    # Field width = 2 integer digits + "." + the fractional digits.
    width = decimals + 3
    return f"{hours:02d}:{minutes:02d}:{secs:0{width}.{decimals}f}"


def filename_safe_timecode(time_str: str) -> str:
    """Turn a ``HH:MM:SS.s`` timecode into a filename-safe token."""
    return time_str.replace(":", "-").replace(".", "_")
