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

def cost(params, data_by_animal):
    [hp_order, hp_f, hp_apps, lp_order, lp_f, lp_apps, env_thr_pct, ] = params
    hp_order = int(hp_order)
    hp_apps = int(hp_apps)
    lp_order = int(lp_order)
    lp_apps = int(lp_apps)
    consumed_vols = []
    licks = []
    for (animal, data) in data_by_animal.items():
        if animal in ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']: continue
        fs = data['fs']
        trace = data['cap_data']
    
        # 1a) 8–12 Hz band-pass
        bh, ah = scs.butter(hp_order, hp_f, btype='high', fs=fs)
        bl, al = scs.butter(lp_order, lp_f, btype='low', fs=fs)
        filtered_data = scs.filtfilt(bh, ah, trace)
        filtered_data = scs.filtfilt(bl, al, filtered_data)
        filtered_data = [scs.filtfilt(bh, ah, filtered_data) for _ in range(hp_apps)][-1]
        filtered_data = [scs.filtfilt(bl, al, filtered_data) for _ in range(lp_apps)][-1]
    
        # 1b) Analytic signal → envelope
        env = np.abs(scs.hilbert(filtered_data))
    
        # 2) Envelope thresholding
        env_thr  = env_thr_pct * np.max(env)
        env_mask = env > env_thr
    
        # 3) Find where we go from above → below the raw_thr
        downs = np.where((trace[:-1] > trace[1:]))[0] + 1
    
        # 4a) Gate by envelope mask
        candidates = [i for i in downs if env_mask[i]]
    
        # 4b) Enforce at least ~80 ms (0.08 s) between licks (mice shouldn't be licking faster than that)
        min_dist = int(0.08 * fs)
        lick_idxs = []
        for idx in candidates:
            if not lick_idxs or (idx - lick_idxs[-1]) > min_dist:
                lick_idxs.append(idx)
    
        # Convert to timestamps
        lick_times = data['time_data'][lick_idxs]

        # Store everything in the dict that we'll use to save an h5
        data['lick_times'] = lick_times
        data['lick_indices'] = lick_idxs
        num_licks = len(lick_times)
        data['num_licks'] = num_licks

        # Build the lists for correlation
        consumed_vols.append(data['consumed_vol'])
        licks.append(data['num_licks'])
        
    res = pearsonr(consumed_vols, licks)
    return (1-res.statistic) # Maximize r

if __name__ == "__main__":
    # freeze_support()
    # Load the data by filename
    recording_filename = 'raw_data_2025-04-24_11-39-40.h5'

    # Determine what date/time the recording was started (for
    # use in saving figures later with the proper date/time)
    recording_datetime = os.path.splitext(recording_filename)[0]
    recording_datetime = recording_datetime.split('raw_data_')[1]

    if not os.path.exists('Filtered Data Figures'):
        os.mkdir('Filtered Data Figures')
    if not os.path.exists('Recording Figures'):
        os.mkdir('Recording Figures')
    layout = pd.read_csv('layouts/test_layout.csv', header=None, index_col=0)
    layout.index.name = 'Sensor'
    layout.columns = ['Animal ID']
    sensor_animal_map = layout

    data_dict = {}
    # We only expect up to 3 nested levels based on the DataRecording notebook
    with h5py.File(recording_filename, 'r') as h5f:
        for k,v in h5f.items():
            data_dict[k] = {} if isinstance(v, h5py._hl.group.Group) else v
            if not isinstance(data_dict[k], dict): continue
            for k2,v2 in v.items():
                data_dict[k][k2] = {} if isinstance(v2, h5py._hl.group.Group) else v2[()]
                if not isinstance(data_dict[k][k2], dict): continue
                for k3,v3 in v2.items():
                    data_dict[k][k2][k3] = v3[()]
                #data_dict[k][k2] = v2[()]

    # Loop through all boards and sensors and truncate at start_time and stop_time, then subtract the first time point from the data
    for board_id, board_data in data_dict.items():
        for sensor_id, sensor_data in board_data.items():
            if 'start_time' not in sensor_data.keys():
                sensor_data['fs'] = len(sensor_data['cap_data'])/(sensor_data['time_data'][-1] - sensor_data['time_data'][0])
                continue
            else:
                start_idx = np.argmin(np.abs(sensor_data['time_data'] - sensor_data['start_time']))
                stop_idx = np.argmin(np.abs(sensor_data['time_data'] - sensor_data['stop_time']))
                
                if sensor_data['stop_time'] - sensor_data['start_time'] <= 1000:
                    print(f"{board_id} {sensor_id} likely had a false start/stop, the stop time is less than 1000 seconds after start")

                sensor_data['time_data'] = sensor_data['time_data'][start_idx:stop_idx] - sensor_data['start_time']
                sensor_data['cap_data'] = sensor_data['cap_data'][start_idx:stop_idx]
                sensor_data['fs'] = (stop_idx - start_idx)/(sensor_data['stop_time'] - sensor_data['start_time'])
                
                if 'stop_vol' in sensor_data.keys():
                    sensor_data['consumed_vol'] = sensor_data['start_vol'] - sensor_data['stop_vol']

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

    data_by_animal['A7']['time_data'] = data_by_animal['A7']['time_data'][1000:]
    data_by_animal['A7']['cap_data'] = data_by_animal['A7']['cap_data'][1000:]

    for (animal, data) in data_by_animal.items():
        data['time_data'] = data['time_data'][:-250]
        data['cap_data'] = data['cap_data'][:-250]

    # Optimizing the filter
    # Define bounds on the various parameters to be optimized
    # Order: hp_order, hp_f, hp_apps, lp_order, lp_f, lp_apps, env_thr_pct
    bounds = [[1,10], [1,10], [1,10], [1,10], [10,20], [1,10], [0.05, 0.95]]
    sol = sco.differential_evolution(cost, args=[data_by_animal], integrality=[1, 0, 1, 1, 0, 1, 0], bounds=bounds, workers=4, popsize=4)

    print(f"sol: {sol}")
    print(f"sol.x: {sol.x}")
