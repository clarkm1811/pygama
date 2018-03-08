import numpy as np
from .calculators import calc_timepoint
from .transforms import center

class Waveform():

    def __init__(self, tier0, channel_info=None, ft_offset=0, ms_start_offset=0, amplitude=1, bl_slope=0, bl_int=0, t0_estimate=None):
        if type(tier0["waveform"]) is list:
            self.data = tier0["waveform"][0].astype('float32')
        else:
            self.data       = tier0["waveform"].astype('float32')

        self.channel    = tier0["channel"]
        self.timestamp  = tier0["timestamp"]
        self.sample_period = 10 #ns

        self.multirate_sum = 1
        self.ft_cnt = 0
        self.ms_start_offset = ms_start_offset

        self.amplitude = amplitude
        self.bl_slope = bl_slope
        self.bl_int = bl_int
        self.t0_estimate = t0_estimate

        if channel_info is not None:
            self.prere_cnt = channel_info["Prerecnt"]
            self.ft_cnt = channel_info["FtCnt"]  + ft_offset
            self.postre_cnt = channel_info["Postrecnt"]
            self.multirate_sum = channel_info["multirate_sum"]
            self.multirate_div = channel_info["multirate_div"]

        self.idx_re = 0 #"rising edge" -- where full-sampling kicks in
        self.idx_ft = len(self.data) - self.ft_cnt -1  # "flat top" -- where full-sampling eds

    def time(self):
        time_full  = np.arange(self.idx_ft)*self.sample_period
        time_multi = np.arange(self.ft_cnt+1)*self.sample_period*self.multirate_sum + time_full[-1] + 0.5*(self.sample_period*self.multirate_sum + self.ms_start_offset)

        return np.concatenate((time_full, time_multi))

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
