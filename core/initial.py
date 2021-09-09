# -*- coding: utf-8 -*-
from atopt.utilities.data import *
from copy import deepcopy


class Insertions:
    def __init__(self, model: CSPModel) -> None:
        self.data = model.data.copy()
        self.constraints = model.constraints
        self.trips = deepcopy(model.trips)
        self.duties = deepcopy(model.duties)
        self.sol = None

    def solve(self):
        max_insertions = len(self.trips)
        c = 0

        while c < max_insertions:
            next_id = len(self.duties)
            duty = Duty(next_id, self.constraints)

            for trip in self.trips:
                if not trip.is_covered and duty.can_add_trip(trip):
                    duty.add_trip(trip)
                    trip.is_covered = True
                    trip.duty = duty
                    c += 1

            self.duties.append(duty)

        self.sol = Solution(self.trips, self.duties, self.constraints)


if __name__ == "__main__":
    datafile = "D:/Google Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
    d = DataProvider(filepath=datafile, route='910')
    model = CSPModel(d)
    model.build_model()
    initial = Insertions(model)
    initial.solve()
    for duty in initial.duties:
        print(duty)

    print(initial.sol.trip_duty_arr)
    print(initial.sol.start_time_arr)
    print(initial.sol.end_time_arr)
    print(initial.sol.duration_arr)
    print([trip.ID for trip in initial.sol.trips])