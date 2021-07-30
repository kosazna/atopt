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

        for st, et, td in zip(self.data[start_time],
                          self.data[end_time],
                          self.data[trip_duration]):
            _duties.append(Duty(st, et, td))

        return _duties

    def solve(self):
        for duty in self.duties:

            try:
                shift = self.shifts[-1]
            except IndexError:
                shift = Shift(self.constraints, duty.start_time)
                continue
