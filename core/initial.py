# -*- coding: utf-8 -*-
from atopt.utilities.data import *


class InitialSolution:
    def __init__(self, data_provider: DataProvider) -> None:
        self.data = data_provider.data
        self.constraints = data_provider.constraints
        self.duties = self._create_duties()
        self.shifts: list = []

    def _create_duties(self) -> list:
        _duties = []

        for row in self.data.itertuples():

            _duties.append(Duty(str(row.Index),
                                row.initial_depot,
                                row.final_depot,
                                row.start_time,
                                row.end_time,
                                row.trip_duration))

        return _duties

    def solve(self):
        for duty in self.duties:

            try:
                shift = self.shifts[-1]
            except IndexError:
                shift = Shift(self.constraints, duty.start_time)
                continue
