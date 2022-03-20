# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
from atopt.core.plot import log_and_plot
from atopt.core.initial import Insertions
from atopt.utilities import CSPModel, DataProvider
from docplex.cp.model import *


def BusDriverCSP(model: CSPModel,
                 nduties: int,
                 ntrips: Optional[int] = None,
                 add_breaks: Optional[bool] = True,
                 nbuses: Optional[int] = None,
                 objective: Optional[bool] = True,
                 ub: Optional[int] = None) -> CpoModel:

    if nbuses is not None and nbuses < model.minimum_buses:
        raise ValueError(
            f"Model can't be solved with less than {model.minimum_buses} vehicles")

    if nduties is not None and nduties < model.minimum_duties:
        raise ValueError(
            f"Model can't be solved with less than {model.minimum_duties} duties")

    cp_model = CpoModel(name="Bus Driver Crew Scheduling Problem Model")

    NDUTIES = nduties

    if ntrips is None:
        NTRIPS = len(model.trips)
    else:
        NTRIPS = ntrips

    breaks = None

    duties = [interval_var(start=(model.min_start, model.max_start),
                           end=(model.min_end, model.max_end),
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
        duty_intervals = [trip2duty[(t, d)] for t in range(NTRIPS)]
        cp_model.add(no_overlap(duty_intervals))

    for t in range(NTRIPS):
        trip_coverage = cp_model.sum([presence_of(trip2duty[(t, d)])
                                      for d in range(NDUTIES)])
        cp_model.add(trip_coverage == 1)

    for d in range(NDUTIES):
        duty_driving_time = cp_model.sum([model.durations[t] * presence_of(trip2duty[(t, d)])
                                          for t in range(NTRIPS)])
        cp_model.add(duty_driving_time <= model.constraints.total_driving)

    if model.depot_type == "Multiple Depot":
        for d in range(NDUTIES):
            for t1 in range(NTRIPS):
                for t2 in range(NTRIPS):
                    if model.start_times[t2] >= model.end_times[t1]:
                        next_trips = []
                        for t3 in range(NTRIPS):
                            if model.start_times[t3] >= model.end_times[t1] and model.end_times[t3] <= model.start_times[t2]:
                                next_trips.append(t3)
                        cp_model.add(
                            if_then(
                                logical_and([presence_of(trip2duty[(t1, d)]),
                                             presence_of(trip2duty[(t2, d)]),
                                             (sum([presence_of(trip2duty[(t3, d)]) for t3 in next_trips]) == 0)]),
                                (model.start_locs[t2] == model.end_locs[t1]))
                        )

    # If the model is to be solved considering breaks then
    # the following variables and constraints are added
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
                trips_duration = sum([model.durations[b] * presence_of(trip2duty[(b, d)])
                                     for b in previous_trips]) + (model.durations[t])
                cp_model.add(end_dt[t][d] == trips_duration)

        for t in range(NTRIPS):
            for d in range(NDUTIES):
                cp_model.add(
                    if_then(
                        logical_and((end_dt[t][d] <= model.constraints.continuous_driving),
                                    (presence_of(trip2duty[(t, d)]))),
                        (end_of(trip2duty[(t, d)]) <= start_of(breaks[d]))))
                cp_model.add(
                    if_then(
                        logical_and((end_dt[t][d] > model.constraints.continuous_driving),
                                    (presence_of(trip2duty[(t, d)]))),
                        (start_of(trip2duty[(t, d)]) >= end_of(breaks[d]))))

    # If the model is to be solved considering vehicle limit then
    # the following variable and constraint are added
    if nbuses is not None:
        bus_usage = step_at(0, 0)
        for t in range(NTRIPS):
            for d in range(NDUTIES):
                bus_usage += pulse(trip2duty[(t, d)], 1)

        cp_model.add(bus_usage <= nbuses)

    # If the model is to be solved as a constraint optimization problem
    # instead of constraint satisfaction problem then
    # the following obective is added
    if objective:
        obj = cp_model.sum([presence_of(duty) for duty in duties])
        cp_model.add(obj >= model.minimum_duties)

        if ub is not None:
            cp_model.add(obj <= ub)

        cp_model.add(cp_model.minimize(obj))

    model_info = {
        'model': model,
        'ntrips': NTRIPS,
        'nduties': NDUTIES,
        'duties': duties,
        'trip2duty': trip2duty,
        'breaks': breaks,
        'nbuses': nbuses,
        'min_start': model.min_start,
        'max_end': model.max_end
    }

    return cp_model, model_info


if __name__ == "__main__":

    DATAFILE = "C:/Users/aznavouridis.k/OneDrive/_Thesis_/Main Thesis/Model Data.xlsx"
    SAVELOC = "D:/.temp/.dev/.aztool/atopt/sols"

    ROUTE = "A2"

    OBJECTIVE = True
    TIMELIMIT = 120
    UPPER_BOUND = True

    NDUTIES = 24
    NTRIPS = None

    BREAKS = False
    TRAFFIC = True
    NBUSES = None

    d = DataProvider(filepath=DATAFILE,
                     route=ROUTE,
                     adjust_for_traffic=TRAFFIC)

    model = CSPModel(data_provider=d,
                     ntrips=NTRIPS)

    model.build_model()

    if UPPER_BOUND:
        initial = Insertions(model)
        initial.solve()
        upper_bound = len(initial.duties)
    else:
        upper_bound = None

    cp_model, model_info = BusDriverCSP(model=model,
                                        nduties=NDUTIES,
                                        ntrips=NTRIPS,
                                        add_breaks=BREAKS,
                                        nbuses=NBUSES,
                                        objective=OBJECTIVE,
                                        ub=upper_bound)

    cp_sol = cp_model.solve(TimeLimit=TIMELIMIT)

    log_and_plot(sol=cp_sol,
                 model_info=model_info,
                 save_folder=SAVELOC,
                 has_breaks=BREAKS,
                 has_traffic=TRAFFIC)
