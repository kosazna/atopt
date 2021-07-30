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

        for st, et in zip(self.data[start_time], self.data[end_time]):
            _duties.append(Duty(st, et))

        return _duties

    def solve(self):
        for duty in self.duties:

            try:
                shift = self.shifts[-1]
            except IndexError:
                shift = Shift(self.constraints, duty.start_time)
                continue
