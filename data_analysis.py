# File Name: data_analysis.py
# Author: Christopher Parker
# Created: Thu May 08, 2025 | 11:48P EDT
# Last Modified: Thu May 08, 2025 | 01:48P EDT

"""Contains the data analysis functions to be called when the user stops
a recording."""


import os
from io import StringIO
import h5py
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.signal as scs
import scipy.optimize as sco
from scipy.stats import pearsonr
import ipywidgets as widgets

def filter_data(raw_h5f, filtered_h5f, sensor_animal_map):

    data_dict = {}
    # We only expect up to 3 nested levels based on the DataRecording notebook
    for k,v in raw_h5f.items():
        data_dict[k] = {} if isinstance(v, h5py._hl.group.Group) else v
        if not isinstance(data_dict[k], dict): continue
        for k2,v2 in v.items():
            data_dict[k][k2] = (
                {} if isinstance(v2, h5py._hl.group.Group) else v2[()]
            )
            if not isinstance(data_dict[k][k2], dict): continue
            for k3,v3 in v2.items():
                data_dict[k][k2][k3] = v3[()]

    # Loop through all boards and sensors and truncate at start_time and
    # stop_time, then subtract the first time point from the data
    for board_id, board_data in data_dict.items():
        for sensor_id, sensor_data in board_data.items():
            if 'start_time' not in sensor_data.keys():
                sensor_data['fs'] = (
                        len(sensor_data['cap_data']) /
                        (
                            sensor_data['time_data'][-1] -
                                sensor_data['time_data'][0]
                        )
                )
                if 'stop_vol' in sensor_data.keys():
                    sensor_data['consumed_vol'] = (
                        sensor_data['start_vol'] - sensor_data['stop_vol']
                    )
                continue
            else:
                start_idx = np.argmin(
                    np.abs(
                        sensor_data['time_data'] - sensor_data['start_time']
                    )
                )
                stop_idx = np.argmin(
                    np.abs(
                        sensor_data['time_data'] - sensor_data['stop_time']
                    )
                )
                
                if (
                    sensor_data['stop_time']-sensor_data['start_time'] <= 1000
                ):
                    print(
                        f"{board_id} {sensor_id} likely had a false start/stop"
                        ", the stop time is less than 1000 seconds after start"
                    )

                sensor_data['time_data'] = (
                    sensor_data['time_data'][start_idx:stop_idx] -
                        sensor_data['start_time']
                )
                sensor_data['cap_data'] = (
                    sensor_data['cap_data'][start_idx:stop_idx]
                )
                sensor_data['fs'] = (
                    (stop_idx - start_idx) /
                        (sensor_data['stop_time'] - sensor_data['start_time'])
                )
                
                if 'stop_vol' in sensor_data.keys():
                    sensor_data['consumed_vol'] = (
                        sensor_data['start_vol'] - sensor_data['stop_vol']
                    )

    # Reorganize the data to be by animal ID, agnostic wrt any board/sensor numbering
    data_by_animal = {}
    for idx,row in sensor_animal_map.iterrows():
        sensor = row.name
        animal = row.item()
        # We need to determine which FT232H was used for the recordings
        if sensor in [1,2,3,7,8,9]:
            board_id = 'board_FT232H0'
        elif sensor in [4,5,6,10,11,12]:
            board_id = 'board_FT232H1'
        elif sensor in [13,14,15,19,20,21]:
            board_id = 'board_FT232H2'
        elif sensor in [16,17,18,22,23,24]:
            board_id = 'board_FT232H3'
        try:
            data_by_animal[animal] = data_dict[board_id][f"sensor_{sensor}"]
        except KeyError as e:
            print(f"Missing key in data_dict: {e}")

    # Trying a mix of using raw trace and Hilbert envelope to find licks
    for (animal, data) in data_by_animal.items():
        # if animal in ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']: continue
        # if animal != 'A9': continue
        fs = data['fs']
        trace = data['cap_data']

        # 8–12 Hz band-pass applied as high- then low-pass
        bh, ah = scs.butter(4, 8, btype='high', fs=fs)
        bl, al = scs.butter(8, 12, btype='low', fs=fs)
        filtered_data = scs.filtfilt(bh, ah, trace)
        filtered_data = scs.filtfilt(bl, al, filtered_data)
        filtered_data = [scs.filtfilt(bh, ah, filtered_data) for _ in range(6)][-1]
        filtered_data = [scs.filtfilt(bl, al, filtered_data) for _ in range(6)][-1]

        # Convert filtered data to Hilbert envelope
        env = np.abs(scs.hilbert(filtered_data))

        # Thresholding with Hilbert envelope
        env_thr  = 0.261 * np.max(env)
        env_mask = env > env_thr

        # Where the value decreases from one point to the next
        downs = np.where((trace[:-1] > trace[1:] + 15))[0] + 1

        # Apply envelope mask
        candidates = [i for i in downs if env_mask[i]]

        # At least ~80 ms (0.08 s) between licks (mice shouldn't be licking faster than that)
        min_dist = int(0.08 * fs)
        lick_idxs = []
        for idx in candidates:
            if not lick_idxs or (idx - lick_idxs[-1]) > min_dist:
                lick_idxs.append(idx)

        # At most 500 ms between licks. This is probably overly permissive,
        # but we need some way to say 
        # "it's impossible to tell if a single lick is really a lick"
        # convert to timestamps
        max_dist = int(0.5 * fs)
        lick_idxs_ = []
        for i, idx in enumerate(lick_idxs):
            # Only check to the right on the first loop and left on the last:
            if i == 0: 
                ir = lick_idxs[i+1]
                ir2 = lick_idxs[i+2]
                if np.abs(idx - ir) < max_dist and np.abs(idx - ir2) < 2*max_dist:
                    lick_idxs_.append(idx)
                continue
            if i == len(lick_idxs)-1: 
                il = lick_idxs[i-1]
                il2 = lick_idxs[i-2]
                if np.abs(idx - il) < max_dist and np.abs(idx - il2) < 2*max_dist:
                    lick_idxs_.append(idx)
                continue
            il = lick_idxs[i-1]
            ir = lick_idxs[i+1]
            if np.abs(idx - il) < max_dist and np.abs(idx - ir) < max_dist:
                lick_idxs_.append(idx)
                continue
            elif np.abs(idx - il) < max_dist:
                if i == 1: continue # Make sure we have 2 points to the left
                il2 = lick_idxs[i-2]
                if np.abs(idx - il2) < 2*max_dist:
                    lick_idxs_.append(idx)
                continue
            elif np.abs(idx - ir) < max_dist:
                if i >= len(lick_idxs)-2: continue # There must be 2 points right
                ir2 = lick_idxs[i+2]
                if np.abs(idx - ir2) < 2*max_dist:
                    lick_idxs_.append(idx)
                continue
        lick_idxs = lick_idxs_
        lick_times = np.array(lick_idxs) / fs
        data['lick_times'] = lick_times
        data['lick_indices'] = lick_idxs

        # print(f"lick_times: {lick_times}")
        num_licks = len(lick_times)
        data['num_licks'] = num_licks

        grp = filtered_h5f.create_group(animal)
        grp.create_dataset('lick_times', data=lick_times)
        grp.create_dataset('lick_indices', data=lick_idxs)

#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#                                 MIT License                                 #
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#
#     Copyright (c) 2022 Christopher John Parker <parkecp@mail.uc.edu>        #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the "Software"),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

