from david_decoder cimport *

from libc.stdio cimport *
from libc.string cimport *
from libc.stdint cimport *

from cython.view cimport array as cvarray
cimport numpy as np
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd

from future.utils import iteritems

from ._header_parser import *

WF_LEN = 2018


#Silence harmless warning about saving numpy array to hdf5
import warnings
warnings.filterwarnings(action="ignore", module="pandas", message="^\nyour performance")

update_freq = 2000

def ProcessTier0( filenamestr, n_max=np.inf):
  cdef FILE       *f_in
  cdef int nDets

  #parse the header (in python)
  reclen, reclen2, headerDict = parse_header(filenamestr)

  fname = filenamestr.encode('utf-8')
  f_in = fopen(fname, "r")
  if f_in == NULL:
    print("Couldn't file the file %s" % fname)
    exit(0)

  #skip the header
  fseek(f_in, reclen*4, SEEK_SET)

  #pull out important header info for event processing
  dataIdRun = get_data_id(headerDict, "ORRunModel", "Run")
  dataIdG   = get_data_id(headerDict, "ORGretina4M", "Gretina4M")
  runNumber = get_run_number(headerDict)

  #read all header info into a single, channel-keyed data frame for saving
  headerinfo = get_header_dataframe_info(headerDict)
  df_channels = pd.DataFrame(headerinfo)
  df_channels.set_index("channel", drop=False, inplace=True)


  cdef np.ndarray[int16_t, ndim=1, mode="c"] narr = np.zeros((WF_LEN), dtype='int16')
  cdef int16_t* sig_ptr
  cdef int16_t [:] sig_arr

  n=0
  res = 0
  cdef uint64_t timestamp
  cdef uint32_t energy
  cdef uint32_t evtdat[20000];
  cdef uint16_t channel;
  cdef int card
  cdef int crate;

  times = []
  energies = []
  appended_data = []
  while (res >=0 and n < n_max):

    res = get_next_event(f_in, evtdat, dataIdRun, dataIdG, &card, &crate)
    sig_ptr = parse_event_data(evtdat, &timestamp, &energy, &channel)
    if res ==0: continue
    if (n%update_freq == 0): print("Tier 0 processing: {}".format(n))

    crate_card_chan = (crate << 12) + (card << 4) + channel

    sig_arr = <int16_t [:WF_LEN]> sig_ptr
    times.append(timestamp)
    energies.append(energy)
    # plt.plot(np.copy(narr))
    data = {}
    data["energy"] = energy
    data["timestamp"] = timestamp
    data["channel"] = crate_card_chan
    data["waveform"] = [np.copy(sig_arr)]

    dr = pd.DataFrame(data, index=[n])

    appended_data.append(dr)
    n+=1;

  fclose(f_in);
  appended_data = pd.concat(appended_data, axis=0)

  appended_data.to_hdf('t0_run{}.h5'.format(runNumber), key="data", mode='w', data_columns=['energy', 'channel', 'timestamp'],)
  df_channels.to_hdf('t0_run{}.h5'.format(runNumber),   key="channel_info", mode='a', data_columns=True,)
  return appended_data



def ProcessTier1(runNumber, processorList):
  #load in tier 0 data
  df = pd.read_hdf('t0_run%d.h5' %runNumber,key="data")
  appended_data = []
  for i, (index, row) in enumerate(df.iterrows()):
    if (i%update_freq == 0): print("Tier 1 processing: {}/{}".format( i, df.shape[0]))
    #convert the stored waveform (which is int16) to a float, throw it to the processorList
    # print("\n\nTier 1 processing: {}/{}".format( i, df.shape[0]))
    processorList.Reset( row["waveform"].astype('float32') )

    paramDict = processorList.Process(row)
    dr = pd.DataFrame(paramDict, index=[index])
    appended_data.append(dr)
  appended_data = pd.concat(appended_data, axis=0)
  appended_data.to_hdf('t1_run%d.h5' % runNumber, key="data", format='table', mode='w', data_columns=True)
  return appended_data

class TierOneProcessorList():
  def __init__(self):
    self.list = []
    self.waveform_dict = {}
    self.param_dict = {}
    self.t0_list = []

  def Reset(self, waveform):
    self.param_dict = {}
    self.waveform_dict = {"waveform":waveform}

  def Process(self, t0_row):
    for name in self.t0_list:
      self.param_dict[name] = t0_row[name]

    for (type, input, output, fn, perm_args) in self.list:
      #check args list for string vals which match keys in param dict
      args = perm_args.copy() #copy we'll actually pass to the function

      for (arg, val) in iteritems(args):
        if val in self.param_dict.keys():
          args[arg] = self.param_dict[val]

      if input is None: input = "waveform"
      input = self.waveform_dict[input]

      if output is None:
        fn(input, args)

      if type == "transform":
        self.waveform_dict[output] = fn(input, **args)

      elif type == "calculator":
        self.param_dict[output] = fn(input, **args)
        # print("    setting {} to {}...".format(output, self.param_dict[output]))

    return self.param_dict

  def AddTransform(self, function, args={}, input_waveform=None, output_waveform=None):
    self.list.append( ("transform", input_waveform, output_waveform, function, args   ) )

  def AddCalculator(self, function, args={}, input_waveform=None,  output_name=None):
    self.list.append( ("calculator", input_waveform, output_name, function, args   ) )

  def AddFromTier0(self, name):
    self.t0_list.append(name)
