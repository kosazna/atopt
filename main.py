# -*- coding: utf-8 -*-
from atopt.utilities import *
from atopt.core.initial import Insertions
from atopt.core.sdcsp import single_depot_CSP
from atopt.core.plot import log_and_plot
from docplex.cp.model import *
from pathlib import Path
import argparse


my_parser = argparse.ArgumentParser()
my_parser.add_argument('-t', '--trips', action='store', type=int)
my_parser.add_argument('-d', '--duties', action='store', type=int)
my_parser.add_argument('-l', '--limit', action='store', type=int, default=120)
my_parser.add_argument('-r', '--route', action='store', type=str, default='910')
my_parser.add_argument('-f', '--filepath', action='store',
                       type=str, default='Model Data.xlsx')
my_parser.add_argument('-s', '--save', action='store', type=str)
my_parser.add_argument('-a', '--adjust', action='store', type=int, default=1)


if __name__ == "__main__":
    args = my_parser.parse_args()

    ROUTE = args.route
    TIMELIMIT = args.limit
    DATAFILE = args.filepath
    ADJUST = bool(args.adjust)

    d = DataProvider(filepath=DATAFILE, route=ROUTE, adjust_for_traffic=ADJUST)

    model = CSPModel(d)
    model.build_model()

    # initial = Insertions(model)
    # initial.solve()

    if args.trips is None:
        NTRIPS = len(model.trips)
    else:
        model.trips = model.trips[:args.trips]
        NTRIPS = len(model.trips)

    if args.duties is None:
        NDUTIES = 10
    else:
        NDUTIES = args.duties

    if args.save is None:
        SAVELOC = Path.cwd().joinpath('sols')

        if not SAVELOC.exists():
            SAVELOC.mkdir(parents=True, exist_ok=True)
    else:
        SAVELOC = Path(args.save)

    cp_model, model_info = single_depot_CSP(model=model, nduties=NDUTIES)
    cpsol = cp_model.solve(TimeLimit=TIMELIMIT)

    log_and_plot(sol=cpsol, model_info=model_info, save_folder=SAVELOC)
