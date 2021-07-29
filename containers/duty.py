# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class Duty:
    start_time: int
    end_time: int
    max_end_time: int = 0
    working_time: int = 0
    short_rests: int = 0
    rest_time: int = 0
    breaks: int = 0
    break_time: int = 0
    trips: set = set()
