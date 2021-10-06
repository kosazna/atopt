
from atopt.utilities import *
from atopt.core.initial import Insertions
from docplex.cp.model import *
from datetime import datetime
from pathlib import Path
import argparse
import docplex.cp.utils_visu as visu
import matplotlib.pyplot as plt
from pylab import rcParams

rcParams['figure.figsize'] = 10, 4

my_parser = argparse.ArgumentParser()
my_parser.add_argument('-trips', action='store', type=int)
my_parser.add_argument('-duties', action='store', type=int)

args = my_parser.parse_args()

datafile = "C:/Users/aznavouridis.k/My Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
sol_folder = Path("D:/.temp/.dev/.aztool/atopt/sols")
d = DataProvider(filepath=datafile, route='910', adjust_for_traffic=True)

model = CSPModel(d)
model.build_model()

# initial = Insertions(model)
# initial.solve()

########################################
if args.trips is None:
    NTRIPS = len(model.trips)
else:
    model.trips = model.trips[:args.trips]
    NTRIPS = len(model.trips)

if args.duties is None:
    NDUTIES = 10
else:
    NDUTIES = args.duties

# print(model.durations)
# print(model.start_times)


sub = CpoModel(name="Pricing_Subproblem")

min_start = model.data[start_time].min()
max_start = model.data[start_time].max()
min_end = model.data[end_time].min()
max_end = model.data[end_time].max()

# trips = [interval_var(start=(trip.start_time, trip.start_time),
#                       end=(trip.end_time, trip.end_time),
#                       size=trip.duration,
#                       name=f'Trip_{idx}') for idx, trip in enumerate(model.trips)]


duties = [interval_var(start=(min_start, max_start),
                       end=(min_end, max_end),
                       size=(0, model.constraints.shift_span),
                       name=f"Duty_{i}",
                       optional=True)
          for i in range(NDUTIES)]

breaks = [interval_var(size=model.constraints.break_time,
                       name=f"BreakTime_{i}",
                       optional=True)
          for i in range(NDUTIES)]

trip2duty = {}
for t, trip in enumerate(model.trips):
    for d in range(NDUTIES):
        trip2duty[(t, d)] = sub.interval_var(start=(trip.start_time, trip.start_time),
                                             end=(trip.end_time, trip.end_time),
                                             size=trip.duration,
                                             name=f"Trip_{t:02} | Duty_{d:02}",
                                             optional=True)

########################################

for d in range(NDUTIES):
    sub.add(sub.span(duties[d], [trip2duty[(t, d)] for t in range(NTRIPS)]))

for d in range(NDUTIES):
    sub.add(sub.no_overlap([trip2duty[(t, d)] for t in range(NTRIPS)]))

for t in range(NTRIPS):
    sub.add(sub.sum([sub.presence_of(trip2duty[(t, d)])
            for d in range(NDUTIES)]) == 1)

cdt  = {}

for d in range(NDUTIES):
    cdt[d] = step_at(0, 0)
    for t in range(NTRIPS):
        cdt[d] += sub.step_at(trip2duty[(t, d)].start[0], trip2duty[(t, d)].size[0])

    sub.add(sub.cumul_range(cdt[d], 0, model.constraints.shift_span))
        # if cdt[d] > model.constraints.continuous_driving:
        #     sub.add(sub.start_of(breaks[(d)]) == sub.end_of_prev([trip2duty[(t, d)] for t in range(NTRIPS)], trip2duty[(t, d)]))
        # print(cdt[d])
    # sub.add(cdt[d] <= model.constraints.continuous_driving)



# cdt = {}
# tdt = {}
# for d in range(NDUTIES):
#     cdt[d] = sub.step_at(0, 0)
#     tdt[d] = sub.step_at(0, 0)
#     for t in range(NTRIPS):
#         cdt[d] += sub.pulse(trip2duty[(t, d)], model.durations[t])
#         tdt[d] += sub.pulse(trip2duty[(t, d)], model.durations[t])
#     sub.add(cdt[d] <= model.constraints.continuous_driving)
#     sub.add(tdt[d] <= model.constraints.total_driving)


obj = sub.sum([sub.presence_of(duty) for duty in duties])
sub.add(sub.minimize(obj))

if __name__ == "__main__":

    cpsol = sub.solve()
    bounds = cpsol.get_objective_bounds()
    status = cpsol.get_solve_status()

    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    out = sol_folder.joinpath(f"{date_str}_{status}_{bounds[0]}.txt")

    cpsol.print_solution()

    for d in range(NDUTIES):
        if cpsol[duties[d]]:
            print(f"\n> Duty {d} : {cpsol[duties[d]]}")
            # print(cdt[d])
            _tdt = 0
            _ntrips = 0
            for t in range(NTRIPS):
                if cpsol[trip2duty[(t, d)]]:
                    print(f"  - Trip {t} : {cpsol[trip2duty[(t, d)]]}")
                    _tdt += model.durations[t]
                    _ntrips += 1
            print(f"\n  > Driving Time: {_tdt}, Trips: {_ntrips}")

            print(cdt[d])
    cpsol.write(str(out))


    visu.timeline(f"{date_str}_{status}_{bounds[0]}", origin=min_start, horizon=max_end)

    for d in range(NDUTIES):
        if cpsol[duties[d]]:
            visu.panel()
            visu.sequence(name=duties[d].get_name(),
                        intervals=[(cpsol.get_var_solution(trip2duty[(t, d)]), d, str(t)) for t in range(NTRIPS) if cpsol[trip2duty[(t, d)]]])

    visu.show()
