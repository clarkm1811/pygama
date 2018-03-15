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
    #plot_waveforms()

    plt.show()

def plot_baselines(draw_non_detectors=True):
    df_preamp =  pd.read_hdf("t1_run35366.h5", key="ORMJDPreAmpDecoderForAdc")
    plt.figure()

    # I thought it might be faster to get a separate df for each device, but it doesn't seem to be the case...
    # for an_id in df_preamp.device_id.unique():
    #     df_device = df_preamp[df_preamp.device_id == an_id]

    #     for a_ch in df_device.channel.unique():
    #         ts = df_device.timestamp[df_device.device_id == an_id][df_device.channel == a_ch].tolist()      # timestamp 
    #         ts_f = [ dt.datetime.fromtimestamp(t) for t in ts]                                              # formatted ts object
    #         v = df_device.adc[df_device.device_id == an_id][df_device.channel == a_ch].tolist()             # voltage reading

    #         if df_device.enabled[df_device.device_id == an_id][df_device.channel == a_ch].any():            # check that the channel is enabled before plotting
    #             detector_name = df_device.name[df_device.device_id == an_id][df_device.channel == a_ch].tolist()[0]
    #             if detector_name != '':
    #                 plt.plot(ts_f,v, marker='+',ls=":", label="{} ".format(detector_name))
    #             else:   # don't add a legent key unless we're looking at a named detector channel
    #                 plt.plot(ts_f,v, marker='+',ls=":")

    for an_id in df_preamp.device_id.unique():        
        for a_ch in df_preamp.channel.unique():
            ts = df_preamp.timestamp[df_preamp.device_id == an_id][df_preamp.channel == a_ch].tolist()      # timestamp 
            ts_f = [ dt.datetime.fromtimestamp(t) for t in ts]                                              # formatted ts object
            v = df_preamp.adc[df_preamp.device_id == an_id][df_preamp.channel == a_ch].tolist()             # voltage reading

            if df_preamp.enabled[df_preamp.device_id == an_id][df_preamp.channel == a_ch].any():            # check that the channel is enabled before plotting
                detector_name = df_preamp.name[df_preamp.device_id == an_id][df_preamp.channel == a_ch].any()
                if detector_name != '':
                    plt.plot(ts_f,v, marker='+',ls=":", label="{} ".format(detector_name))
                else:   # don't add a legent key unless we're looking at a named detector channel
                    if(draw_non_detectors):
                        plt.plot(ts_f,v, marker='+',ls=":")

    plt.legend()
    plt.show()






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
