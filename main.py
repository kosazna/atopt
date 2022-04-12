# -*- coding: utf-8 -*-
import argparse
from pathlib import Path

from docplex.cp.model import *

from atopt.core.model import BusDriverCSP
from atopt.core.initial import Insertions
from atopt.core.plot import log_and_plot
from atopt.utilities import CSPModel, DataProvider

my_parser = argparse.ArgumentParser()

my_parser.add_argument('-r', '--route', action='store', type=str)
my_parser.add_argument('-d', '--duties', action='store', type=int, default=-1)
my_parser.add_argument('-t', '--trips', action='store', type=int)
my_parser.add_argument('-l', '--limit', action='store', type=int, default=-1)
my_parser.add_argument('-v', '--vehicles', action='store', type=int)
my_parser.add_argument('-a', '--adjust', action='store', type=int, default=1)
my_parser.add_argument('-b', '--breaks', action='store', type=int, default=1)
my_parser.add_argument('-o', '--objective', action='store', type=int, default=1)
my_parser.add_argument('-u', '--upperbound',
                       action='store', type=int, default=1)

my_parser.add_argument('-s', '--save', action='store', type=str)
my_parser.add_argument('-f', '--filepath',
                       action='store',
                       type=str,
                       default='Model Data.xlsx')


if __name__ == "__main__":
    args = my_parser.parse_args()

    if args.route is None:
        raise ValueError("Route must be set with [-r] flag")

    ROUTE = args.route
    NTRIPS = args.trips
    BUSES = args.vehicles
    TRAFFIC = bool(args.adjust)
    BREAKS = bool(args.breaks)
    OBJECTIVE = bool(args.objective)
    UPPER_BOUND = bool(args.upperbound)
    DATAFILE = args.filepath

    d = DataProvider(filepath=DATAFILE,
                     route=ROUTE,
                     adjust_for_traffic=TRAFFIC)

    model = CSPModel(data_provider=d,
                     ntrips=NTRIPS)

    model.build_model()

    if args.duties == -1:
        NDUTIES = int(model.minimum_duties * 1.5) + 1
    else:
        NDUTIES = args.duties

    if args.save is None:
        SAVELOC = Path.cwd().joinpath('sols')

        if not SAVELOC.exists():
            SAVELOC.mkdir(parents=True, exist_ok=True)
    else:
        SAVELOC = Path(args.save)

    if UPPER_BOUND and args.duties == -1:
        initial = Insertions(model)
        initial.solve()
        upper_bound = len(initial.duties)
    elif UPPER_BOUND and args.duties != -1:
        upper_bound = NDUTIES
    elif not UPPER_BOUND and args.duties != -1:
        upper_bound = NDUTIES
    else:
        upper_bound = None

    if args.limit == -1:
        TIMELIMIT = None
    else:
        TIMELIMIT = args.limit

    print("\n\n-- Problem Details --\n")
    print(f"Route:     {ROUTE}")
    print(f"Depot:     {model.depot_type}")
    print(f"Duties:    {NDUTIES} (created variables)")
    print(f"Trips:     {d.trips}" if NTRIPS is None else f"Trips:     {NTRIPS}")
    print(f"Traffic:   {TRAFFIC}")
    print(f"Breaks:    {BREAKS}")
    print(f"Vehicles:  No limit (min: {model.minimum_buses})" if BUSES is None else f"Vehicles:  {BUSES} (min: {model.minimum_buses})")
    print(f"Objective: {OBJECTIVE}")
    print(f"Timelimit: {TIMELIMIT} seconds")
    print(f"LB:        {int(model.minimum_duties)}")
    print(f"UB:        {upper_bound}\n" if (UPPER_BOUND and OBJECTIVE) else "UB:        Not set\n")
    print("----------------------")

    print(f"\nInitializing model...\n")

    cp_model, model_info = BusDriverCSP(model=model,
                                        nduties=NDUTIES,
                                        ntrips=NTRIPS,
                                        add_breaks=BREAKS,
                                        nbuses=BUSES,
                                        objective=OBJECTIVE,
                                        ub=upper_bound)

    cpsol = cp_model.solve(TimeLimit=TIMELIMIT)

    log_and_plot(sol=cpsol,
                 model_info=model_info,
                 save_folder=SAVELOC,
                 has_breaks=BREAKS,
                 has_traffic=TRAFFIC)
