from utils.timecode import seconds_to_hms, filename_safe_timecode


class TestSecondsToHms:

    def test_zero(self):
        assert seconds_to_hms(0) == "00:00:00.0"

    def test_one_decimal(self):
        assert seconds_to_hms(65.4, decimals=1) == "00:01:05.4"

    def test_two_decimals(self):
        assert seconds_to_hms(5.0, decimals=2) == "00:00:05.00"

    def test_no_decimals(self):
        assert seconds_to_hms(3661, decimals=0) == "01:01:01"

    def test_hours(self):
        assert seconds_to_hms(3600, decimals=1) == "01:00:00.0"

    def test_negative_clamped_to_zero(self):
        assert seconds_to_hms(-5, decimals=1) == "00:00:00.0"


class TestFilenameSafeTimecode:

    def test_replaces_colons_and_dots(self):
        assert filename_safe_timecode("00:01:05.4") == "00-01-05_4"

    def test_plain_string_unchanged(self):
        assert filename_safe_timecode("frame") == "frame"
