# File Name: individual_dataset_filtering.py
# Author: Christopher Parker
# Created: Wed May 21, 2025 | 11:43P EDT
# Last Modified: Wed May 21, 2025 | 11:51P EDT

"""Since we may sometimes want to run the analysis for a raw datafile again,
I've made a succinct script to do that (using the same function as the 
automatic analysis, imported from data_analysis.py)"""

import os
import sys
import h5py
import pandas as pd
from data_analysis import filter_data

layout = pd.read_csv('layouts/default_layout.csv', index_col=0, header=None)

# Get the raw datafile path from the user as a CLI arg
raw_file = sys.argv[1]
try:
    raw_filename = os.path.split(raw_file)[1]
    raw_filepath = raw_file
except IndexError:
    raw_filename = raw_file
    raw_filepath = raw_file
filtered_filename = 'filtered'+raw_filename[3:]
raw_h5f = h5py.File(raw_filepath, 'r')
filtered_h5f = h5py.File(filtered_filename, 'w')

filter_data(raw_h5f, filtered_h5f, layout, f'logs/{raw_filename[:-3]}.log')
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

