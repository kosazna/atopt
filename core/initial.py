# -*- coding: utf-8 -*-
from atopt.utilities.data import *


class Insertions:
    def __init__(self, model: Model) -> None:
        self.data = model.data
        self.constraints = model.constraints
        self.trips = model.trips
        self.duties = model.duties

    def solve(self):
        max_insertions = len(self.trips)
        c = 0

        while c < max_insertions:
            next_id = c + 1
            duty = Duty(str(next_id), self.constraints)

            for trip in self.trips:
                if not trip.is_covered and duty.can_add_trip(trip):
                    duty.add_trip(trip)
                    trip.is_covered = True
                    c += 1

            self.duties.append(duty)


if __name__ == "__main__":
    datafile = "D:/Google Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
    d = DataProvider(filepath=datafile, route='910')
    model = Model(d)
    model.build_model()
    sol = Insertions(model)
    sol.solve()
    for duty in sol.duties:
        print(duty)