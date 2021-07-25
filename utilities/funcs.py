# -*- coding: utf-8 -*-

def time2minutes(_time):
    h, m = map(int, _time.split(':'))

    if not 0 <= h <= 23:
        raise ValueError("Hours should be between 0 and 23")

    if not 0 <= m <= 59:
        raise ValueError("Minutes should be between 0 and 59")

    return int(h) * 60 + int(m)


def minutes2time(_minutes):
    if not 0 <= _minutes <= 1440:
        raise ValueError("Minutes since midnight should be between 0 and 1440")

    if _minutes == 1440:
        return "00:00"
    return f"{_minutes // 60:02d}:{_minutes % 60:02d}"
