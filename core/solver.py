import sys
import docplex.cp
from docplex.cp.model import CpoModel
from atopt.utilities import *
from atopt.core.initial import Insertions


class CGCPSolver:
    def __init__(self, solution: Solution) -> None:
        self.trips = solution.trips
        self.duties = solution.duties
        self.constraints = solution.constraints
        self.trip_duty_arr = solution.trip_duty_arr
        self.start_loc_arr = solution.trip_duty_arr
        self.end_loc_arr = solution.trip_duty_arr
        self.start_time_arr = solution.trip_duty_arr
        self.end_time_arr = solution.trip_duty_arr
        self.duration_arr = solution.trip_duty_arr

        self.m = CpoModel(name="Scheduling")
        self.build()

    def build(self):
        spells = {}
        for trip in self.trips:
            spells[trip.ID] = self.m.interval_var(start=trip.start_time,
                                                  end=trip.end_time,
                                                  size=trip.duration,
                                                  name=f"Trip_{trip.ID}")

        print(spells)


if __name__ == "__main__":
    datafile = "D:/Google Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
    d = DataProvider(filepath=datafile, route='910')
    model = Model(d)
    model.build_model()
    initial = Insertions(model)
    initial.solve()
    cgcp = CGCPSolver(initial.sol)
