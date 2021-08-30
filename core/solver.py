import sys
import docplex.cp
from docplex.cp.model import CpoModel
from docplex.mp.model import Model
from atopt.utilities import *
from atopt.core.initial import Insertions


class CGCPSolver:
    def __init__(self, solution: Solution) -> None:
        self.trips = solution.trips
        self.duties = solution.duties
        self.constraints = solution.constraints
        self.trip_duty_arr = solution.trip_duty_arr
        self.start_loc_arr = solution.start_loc_arr
        self.end_loc_arr = solution.end_loc_arr
        self.start_time_arr = solution.start_time_arr
        self.end_time_arr = solution.end_time_arr
        self.duration_arr = solution.duration_arr

    def init_master(self):
        rmp = Model(name='Restricted_Master_Problem')

        rmp.trips = self.trips
        rmp.duties = self.duties

        rmp.binary_var_matrix()

    def init_pricing(self):
        sub = CpoModel(name="Pricing_Subproblem")

        spells = {}
        for trip in self.trips:
            spells[trip.ID] = sub.interval_var(start=trip.start_time,
                                                    end=trip.end_time,
                                                    length=trip.duration,
                                                    size=trip.duration,
                                                    name=f"Trip_{trip.ID}")


if __name__ == "__main__":
    datafile = "D:/Google Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
    d = DataProvider(filepath=datafile, route='910')
    model = CSPModel(d)
    model.build_model()
    initial = Insertions(model)
    initial.solve()
    cgcp = CGCPSolver(initial.sol)
