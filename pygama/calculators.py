import numpy as np
import pandas as pd
from scipy.ndimage.filters import gaussian_filter1d
from scipy import signal

#Finds the maximum current ("A").  Current is calculated by convolution with a first-deriv. of Gaussian
def current_max(waveform, sigma=1):
  if sigma > 0:
      return np.amax(gaussian_filter1d(waveform, sigma=sigma, order=1))
  else:
      print("Current max requires smooth>0")
      exit(0)

#Finds average baseline from first [samples] number of samples
def avg_baseline(waveform, num_samples=500):
    return np.mean(waveform[:num_samples])

#Estimate t0
def t0_estimate(waveform, baseline=0):
    #find max to walk back from:
    maxidx = np.argmax(waveform)

    #find first index below or equal to baseline value walking back from the max
    t0_from_max = np.argmax(waveform[maxidx::-1] <= baseline)
    if t0_from_max == 0:
        print("warning: t0_from_max is zero")
        return 0
    return maxidx - t0_from_max

#Estimate arbitrary timepoint before max
def calc_timepoint(waveform, percentage=0.5, baseline=0):
    return np.argmax( waveform >= (percentage*(np.amax(waveform) - baseline) + baseline) )

#Calculate maximum of trapezoid -- no pride here
def trap_max(waveform):
    return np.amax(waveform)
