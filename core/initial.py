# -*- coding: utf-8 -*-
from atopt.utilities.data import *


class Insertions:
    def __init__(self, model: Model) -> None:
        self.data = model.data
        self.constraints = model.constraints
        self.trips = model.trips
        self.duties = model.duties
        self.sol = None

    def solve(self):
        max_insertions = len(self.trips)
        c = 0

        while c < max_insertions:
            next_id = len(self.duties)
            duty = Duty(str(next_id), self.constraints)

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
    model = Model(d)
    model.build_model()
    sol = Insertions(model)
    sol.solve()
    for duty in sol.duties:
        print(duty)

    print(sol.sol.trip_duty_arr)
    print(sol.sol.start_time_arr)
    print(sol.sol.end_time_arr)
    print(sol.sol.duration_arr)
    print([trip.ID for trip in sol.sol.trips])
    print(sol.sol.start_loc_arr)