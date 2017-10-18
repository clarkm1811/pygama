from david_decoder cimport *

from libc.stdio cimport *
from libc.string cimport *
from libc.stdint cimport *

from cython.view cimport array as cvarray
cimport numpy as np
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd

update_freq = 2000

def ProcessTier0( filenamestr, n_max=np.inf):
  cdef MJDetInfo  detInfo[100];
  cdef MJRunInfo  runInfo;
  cdef FILE       *f_in
  cdef int nDets

  fname = filenamestr.encode('utf-8')

  f_in = fopen(fname, "r")
  if f_in == NULL:
    print("Couldn't file the file %s" % fname)
    exit(0)

  strncpy(runInfo.filename, fname, 256);
  runInfo.argc = 0;
  runInfo.argv = NULL;

  #read run info, channel settings, etc from header
  nDets = decode_runfile_header(f_in, detInfo, &runInfo);

  dataIdG = runInfo.dataIdG;
  for i in range(runInfo.idNum):
    if (strstr(runInfo.decoder[i], "ORRunDecoderForRun")):
      dataIdRun = runInfo.dataId[i];
      printf("dataIdRun = %d %s %d\n", dataIdRun, runInfo.decoder[i], i);

  printf("dataIdRun = %d\n", dataIdRun);

  cdef np.ndarray[int16_t, ndim=1, mode="c"] narr = np.zeros((2018), dtype='int16')
  cdef int16_t* sig_ptr
  cdef int16_t [:] sig_arr

  #now read the file in as a bytearray
  n=0
  res = 0
  cdef uint64_t timestamp
  cdef uint32_t energy
  cdef uint32_t evtdat[20000];
  cdef uint16_t channel;

  times = []
  energies = []
  appended_data = []
  while (res >=0 and n < n_max):

    res = get_next_event(f_in, evtdat, dataIdRun, dataIdG)
    sig_ptr = parse_event_data(evtdat, &timestamp, &energy, &channel)

    sig_arr = <int16_t [:2018]> sig_ptr

    if res ==0: continue

    if (n%update_freq == 0): print("Tier 0 processing: {}".format(n))

    times.append(timestamp)
    energies.append(energy)
    # plt.plot(np.copy(narr))
    data = {}
    data["energy"] = energy
    data["timestamp"] = timestamp
    data["channel"] = channel
    data["waveform"] = [np.copy(sig_arr)]

    #avg basel

    dr = pd.DataFrame(data, index=[n])

    appended_data.append(dr)
    n+=1;

  fclose(f_in);
  appended_data = pd.concat(appended_data, axis=0)

  appended_data.to_hdf('t0_run%d.h5' %runInfo.runNumber, key="data", mode='w', data_columns=['energy', 'channel', 'timestamp'],)
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

      # print("-->{}".format(fn))
      for (arg, val) in args.items():
        # if output == "blrm_wf": print( "    checking if {} is in {}".format(val, self.param_dict.keys() ))
        if val in self.param_dict.keys():
          # print("    getting {} to {} from dict...".format(val, self.param_dict[val]))
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
