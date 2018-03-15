import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

from pygama.processing import process_tier_0
import pygama.data_loader as dl

def main():
    # process()
    plot_baselines()
    # plot_waveforms()

    plt.show()

def plot_baselines():
    df_preamp =  pd.read_hdf("t1_run35366.h5", key="ORMJDPreAmpDecoderForAdc")

    plt.figure()

    for device_num, device_id in enumerate(df_preamp.device_id.unique()):
        # print(device_id)
        df_device = df_preamp[df_preamp.device_id == device_id]

        baselines = np.zeros((16, len(df_device)))
        timestamps = np.zeros((len(df_device)))

        for i, (index, row) in enumerate(df_device.iterrows()):
            baselines[:,i] = row.adc
            enabled_mask = row.enabled.astype(np.bool)
            baselines[~enabled_mask,i] = np.nan
            timestamps[i] = row.timestamp

        timestamps = [ dt.datetime.fromtimestamp(t) for t in timestamps]

        for i in range(baselines.shape[0]):
            plt.plot(timestamps, baselines[i,:], marker='+', ls=":", label="Channel {}".format(i))
    # plt.legend()

def plot_waveforms():
    df_gretina = pd.read_hdf("t1_run35366.h5", key="ORGretina4MWaveformDecoder")


    plt.figure()

    #plot the first 5 waveforms
    for i, (index, row) in enumerate(df_gretina.iterrows()):
        plt.plot(row.waveform[0])
        if i >= 5: break

def process():
    mjd_data_dir = os.path.join(os.getenv("DATADIR", "."), "mjd")
    raw_data_dir = os.path.join(mjd_data_dir,"raw")

    runList = [35366]

    mjd = dl.MJDPreamp_Decoder()
    hv = dl.ISegHV_Decoder()
    g4 = dl.Gretina4m_Decoder()

    mjd.chanList = [600,626,672]

    process_tier_0(raw_data_dir, runList, output_dir="", chanList=None)


if __name__=="__main__":
    main()
