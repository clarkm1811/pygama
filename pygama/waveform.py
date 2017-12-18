import numpy as np

class Waveform():

    def __init__(self, tier0, channel_info=None, ft_offset=0, ms_start_offset=0):
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

    #Methods so you can just address the object itself as an array
    def __len__(self):
        return len(self.data)
    def __getitem__(self, key):
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
