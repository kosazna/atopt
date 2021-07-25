# -*- coding: utf-8 -*-
from typing import Union


def time2minutes(_time: str) -> int:
    h, m = map(int, _time.split(':'))

    if not 0 <= h <= 23:
        raise ValueError("Hours should be between 0 and 23")

    if not 0 <= m <= 59:
        raise ValueError("Minutes should be between 0 and 59")

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
