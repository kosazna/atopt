# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import docplex.cp.utils_visu as visu
import matplotlib.pyplot as plt
from docplex.cp.model import *
from pylab import rcParams


def log_and_plot(sol: CpoSolveResult,
                 model_info: dict,
                 save_folder: Union[str, Path],
                 has_breaks: Optional[bool] = True,
                 has_traffic: Optional[bool] = True):
    rcParams['figure.figsize'] = 10, 4

    model = model_info.get('model')
    ntrips = model_info.get('ntrips')
    nduties = model_info.get('nduties')
    duties = model_info.get('duties')
    trip2duty = model_info.get('trip2duty')
    breaks = model_info.get('breaks')
    nbuses = model_info.get('nbuses')
    min_start = model_info.get('min_start')
    max_end = model_info.get('max_end')

    status = sol.get_solve_status()

    save_loc = Path(save_folder)

    total_duties = 0

    try:
        for d in range(nduties):
            if sol[duties[d]]:
                total_duties += 1

        date_str = datetime.now().strftime('[%Y-%m-%d %H-%M]')
        out = save_loc.joinpath(
            f"{date_str}-R-{status}-{total_duties}-[Breaks={bool(breaks)}-Traffic={has_traffic}-Buses={nbuses}].txt")
        sol_log = save_loc.joinpath(
            f"{date_str}-S-{status}-{total_duties}-[Breaks={bool(breaks)}-Traffic={has_traffic}-Buses={nbuses}].txt")
        sol_excel = save_loc.joinpath(
            f"{date_str}-S-{status}-{total_duties}-[Breaks={bool(breaks)}-Traffic={has_traffic}-Buses={nbuses}].xlsx")

        sol.print_solution()

        buses = CpoStepFunction()

        model.data['duty'] = ''

        with open(sol_log, 'w') as sol_log_file:
            driving_times = []
            for d in range(nduties):
                if sol[duties[d]]:
                    print(f"\n> Duty {d} : {sol[duties[d]]}")
                    sol_log_file.write(f"\n> Duty {d} : {sol[duties[d]]}")
                    _tdt = 0
                    _ntrips = 0
                    for t in range(ntrips):
                        if sol[trip2duty[(t, d)]]:
                            model.data.loc[t, 'duty'] = d
                            bus_td = sol.get_var_solution(trip2duty[(t, d)])
                            buses.add_value(bus_td.get_start(), bus_td.get_end(), 1)
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

        model.data.to_excel(sol_excel)
        sol.write(str(out))

        visu.timeline(f"{date_str}-F-{status}-{total_duties}-[Breaks={bool(breaks)}-Traffic={has_traffic}-Buses={nbuses}]",
                    origin=min_start,
                    horizon=max_end)

        for d in range(nduties):
            if sol[duties[d]]:
                visu.panel()
                visu.sequence(name=f"{duties[d].get_name()} ({driving_times[d]})",
                            intervals=[(sol.get_var_solution(trip2duty[(t, d)]), d, str(t)) for t in range(ntrips) if sol[trip2duty[(t, d)]]])
                if has_breaks:
                    visu.interval(sol.get_var_solution(breaks[d]), 'red', 'B')

        visu.panel(name="Buses")
        visu.function(segments=buses, style='area')

        visu.show()
    except KeyError as e:
        print(f" -- NO SOLUTION -- [KeyError: {e}]")
