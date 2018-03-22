import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

from pygama.processing import process_tier_0
import pygama.decoders as dl

def main():
    # runNumber = 35366
    runNumber = 11510
    n_max = 5000

    process(runNumber, n_max=n_max)
    # plot_baselines("t1_run{}.h5".format(runNumber))
    plot_waveforms("t1_run{}.h5".format(runNumber), num_waveforms=500)

    plt.show()

def plot_baselines(file_name, draw_non_detectors=True):
    df_preamp =  pd.read_hdf(file_name, key="ORMJDPreAmpDecoderForAdc")
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

def plot_waveforms(file_name, num_waveforms=5):
    df_gretina = pd.read_hdf(file_name, key="ORGretina4MWaveformDecoder")

    g4 = dl.Gretina4MDecoder(file_name)

    plt.figure()
    plt.xlabel("Time [ns]")
    plt.ylabel("ADC [arb]")

    # from timeit import default_timer as timer
    # start = timer()

    for i, (index, row) in enumerate(df_gretina.iterrows()):
        wf = g4.parse_event_data(row)
        plt.plot(wf.time, wf.data)

        # try:
        #     waveform = g4.parse_event_data(row)
        #     plt.plot(time, waveform)
        # except Exception as e:
        #     print(e)
        #     wf_data = row["waveform"][0].astype('float_')
        #     plt.plot(wf_data)
        #     # plt.plot()
        if i >=num_waveforms : break
    # end = timer()
    # print("Elapsed time: {}".format(end - start))

def process(runNumber, n_max=5000):
    mjd_data_dir = os.path.join(os.getenv("DATADIR", "."), "mjd")
    raw_data_dir = os.path.join(mjd_data_dir,"raw")

    runList = [runNumber]
    #
    # mjd = dl.MJDPreamp_Decoder()
    # hv = dl.ISegHV_Decoder()
    # g4 = dl.Gretina4m_Decoder()

    # mjd.chanList = [600,626,672]

    process_tier_0(raw_data_dir, runList, output_dir="", chanList=None, n_max=n_max)


if __name__=="__main__":
    main()
