
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
my_parser.add_argument('-t', '--trips', action='store', type=int)
my_parser.add_argument('-d', '--duties', action='store', type=int)
my_parser.add_argument('-l', '--limit', action='store', type=int, default=300)
my_parser.add_argument('-r', '--route', action='store', type=str, default='910')
my_parser.add_argument('-f', '--filepath', action='store',
                       type=str, default='Model Data.xlsx')
my_parser.add_argument('-s', '--save', action='store', type=str)


args = my_parser.parse_args()
ROUTE = args.route
TIMELIMIT = args.limit
DATAFILE = args.filepath

DATAFILE = "C:/Users/aznavouridis.k/My Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"

d = DataProvider(filepath=DATAFILE, route=ROUTE, adjust_for_traffic=True)

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

# if args.save is None:
#     SAVELOC = Path.cwd().joinpath('sols')

#     if not SAVELOC.exists():
#         SAVELOC.mkdir(parents=True, exist_ok=True)
# else:
#     SAVELOC = Path(args.save)

SAVELOC = Path("D:/.temp/.dev/.aztool/atopt/sols")


sub = CpoModel(name="Pricing_Subproblem")

min_start = min(model.start_times)
max_start = max(model.start_times)
min_end = min(model.end_times)
max_end = max(model.end_times)

# trips = [interval_var(start=(trip.start_time, trip.start_time),
#                       end=(trip.end_time, trip.end_time),
#                       size=trip.duration,
#                       name=f'Trip_{idx}') for idx, trip in enumerate(model.trips)]

# driving_time = {}

# for d in range(NDUTIES):
#     step = CpoStepFunction()
#     step.set_value(0, max_end, 0)
#     for t in range(len(model.trips)):
#         step.set_value(model.model.start_times[t], model.model.end_times[t], 100)
#     driving_time[d] = step

duties = [interval_var(start=(min_start, max_start),
                       end=(min_end, max_end),
                       size=(0, model.constraints.total_driving),
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

end_dt = []
for t in range(NTRIPS):
    end_dt.append([sub.integer_var(min=0,
                                   max=model.constraints.shift_span,
                                   name=f"EDT_{t:02}_{d:02}") for d in range(NDUTIES)])

########################################

for d in range(NDUTIES):
    sub.add(sub.span(duties[d], [trip2duty[(t, d)] for t in range(NTRIPS)]))

for d in range(NDUTIES):
    sub.add(sub.no_overlap([trip2duty[(t, d)] for t in range(NTRIPS)]))

for t in range(NTRIPS):
    sub.add(sub.sum([sub.presence_of(trip2duty[(t, d)])
            for d in range(NDUTIES)]) == 1)

for t in range(NTRIPS):
    previous_trips = []
    for b in range(NTRIPS):
        if model.end_times[b] <= model.start_times[t]:
            previous_trips.append(b)
    for d in range(NDUTIES):
        sub.add(end_dt[t][d] == sum([(model.durations[b])*sub.presence_of(trip2duty[(b, d)])
                for b in previous_trips]) + (model.durations[t]))

for t in range(NTRIPS):
    for d in range(NDUTIES):
        sub.add(sub.if_then(sub.logical_and((end_dt[t][d] <= model.constraints.continuous_driving), (sub.presence_of(
            trip2duty[(t, d)]))), (sub.end_of(trip2duty[(t, d)]) <= sub.start_of(breaks[(d)]))))
        sub.add(sub.if_then(sub.logical_and((end_dt[t][d] > model.constraints.continuous_driving), (sub.presence_of(
            trip2duty[(t, d)]))), (sub.start_of(trip2duty[(t, d)]) >= sub.end_of(breaks[(d)]))))

# cdt = {}

# for d in range(NDUTIES):
#     cdt[d] = step_at(0, 0)
#     for t in range(NTRIPS):
#         cdt[d] += sub.step_at_end(trip2duty[(t, d)], model.durations[t])

    # sub.add(sub.cumul_range(cdt[d], 0, model.constraints.shift_span))
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

    cpsol = sub.solve(TimeLimit=TIMELIMIT)
    bounds = cpsol.get_objective_bounds()
    status = cpsol.get_solve_status()

    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    out = SAVELOC.joinpath(f"{date_str}_{status}_{bounds[0]}.txt")
    sol_log = SAVELOC.joinpath(f"{date_str}_{status}_{bounds[0]}_SOLUTION.txt")

    cpsol.print_solution()

    with open(sol_log, 'w') as sol_log_file:
        for d in range(NDUTIES):
            if cpsol[duties[d]]:
                print(f"\n> Duty {d} : {cpsol[duties[d]]}")
                sol_log_file.write(f"\n> Duty {d} : {cpsol[duties[d]]}")
                # print(cdt[d])
                _tdt = 0
                _ntrips = 0
                for t in range(NTRIPS):
                    if cpsol[trip2duty[(t, d)]]:
                        print(f"  - Trip {t} : {cpsol[trip2duty[(t, d)]]}")
                        sol_log_file.write(f"\n  - Trip {t} : {cpsol[trip2duty[(t, d)]]}")
                        _tdt += model.durations[t]
                        _ntrips += 1
                print(f"\n  > Driving Time: {_tdt}, Trips: {_ntrips}")
                sol_log_file.write(f"\n  > Driving Time: {_tdt}, Trips: {_ntrips}\n")

            # print(cdt[d])
    cpsol.write(str(out))

    visu.timeline(
        f"{date_str}_{status}_{bounds[0]}", origin=min_start, horizon=max_end)

    for d in range(NDUTIES):
        if cpsol[duties[d]]:
            visu.panel()
            visu.sequence(name=duties[d].get_name(),
                          intervals=[(cpsol.get_var_solution(trip2duty[(t, d)]), d, str(t)) for t in range(NTRIPS) if cpsol[trip2duty[(t, d)]]])
            visu.interval(cpsol.get_var_solution(breaks[d]), 'red', 'B')

    visu.show()
