from os import stat
from atopt.utilities import *
from atopt.core.initial import Insertions
from docplex.cp.model import *
from IPython.display import display
from datetime import datetime
from pathlib import Path
import sys

datafile = "C:/Users/aznavouridis.k/My Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
sol_folder = Path("D:/.temp/.dev/.aztool/atopt/sols")
d = DataProvider(filepath=datafile, route='910')

model = CSPModel(d)
model.build_model()

# initial = Insertions(model)
# initial.solve()

########################################
if len(sys.argv) > 1:
    _trips = int(sys.argv[1])
    _duties = int(sys.argv[2])

    model.trips = model.trips[:_trips]

    NTRIPS = len(model.trips)
    NDUTIES = _duties
else:
    NTRIPS = len(model.trips)
    NDUTIES = 10

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
                                             name=f"Trip_{t:02}-Duty_{d:02}",
                                             optional=True)

########################################

for d in range(NDUTIES):
    sub.add(sub.span(duties[d], [trip2duty[(t, d)] for t in range(NTRIPS)]))

for d in range(NDUTIES):
    sub.add(sub.no_overlap([trip2duty[(t, d)] for t in range(NTRIPS)]))

for t in range(NTRIPS):
    sub.add(sub.sum([sub.presence_of(trip2duty[(t, d)])
            for d in range(NDUTIES)]) == 1)


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
            for t in range(NTRIPS):
                if cpsol[trip2duty[(t, d)]]:
                    print(f"  - Trip {t} : {cpsol[trip2duty[(t, d)]]}")

    cpsol.write(str(out))
