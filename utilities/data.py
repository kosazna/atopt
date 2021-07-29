# -*- coding: utf-8 -*-
import pandas as pd
from .funcs import time2minutes, weighted_trip_duration, calculate_trip_end_time

# Column names
trip = 'trip'
initial_depot = 'initial_depot'
final_depot = 'final_depot'
relief_point = 'relief_point'
time = 'time'
trip_duration = 'trip_duration'

start_time = 'start_time'
end_time = 'end_time'

class DataProvider:
    def __init__(self, filepath, route) -> None:
        self.filepath = filepath
        self.data = pd.read_excel(filepath, sheet_name=route).set_index(trip)
        self.constraints = pd.read_excel(filepath,
                                         sheet_name='driver constraints').set_index('constraint')
        self._preprocess()


    def _preprocess(self):
        self.data[start_time] = self.data[time].apply(time2minutes)
        self.data[trip_duration] = self.data.apply(lambda x: weighted_trip_duration(x[start_time], x[trip_duration]), axis=1)
        self.data[end_time] = self.data.apply(lambda x: calculate_trip_end_time(x[start_time], x[trip_duration]), axis=1)
