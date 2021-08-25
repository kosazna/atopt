# -*- coding: utf-8 -*-
from typing import Union
from atopt.config import traffic_timeslots


def time2minutes(_time: str) -> int:
    h, m = map(int, _time.split(':'))

    if not 0 <= h <= 23:
        raise ValueError("Hours should be between 0 and 23")

    if not 0 <= m <= 59:
        raise ValueError("Minutes should be between 0 and 59")

    _minutes = int(h) * 60 + int(m)

    if _minutes == 0:
        return 1440
    return int(h) * 60 + int(m)


def minutes2time(_minutes: Union[int, str]) -> str:
    if isinstance(_minutes, str):
        _mins = int(_minutes)
    else:
        _mins = _minutes

    if not 0 <= _mins <= 1440:
        raise ValueError("Minutes since midnight should be between 0 and 1440")

    if _mins == 1440:
        return "00:00"
    return f"{_mins // 60:02d}:{_mins % 60:02d}"


def weighted_trip_duration(start_time, duration):
    if duration < 0:
        raise ValueError("Trip duration should be greater than 0")
    else:
        for timeslot in traffic_timeslots:
            if start_time in range(*timeslot):
                return int(duration * traffic_timeslots[timeslot])

        return duration


def calculate_trip_end_time(start_time, duration):
    end_time = start_time + duration
    # if end_time >= 1440:
    #     return end_time - 1440
    return end_time
