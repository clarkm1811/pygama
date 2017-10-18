import numpy as np
import pandas as pd
from scipy.ndimage.filters import gaussian_filter1d
from scipy import signal

#Finds average baseline from first [samples] number of samples
def remove_baseline(waveform, bl_val=0):
    return (waveform - bl_val)

def savgol_filter(waveform, window_length=47, order=2):
  return signal.savgol_filter(waveform, window_length, order)
