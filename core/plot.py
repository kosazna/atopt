# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Union
from docplex.cp.model import *
import docplex.cp.utils_visu as visu
import matplotlib.pyplot as plt
from pylab import rcParams


def log_and_plot(sol: CpoSolveResult,
                 model_info: dict,
                 save_folder: Union[str, Path]):
    rcParams['figure.figsize'] = 10, 4

    model = model_info.get('model')
    ntrips = model_info.get('ntrips')
    nduties = model_info.get('nduties')
    duties = model_info.get('duties')
    trip2duty = model_info.get('trip2duty')
    breaks = model_info.get('breaks')
    min_start = model_info.get('min_start')
    max_end = model_info.get('max_end')

    bounds = sol.get_objective_bounds()
    status = sol.get_solve_status()

    save_loc = Path(save_folder)

    date_str = datetime.now().strftime('[%Y-%m-%d_%H-%M-%S]')
    out = save_loc.joinpath(f"{date_str}_{status}_{bounds[0]}.txt")
    sol_log = save_loc.joinpath(f"{date_str}_{status}_{bounds[0]}_SOLUTION.txt")

    sol.print_solution()

    with open(sol_log, 'w') as sol_log_file:
        driving_times = []
        for d in range(nduties):
            if sol[duties[d]]:
                print(f"\n> Duty {d} : {sol[duties[d]]}")
                sol_log_file.write(f"\n> Duty {d} : {sol[duties[d]]}")
                # print(cdt[d])
                _tdt = 0
                _ntrips = 0
                for t in range(ntrips):
                    if sol[trip2duty[(t, d)]]:
                        print(f"  - Trip {t} : {sol[trip2duty[(t, d)]]}")
                        sol_log_file.write(
                            f"\n  - Trip {t} : {sol[trip2duty[(t, d)]]}")
                        _tdt += model.durations[t]
                        _ntrips += 1
                print(f"\n  > Driving Time: {_tdt}, Trips: {_ntrips}")
                sol_log_file.write(
                    f"\n  > Driving Time: {_tdt}, Trips: {_ntrips}\n")
                driving_times.append(_tdt)
            else:
                driving_times.append(0)

            # print(cdt[d])
    sol.write(str(out))

    visu.timeline(
        f"{date_str}_{status}_{bounds[0]}", origin=min_start, horizon=max_end)

    for d in range(nduties):
        if sol[duties[d]]:
            visu.panel()
            visu.sequence(name=f"{duties[d].get_name()} ({driving_times[d]})",
                          intervals=[(sol.get_var_solution(trip2duty[(t, d)]), d, str(t)) for t in range(ntrips) if sol[trip2duty[(t, d)]]])
            visu.interval(sol.get_var_solution(breaks[d]), 'red', 'B')

    visu.show()
