import os
import pandas as pd
import matplotlib.pyplot as plt

from pygama.processing import process_tier_0
import pygama.data_loader as dl

def main():
    process()
    plot()

    plt.show()

def plot():
    df = pd.read_hdf("t1_run11510.h5", key="ORGretina4M")

    plt.figure()

    for i, (index, row) in enumerate(df.iterrows()):
        plt.plot(row.waveform[0])
        if i > 5: break

def process():
    mjd_data_dir = os.path.join(os.getenv("DATADIR", "."), "mjd")
    raw_data_dir = os.path.join(mjd_data_dir,"raw")

    runList = [11510]

    mjd = dl.MJDPreamp_Decoder()
    hv = dl.ISegHV_Decoder()
    g4 = dl.Gretina4m_Decoder()

    mjd.chanList = [600,626,672]

    process_tier_0(raw_data_dir, runList, output_dir="", chanList=None, n_max=50000)


if __name__=="__main__":
    main()
