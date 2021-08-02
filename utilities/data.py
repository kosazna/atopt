# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List

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

        self.min_break_time = self.data.loc['break time', 'min']
        self.max_break_time = self.data.loc['break time', 'max']

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
class Trip:
    ID: str
    start_loc: str
    end_loc: str
    start_time: int
    end_time: int
    duration: int
    min_duration: int
    is_covered: bool


class Duty:
    def __init__(self,
                 _id: str,
                 constraints: Contraints) -> None:
        self.constraints = constraints

        self.ID = _id
        self.start_time: int = 0
        self.end_time: int = 0
        self.max_end_time: int = 0

        self.working_time: int = 0
        self.driving_time: int = 0
        self.continuous_driving_time: int = 0

        self.rests: int = 0
        self.rest_time: int = 0

        self.breaks: int = 0
        self.break_time: int = 0

        self.available_from: int = -1

        self.overnight: bool = False
        self.trips: List[Trip] = []

        

    def __repr__(self) -> str:
        trips = '-'.join([t.ID for t in self.trips])
        return f"Duty(ID={self.ID}, start={self.start_time}, end={self.end_time}, trips={len(self.trips)}, driving_time={self.driving_time}, rests={self.rests} breaks={self.breaks}, trips={trips}"

    def _calc_max_end_time(self):
        self.max_end_time = calculate_trip_end_time(self.start_time,
                                                    self.constraints.shift_span)
        if self.max_end_time < self.start_time:
            self.overnight = True

    def can_add_trip(self, trip: Trip) -> bool:
        try:
            last_trip = self.trips[-1]
        except IndexError:
            return True

        _working = self.working_time + trip.duration
        _total = self.driving_time + trip.duration
        _continuous = self.continuous_driving_time + trip.duration

        if last_trip.end_loc == trip.start_loc:
            is_driving = trip.start_time < self.end_time
            is_on_break = trip.start_time < self.available_from
            is_shift_ended = trip.end_time > self.max_end_time
            is_total_maxed = _total > self.constraints.max_total_driving_time
            is_continuous_maxed = _continuous > self.constraints.continuous_driving_time

            return not any([is_driving,
                            is_on_break,
                            is_shift_ended,
                            is_total_maxed,
                            is_continuous_maxed])

        else:
            return False

    def add_trip(self, trip: Trip) -> None:
        if self.trips:
            last_trip = self.trips[-1]
            _rest = trip.start_time - last_trip.end_time
            self.rest_time += _rest
            self.rests += 1
            self.end_time = trip.end_time
            self.continuous_driving_time += trip.duration
            self.driving_time += trip.duration
            self.working_time += _rest + trip.duration
        else:
            self.start_time = trip.start_time
            self.end_time = trip.end_time
            self.continuous_driving_time += trip.duration
            self.driving_time += trip.duration
            self.working_time += trip.duration
            self._calc_max_end_time()

        _driving_until_break = self.constraints.continuous_driving_time - \
            self.continuous_driving_time
        if _driving_until_break < trip.min_duration:
            self.breaks += 1
            self.break_time += self.constraints.min_break_time
            self.available_from = trip.end_time + self.constraints.min_break_time
            self.continuous_driving_time = 0

        self.trips.append(trip)


class Model:
    def __init__(self, data_provider: DataProvider) -> None:
        self.data = data_provider.data
        self.constraints = data_provider.constraints
        self.trips: List[Trip] = []
        self.duties: List[Duty] = []

    def build_model(self) -> list:
        _min = self.data[trip_duration].min()

        for row in self.data.itertuples():

            self.trips.append(Trip(str(row.Index),
                                    row.initial_depot,
                                    row.final_depot,
                                    row.start_time,
                                    row.end_time,
                                    row.trip_duration,
                                    _min,
                                    False))
