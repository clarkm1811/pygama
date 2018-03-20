import numpy as np
from .calculators import calc_timepoint
from .transforms import center

class Waveform():

    def __init__(self, waveform, time=None, full_sample_range=None):

        self.data = waveform
        self.time = time
        self.full_sample_range = full_sample_range


    def window_waveform(self, time_point=0.5, early_samples=200, num_samples=400):
        '''Windows waveform around a risetime percentage timepoint
            time_point: percentage (0-1)
            early_samples: samples to include before the calculated time_point
            num_samples: total number of samples to include
        '''

        #don't mess with the original data
        wf_copy = np.copy(self.data)

        #bl subtract
        wf_copy -= self.bl_int + np.arange(len(wf_copy))*self.bl_slope

        #Normalize the waveform by the calculated energy (noise-robust amplitude estimation)
        wf_norm = np.copy(wf_copy) / self.amplitude
        tp_idx = np.int( calc_timepoint(wf_norm, time_point, doNorm=False  ))

        self.windowed_wf = center(wf_copy, tp_idx, early_samples, num_samples-early_samples)
        self.window_length = num_samples

        return self.windowed_wf

    #Methods so you can just address the object itself as an array
    # def __len__(self):
    #     return len(self.data)
    # def __getitem__(self, key):
    #     return self.data[key]
    # def __setitem__(self, key, value):
    #     self.data[key] = value
