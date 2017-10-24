import numpy as np
import pandas as pd
from scipy.ndimage.filters import gaussian_filter1d
from scipy import signal

#Silence harmless warning you get using savgol on old LAPACK
import warnings
warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")

#Finds average baseline from first [samples] number of samples
def remove_baseline(waveform, bl_val=0):
    return (waveform - bl_val)

def savgol_filter(waveform, window_length=47, order=2):
  return signal.savgol_filter(waveform, window_length, order)

def trap_filter(waveform, rampTime=400, flatTime=200, decayTime=0.):
    """ Apply a trap filter to a waveform. """
    baseline = 0.
    decayConstant = 0.
    norm = rampTime
    if decayTime != 0:
        decayConstant = 1./(np.exp(1./decayTime) - 1)
        norm *= decayConstant

    trapOutput = np.linspace(0, len(waveform), num=len(waveform), dtype=np.double)
    fVector = np.linspace(0, len(waveform), num=len(waveform), dtype=np.double)

    fVector[0] = waveform[0] - baseline
    trapOutput[0] = (decayConstant+1.)*(waveform[0] - baseline)
    scratch = 0.
    for x in range(1,len(waveform)):
        scratch = waveform[x] - (
            waveform[x-rampTime] if x >= rampTime else baseline) - (
            waveform[x-flatTime-rampTime] if x >= (flatTime+rampTime) else baseline) + (
            waveform[x-flatTime-2*rampTime] if x >= (flatTime+2*rampTime) else baseline)
        if decayConstant != 0:
            fVector[x] = fVector[x-1] + scratch
            trapOutput[x] = trapOutput[x-1] + fVector[x] + decayConstant*scratch
        else:
            trapOutput[x] = trapOutput[x-1] + scratch

    # Normalize and resize output
    for x in range(2*rampTime+flatTime, len(waveform)):
        trapOutput[x-(2*rampTime+flatTime)] = trapOutput[x]/norm
    trapOutput.resize( (len(waveform) - (2*rampTime+flatTime)))
    return trapOutput

def asym_trap_filter(waveform,ramp=200,flat=100,fall=40,padAfter=False):
    """ Computes an asymmetric trapezoidal filter """
    trap = np.zeros(len(waveform))
    for i in range(len(waveform)-1000):
        w1 = ramp
        w2 = ramp+flat
        w3 = ramp+flat+fall
        r1 = np.sum(waveform[i:w1+i])/(ramp)
        r2 = np.sum(waveform[w2+i:w3+i])/(fall)
        if not padAfter:
            trap[i+1000] = r2 - r1
        else:
            trap[i] = r2 - r1
    return trap
