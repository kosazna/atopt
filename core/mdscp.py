# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
from atopt.core.plot import log_and_plot
from atopt.utilities import CSPModel, DataProvider
from docplex.cp.model import *


def multi_depot_CSP(model: CSPModel,
                    nduties: int,
                    ntrips: Optional[int] = None,
                    add_breaks: Optional[bool] = True,
                    nbuses: Optional[int] = None,
                    objective: Optional[bool] = True) -> CpoModel:

    cp_model = CpoModel(name="CSP_Multiple_Depot")

    NDUTIES = nduties

    if ntrips is None:
        NTRIPS = len(model.trips)
    else:
        NTRIPS = ntrips

    min_start = min(model.start_times)
    max_start = max(model.start_times)
    min_end = min(model.end_times)
    max_end = max(model.end_times)

    lower_bound = np.ceil(sum(model.durations) / model.constraints.shift_span)

    breaks = None

    duties = [interval_var(start=(min_start, max_start),
                           end=(min_end, max_end),
                           size=(0, model.constraints.shift_span),
                           name=f"Duty_{i}",
                           optional=True)
              for i in range(NDUTIES)]

    trip2duty = {}
    for t, trip in enumerate(model.trips):
        for d in range(NDUTIES):
            trip2duty[(t, d)] = interval_var(start=(trip.start_time, trip.start_time),
                                             end=(trip.end_time, trip.end_time),
                                             size=trip.duration,
                                             name=f"Trip_{t:02} | Duty_{d:02}",
                                             optional=True)

    for d in range(NDUTIES):
        cp_model.add(span(duties[d],
                          [trip2duty[(t, d)] for t in range(NTRIPS)]))

    for d in range(NDUTIES):
        cp_model.add(no_overlap([trip2duty[(t, d)] for t in range(NTRIPS)]))

    for t in range(NTRIPS):
        cp_model.add(cp_model.sum([presence_of(trip2duty[(t, d)])
                                   for d in range(NDUTIES)]) == 1)
    if add_breaks:
        breaks = [interval_var(size=model.constraints.break_time,
                               name=f"BreakTime_{i}",
                               optional=True)
                  for i in range(NDUTIES)]

        end_dt = []
        for t in range(NTRIPS):
            end_dt.append([integer_var(min=0,
                                       max=model.constraints.shift_span,
                                       name=f"EDT_{t:02}_{d:02}") for d in range(NDUTIES)])

        for t in range(NTRIPS):
            previous_trips = []
            for b in range(NTRIPS):
                if model.end_times[b] <= model.start_times[t]:
                    previous_trips.append(b)
            for d in range(NDUTIES):
                cp_model.add(end_dt[t][d]
                             == sum([(model.durations[b]) * presence_of(trip2duty[(b, d)]) for b in previous_trips])
                             + (model.durations[t]))

        for t in range(NTRIPS):
            for d in range(NDUTIES):
                cp_model.add(
                    if_then(
                        logical_and((end_dt[t][d] <= model.constraints.continuous_driving),
                                    (presence_of(trip2duty[(t, d)]))),
                        (end_of(trip2duty[(t, d)]) <= start_of(breaks[(d)]))))
                cp_model.add(
                    if_then(
                        logical_and((end_dt[t][d] > model.constraints.continuous_driving),
                                    (presence_of(trip2duty[(t, d)]))),
                        (start_of(trip2duty[(t, d)]) >= end_of(breaks[(d)]))))

    if nbuses is not None:
        bus_usage = step_at(0, 0)
        for t in range(NTRIPS):
            for d in range(NDUTIES):
                bus_usage += pulse(trip2duty[(t, d)], 1)

        cp_model.add(bus_usage <= nbuses)

    if objective:
        obj = cp_model.sum([presence_of(duty) for duty in duties])
        cp_model.add(obj >= lower_bound)
        cp_model.add(cp_model.minimize(obj))

    model_info = {
        'model': model,
        'ntrips': NTRIPS,
        'nduties': NDUTIES,
        'duties': duties,
        'trip2duty': trip2duty,
        'breaks': breaks,
        'nbuses': nbuses,
        'min_start': min_start,
        'max_end': max_end
    }

    return cp_model, model_info


if __name__ == "__main__":

    DATAFILE = "C:/Users/aznavouridis.k/My Drive/MSc MST-AUEB/_Thesis_/Main Thesis/Model Data.xlsx"
    SAVELOC = "D:/.temp/.dev/.aztool/atopt/sols"
    ROUTE = 'A2'
    BREAKS = False
    TRAFFIC = False
    TIMELIMIT = 60
    NDUTIES = 10

    d = DataProvider(filepath=DATAFILE, route=ROUTE, adjust_for_traffic=TRAFFIC)

    model = CSPModel(d)
    model.build_model()

    cp_model, model_info = multi_depot_CSP(model=model,
                                           nduties=NDUTIES,
                                           ntrips=None,
                                           add_breaks=BREAKS,
                                           nbuses=None,
                                           objective=True)

    cp_sol = cp_model.solve(TimeLimit=TIMELIMIT)

    log_and_plot(sol=cp_sol,
                 model_info=model_info,
                 save_folder=SAVELOC,
                 has_breaks=BREAKS,
                 has_traffic=TRAFFIC)
