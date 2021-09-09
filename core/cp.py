# -*- coding: utf-8 -*-
from atopt.utilities import *
from atopt.core.initial import Insertions
from docplex.cp.model import *

datafile = "D:/Google Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"

d = DataProvider(filepath=datafile, route='910')

model = CSPModel(d)
model.build_model()

# initial = Insertions(model)
# initial.solve()

########################################

ntrips = len(model.trips)
nduties = len(model.trips)

sub = CpoModel(name="Pricing_Subproblem")

# trips = [interval_var(start=trip.start_time,
#                       end=trip.end_time,
#                       size=trip.duration,
#                       name=f'Trip_{idx}') for idx, trip in enumerate(model.trips)]


# Duties
min_start = model.data[start_time].min()
max_start = model.data[start_time].max()
min_end = model.data[end_time].min()
max_end = model.data[end_time].max()

duties = [interval_var(start=(min_start, max_start),
                       end=(min_end, max_end),
                       size=model.constraints.shift_span,
                       name=f"Duty_{i}",
                       optional=True)
          for i in range(nduties)]

trip2trip = integer_var_list(size=ntrips,
                             min=0,
                             max=ntrips + 1,
                             name='Trip2Trip')

trip2duty = integer_var_list(size=ntrips,
                             min=0,
                             max=nduties,
                             name='Trip2Duty')

start_times = [[integer_var(min=0,
                            max=model.constraints.shift_span,
                            name=f"StartTime-{i}-{j}")
               for j in range(nduties)] for i in range(ntrips)]

cdt = integer_var_list(size=nduties,
                       min=0,
                       max=model.constraints.continuous_driving,
                       name="CDT")

tdt = integer_var_list(size=nduties,
                       min=0,
                       max=model.constraints.total_driving,
                       name="TDT")

for i in range(ntrips):
    for j in range(ntrips):
        sub.add(sub.if_then(
            trip2trip[i] == j, model.end_time_arr[i] <= model.start_time_arr[j]))

for i in range(ntrips):
    for j in range(ntrips):
        sub.add(sub.if_then(
            trip2trip[i] == j, model.end_loc_arr[i] <= model.start_loc_arr[j]))

for i in range(ntrips):
    sub.add(trip2trip[i] != i)

for i in range(ntrips):
    for j in range(ntrips):
        sub.add(sub.if_then(trip2trip[i] == j, trip2duty[i] == trip2duty[j]))


def report_solution(cpsol: CpoSolveResult):
    trips_per_duty = {}
    for i in range(ntrips):
        _out = f"{i:>2} -> {cpsol[trip2trip[i]]} | Duty: {cpsol[trip2duty[i]]}"
        print(_out)

        duty_id = cpsol[trip2duty[i]]

        if duty_id in trips_per_duty:
            trips_per_duty[duty_id].append(i)
        else:
            trips_per_duty[duty_id] = []
            trips_per_duty[duty_id].append(i)

    print(f'\n\nTotal Duties: {len(trips_per_duty.keys())}')

    for duty_id, duty_trips in trips_per_duty.items():
        df_trips = model.data.loc[duty_trips]

        span = df_trips[end_time].max() - df_trips[start_time].min()

        print(
            f'\n\n>>> Duty {duty_id} - Trips: {len(duty_trips)} - Drive Time: {df_trips[trip_duration].sum()} - Shift Span: {span}\n')
        print(df_trips)


if __name__ == "__main__":
    msol = sub.solve()

    report_solution(msol)
