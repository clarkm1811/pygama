import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

from pygama.processing import process_tier_0
import pygama.decoders as dl

#path to the DaqTest_Run1 file
lanl_data_dir = os.path.join(os.getenv("DATADIR", "."), "lanl")
raw_data_dir = os.path.join(lanl_data_dir,"raw")

def main():
    runNumber = 1
    n_max = np.inf #max number of events to decode

    # process_t0(runNumber, n_max=n_max)
    plot_waveforms(runNumber, num_waveforms=50)
    plt.show()

def plot_waveforms(runNumber, num_waveforms=5):
    file_name = "t1_run{}.h5".format(runNumber)

    dcdr = dl.SIS3302Decoder(file_name)
    df_events = pd.read_hdf(file_name, key=dcdr.decoder_name)

    plt.figure()
    plt.xlabel("Time [ns]")
    plt.ylabel("ADC [arb]")

    for i, (index, row) in enumerate(df_events.iterrows()):
        wf = dcdr.parse_event_data(row)
        plt.plot(wf.data)
        if i >=num_waveforms : break

def process_t0(runNumber, n_max=5000):
    lanl_data_dir = os.path.join(os.getenv("DATADIR", "."), "lanl")
    raw_data_dir = os.path.join(lanl_data_dir,"raw")

    runList = [runNumber]
    process_tier_0(raw_data_dir, runList, output_dir="", chanList=None, n_max=n_max)

# def process_t1(runNumber, n_max=5000):
#     file_name = "t1_run{}.h5".format(runNumber)
#
#     runList = [runNumber]
#     process_tier_0(raw_data_dir, runList, output_dir="", chanList=None, n_max=n_max)


if __name__=="__main__":
    main()
