# -*- coding: utf-8 -*-
from utilities import *
from core.initial import Insertions
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

start_time = [[integer_var(min=0,
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


if __name__ == "__main__":
    msol = sub.solve()

    sduties = []
    for i in range(ntrips):
        print(str(i)+" to "+str(msol[trip2trip[i]]) +
              ' - ' + str(msol[trip2duty[i]]))
        duties.append(str(msol[trip2duty[i]]))

    print(set(sduties))
