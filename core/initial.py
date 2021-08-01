# -*- coding: utf-8 -*-
from atopt.utilities.data import *


class InitialSolution:
    def __init__(self, data_provider: DataProvider) -> None:
        self.data = data_provider.data
        self.constraints = data_provider.constraints
        self.trips: List[Trip] = self._create_trips()
        self.duties: List[Duty] = []

    def _create_trips(self) -> list:
        _duties = []

        _min = self.data[trip_duration].min()

        for row in self.data.itertuples():

            _duties.append(Trip(str(row.Index),
                                row.initial_depot,
                                row.final_depot,
                                row.start_time,
                                row.end_time,
                                row.trip_duration,
                                _min,
                                False))

        return _duties

    def solve(self):
        max_insertions = len(self.trips)
        c = 0

        while c < max_insertions:
            next_id = c + 1
            duty = Duty(str(next_id), self.constraints)

            for trip in self.trips:
                if not trip.is_in_duty and duty.can_add_trip(trip):
                    duty.add_trip(trip)
                    trip.is_in_duty = True
                    c += 1

            self.duties.append(duty)
