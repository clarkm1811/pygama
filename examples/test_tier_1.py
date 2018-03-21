import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

from pygama.processing import process_tier_0, process_tier_1
import pygama.decoders as dl

def main():
    # runNumber = 35366
    runNumber = 11510
    n_max = 50000

    process(runNumber, n_max=n_max)

def process(runNumber, n_max=5000):
    file_name = "t1_run{}.h5"

    runList = [runNumber]
    process_tier_1("", runList)


if __name__=="__main__":
    main()
