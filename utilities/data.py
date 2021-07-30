# -*- coding: utf-8 -*-
from dataclasses import dataclass

import pandas as pd

from .funcs import (calculate_trip_end_time, time2minutes,
                    weighted_trip_duration)

# Column names
trip = 'trip'
initial_depot = 'initial_depot'
final_depot = 'final_depot'
relief_point = 'relief_point'
time = 'time'
trip_duration = 'trip_duration'

start_time = 'start_time'
end_time = 'end_time'


class Contraints:
    def __init__(self, filepath) -> None:
        self.data = pd.read_excel(filepath,
                                  sheet_name='driver constraints').set_index('constraint')
        self._init_values()

    def _init_values(self):
        self.min_total_driving_time = self.data.loc['total driving time', 'min']
        self.max_total_driving_time = self.data.loc['total driving time', 'max']

        self.continuous_driving_time = self.data.loc['continuous driving time', 'min']

        self.min_rest_time = self.data.loc['rest time', 'min']
        self.max_rest_time = self.data.loc['rest time', 'max']

        self.min_rest_time = self.data.loc['break time', 'min']
        self.max_rest_time = self.data.loc['break time', 'max']

        self.shift_span = self.data.loc['shift span', 'min']


class DataProvider:
    def __init__(self, filepath, route) -> None:
        self.filepath = filepath
        self.data = pd.read_excel(filepath, sheet_name=route).set_index(trip)
        self.constraints = Contraints(filepath=filepath)
        self._preprocess()

    def _preprocess(self):
        self.data[start_time] = self.data[time].apply(time2minutes)
        self.data[trip_duration] = self.data.apply(
            lambda x: weighted_trip_duration(x[start_time], x[trip_duration]),
            axis=1)
        self.data[end_time] = self.data.apply(
            lambda x: calculate_trip_end_time(x[start_time], x[trip_duration]),
            axis=1)


@dataclass
class Duty:
    ID: str
    start_loc: str
    end_loc: str
    start_time: int
    end_time: int
    duration: int


@dataclass
class Shift:
    constraints: Contraints
    start_time: int
    end_time: int = 0
    max_end_time: int = 0
    working_time: int = 0
    short_rests: int = 0
    rest_time: int = 0
    breaks: int = 0
    break_time: int = 0
    overnight: bool = False
    trips: tuple = ()

    def __post_init__(self):
        self.max_end_time = calculate_trip_end_time(self.start_time,
                                                    self.constraints.shift_span)
        if self.max_end_time < self.start_time:
            self.overnight = True

    def can_add_duty(self, duty: Duty) -> bool:
        try:
            last_duty = self.trips[-1]
        except IndexError:
            return True

        if last_duty.end_loc == duty.start_loc:
            if duty.start_time >= self.max_end_time or duty.end_time >= self.max_end_time:
                return False

            if self.working_time + duty.trip_duration > self.constraints.max_total_driving_time:
                return False

            if self.working_time + duty.trip_duration > self.constraints.continuous_driving_time:
                return False
        else:
            return False
