# -*- coding: utf-8 -*-
import argparse
from pathlib import Path

from docplex.cp.model import *

from atopt.core.model import BusDriverCSP
from atopt.core.plot import log_and_plot
from atopt.utilities import CSPModel, DataProvider

my_parser = argparse.ArgumentParser()

my_parser.add_argument('-r', '--route', action='store', type=str, default='910')
my_parser.add_argument('-d', '--duties', action='store', type=int, default=10)
my_parser.add_argument('-t', '--trips', action='store', type=int)
my_parser.add_argument('-l', '--limit', action='store', type=int, default=120)
my_parser.add_argument('-v', '--vehicles', action='store', type=int)
my_parser.add_argument('-a', '--adjust', action='store', type=int, default=1)
my_parser.add_argument('-b', '--breaks', action='store', type=int, default=1)
my_parser.add_argument('-o', '--objective', action='store', type=int, default=1)

my_parser.add_argument('-s', '--save', action='store', type=str)
my_parser.add_argument('-f', '--filepath',
                       action='store',
                       type=str,
                       default='Model Data.xlsx')


if __name__ == "__main__":
    args = my_parser.parse_args()

    ROUTE = args.route
    NTRIPS = args.trips
    TIMELIMIT = args.limit
    BUSES = args.vehicles
    TRAFFIC = bool(args.adjust)
    BREAKS = bool(args.breaks)
    OBJECTIVE = bool(args.objective)
    DATAFILE = args.filepath

    d = DataProvider(filepath=DATAFILE,
                     route=ROUTE,
                     adjust_for_traffic=TRAFFIC)

    model = CSPModel(data_provider=d, ntrips=NTRIPS)
    model.build_model()

    if args.duties is None:
        NDUTIES = model.minimum_duties
    else:
        NDUTIES = args.duties

    if args.save is None:
        SAVELOC = Path.cwd().joinpath('sols')

        if not SAVELOC.exists():
            SAVELOC.mkdir(parents=True, exist_ok=True)
    else:
        SAVELOC = Path(args.save)

    cp_model, model_info = BusDriverCSP(model=model,
                                        nduties=NDUTIES,
                                        ntrips=NTRIPS,
                                        add_breaks=BREAKS,
                                        nbuses=BUSES,
                                        objective=OBJECTIVE)

    cpsol = cp_model.solve(TimeLimit=TIMELIMIT)

    log_and_plot(sol=cpsol,
                 model_info=model_info,
                 save_folder=SAVELOC,
                 has_breaks=BREAKS,
                 has_traffic=TRAFFIC)
