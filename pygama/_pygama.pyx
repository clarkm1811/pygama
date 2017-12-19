from david_decoder cimport *

from libc.stdio cimport *
from libc.string cimport *
from libc.stdint cimport *

from cython.view cimport array as cvarray
cimport numpy as np
import numpy as np
# import matplotlib.pyplot as plt
import os, re

import pandas as pd

from future.utils import iteritems

from ._header_parser import *
from .utils import update_progress

WF_LEN = 2018

#Silence harmless warning about saving numpy array to hdf5
import warnings
warnings.filterwarnings(action="ignore", module="pandas", message="^\nyour performance")

update_freq = 2000

def ProcessTier0( filename, output_file_string = "t1", n_max=np.inf, verbose=False, output_dir=None, min_signal_thresh=0):
  '''
  Reads in "raw," or "tier 0," Orca data and saves to a hdf5 format using pandas
    filename: path to an orca data file
    output_file_string: output file name will be <output_file_string>_run<runNumber>.h5
    n_max: maximum number of events to process (useful for debugging)
    verbose: spits out a progressbar to let you know how the processing is going
    min_signal_thresh: multiple of noise std required for wf_max to be above to save a signal
  '''

  cdef FILE       *f_in
  cdef int file_size

  directory = os.path.dirname(filename)
  output_dir = os.getcwd() if output_dir is None else output_dir

  #parse the header (in python)
  reclen, reclen2, headerDict = parse_header(filename)

  f_in = fopen(filename.encode('utf-8'), "r")
  if f_in == NULL:
    print("Couldn't file the file %s" % filename)
    exit(0)
  #figure out the total size

  fseek(f_in, 0L, SEEK_END);
  file_size = ftell(f_in);
  rewind(f_in);

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
  active_channels = df_channels["channel"].values

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
  cdef uint16_t board_id;

  appended_data = []
  print("Beginning Tier 0 processing of file {}...".format(filename))

  board_id_map = {}

  # import matplotlib.pyplot as plt
  # plt.ion()
  # plt.figure()

  while (res >=0 and n < n_max):
    #
    if verbose and n%100==0: update_progress( float(ftell(f_in))/ file_size)

    res = get_next_event(f_in, evtdat, dataIdRun, dataIdG, &card, &crate, &board_id)
    sig_ptr = parse_event_data(evtdat, &timestamp, &energy, &channel)
    if res ==0: continue
    #TODO: this is totally mysterious to me.  why bitshift 9??
    crate_card_chan = (crate << 9) + (card << 4) + (channel)

    if crate_card_chan not in active_channels:
      print("Data read for channel {}: not an active channel".format(crate_card_chan))
      continue

    if not board_id_map.has_key(crate_card_chan):
      board_id_map[crate_card_chan] = board_id
      if crate_card_chan == 642:
        print("created board_id_map with {}, id {}".format(crate_card_chan,board_id_map[crate_card_chan]))
    else:
      if not board_id_map[crate_card_chan] == board_id:
        print ("WARNING: previously channel {} had board serial id {}, now it has id {}".format(crate_card_chan, board_id_map[crate_card_chan], board_id))

    #TODO: it feels like the wf can be probabilistically too early or too late in the record?
    #for now, just trim 4 off each side to make length 2010 wfs?

    sig_arr = <int16_t [:WF_LEN]> sig_ptr
    sig_arr = sig_arr[4:-4]

    color = "b"
    if min_signal_thresh > 0:
      baseline_samples = 100 #just take the first 100, it isnt that important
      noise_std = np.std(sig_arr[:100])
      bl_mean = np.mean(sig_arr[:100])
      if (np.amax(sig_arr) - bl_mean) < min_signal_thresh*noise_std: continue

        # if (np.amax(sig_arr) - bl_mean) < 5*noise_std: continue
        # color = "r"
        # # continue
        # plt.clf()
        # plt.plot(np.copy(sig_arr), color=color)
        # inp = input("Channel {}.  q to quit else to continue...".format(crate_card_chan))
        # if inp == "q": exit()


    data = {
      "energy": energy,
      "timestamp": timestamp,
      "channel": crate_card_chan,
      "waveform": [np.copy(sig_arr)]
    }

    # dr = pd.DataFrame(data, index=[n])
    appended_data.append(data)
    n+=1;

  fclose(f_in);
  if verbose: update_progress(1)
  verbose=True
  if verbose: print("Creating dataframe for file {}...".format(filename))
  df_data = pd.DataFrame.from_dict(appended_data)
  t1_file_name = os.path.join(output_dir, output_file_string+'_run{}.h5'.format(runNumber))
  if verbose: print("Writing {} to tier1 file {}...".format(filename, t1_file_name))

  df_channels['board_id'] = df_channels['channel'].map(board_id_map)

  df_data.to_hdf(t1_file_name, key="data", mode='w', data_columns=['energy', 'channel', 'timestamp'],)
  df_channels.to_hdf(t1_file_name,   key="channel_info", mode='a', data_columns=True,)

  return df_data

def ProcessTier1(filename,  processorList, output_file_string="t2", verbose=False, output_dir=None):
  '''
  Reads in "raw," or "tier 0," Orca data and saves to a hdf5 format using pandas
    filename: path to a tier1 data file
    processorList: TierOneProcessorList object with list of calculations/transforms you want done
    output_file_string: file is saved as <output_file_string>_run<runNumber>.h5
    verbose: spits out a progressbar to let you know how the processing is going
  '''

  directory = os.path.dirname(filename)
  output_dir = os.getcwd() if output_dir is None else output_dir

  #snag the run number (assuming filename ends in _run<number>.<filetype>)
  run_str = re.findall('run\d+', filename)[-1]
  runNumber = int(''.join(filter(str.isdigit, run_str)))

  df = pd.read_hdf(filename,key="data")
  appended_data = []

  print("Beginning Tier 1 processing of file {}...".format(filename))

  for i, (index, row) in enumerate(df.iterrows()):
    # print("im alive")
    if verbose and i%100==0: update_progress( float(i)/ len(df.index))

    #convert the stored waveform (which is int16) to a float, throw it to the processorList
    processorList.Reset( row["waveform"][0].astype('float32') )

    paramDict = processorList.Process(row)
    appended_data.append(paramDict)
    # print(row["channel"],  paramDict["channel"])
  if verbose: update_progress(1)
  verbose=True
  if verbose: print("Creating dataframe for file {}...".format(filename))
  df_data = pd.DataFrame(appended_data)

  t2_file_name = output_file_string+'_run{}.h5'.format(runNumber)
  t2_path = os.path.join(output_dir,t2_file_name)

  if verbose: print("Writing {} to tier1 file {}...".format(filename, t2_path))

  df_data.to_hdf(t2_path, key="data", format='fixed', mode='w', data_columns=True)
  return df_data

class TierOneProcessorList():
  '''
  Class to handle the list of transforms/calculations we do in the processing
  '''

  def __init__(self):
    self.list = []
    self.waveform_dict = {}
    self.param_dict = {}

    #t1 fields to make available for t2 processors
    self.t0_list = ["channel", "energy", "timestamp"]

  def Reset(self, waveform):
    self.param_dict = {}
    # print("TierOneProcessorList.reset() not implemented")
    # exit()
    self.waveform_dict = {"waveform":waveform}

  def Process(self, t0_row):
    for processor in self.list:
      #Parse out the t0 fields
      for name in self.t0_list: self.param_dict[name] = t0_row[name]


      processor.replace_args(self.param_dict)

      #TODO: what if output is None??

      try: #if you can set a waveform, do it
        processor.set_waveform(self.waveform_dict)
      except AttributeError:
        pass

      if isinstance(processor, Transformer):
        self.waveform_dict[processor.output_name] = processor.process()

      else:
        output = processor.output_name
        calc = processor.process()
        if not isinstance(output, str) and len(output) > 1:
          for i, out in enumerate(output):
            self.param_dict[out] = calc[i]
        else: self.param_dict[output] = calc

    return self.param_dict

  def AddTransform(self, function, args={}, input_waveform="waveform", output_waveform=None):
    self.list.append( Transformer(function, args, input_waveform, output_waveform) )

  def AddCalculator(self, function, args={}, input_waveform="waveform",  output_name=None):
    self.list.append( Calculator(function, args, input_waveform, output_name) )

  def AddDatabaseLookup(self, function, args={}, output_name=None):
    self.list.append( DatabaseLookup(function, args, output_name) )

  def AddFromTier0(self, name, output_name=None):
    self.list.append( Tier0Passer(name, output_name) )

#Classes that wrap functional implementations of calculators or transformers

class Calculator():
  def __init__(self, function, args={}, input_waveform="waveform",  output_name=None):
    self.function = function
    self.perm_args = args
    self.input_waveform_name = input_waveform
    self.output_name = output_name

  def replace_args(self, param_dict):
    #check args list for string vals which match keys in param dict
    self.args = self.perm_args.copy() #copy we'll actually pass to the function

    for (arg, val) in iteritems(self.args):
      if val in param_dict.keys():
        self.args[arg] = param_dict[val]

  def set_waveform(self, waveform_dict):
    self.input_wf = waveform_dict[self.input_waveform_name]

  def process(self):
    return self.function(self.input_wf, **self.args)

class Transformer():
  def __init__(self, function, args={}, input_waveform="waveform",  output_waveform=None):
    self.function = function
    self.perm_args = args
    self.input_waveform_name = input_waveform
    self.output_name = output_waveform

  def replace_args(self, param_dict):
    #check args list for string vals which match keys in param dict
    self.args = self.perm_args.copy() #copy we'll actually pass to the function

    for (arg, val) in iteritems(self.args):
      if val in param_dict.keys():
        self.args[arg] = param_dict[val]

  def set_waveform(self, waveform_dict):
    self.input_wf = waveform_dict[self.input_waveform_name]

  def process(self):
    return self.function(self.input_wf, **self.args)

class DatabaseLookup():
  def __init__(self, function, args={}, output_name=None):
    self.function = function
    self.perm_args = args
    self.output_name = output_name

  def replace_args(self, param_dict):
    #check args list for string vals which match keys in param dict
    self.args = self.perm_args.copy() #copy we'll actually pass to the function

    for (arg, val) in iteritems(self.args):
      if val in param_dict.keys():
        self.args[arg] = param_dict[val]

  def process(self):
    return self.function(**self.args)

class Tier0Passer():
  def __init__(self, t0_name, output_name=None):
    self.t0_name = t0_name
    if output_name is None: output_name = t0_name
    self.output_name = output_name

  def replace_args(self, param_dict):
    self.t0_value = param_dict[self.t0_name]

  def process(self):
    return self.t0_value

# ######################################################################################
#
# class NonlinearityCorrectionMap():
#   def __init__(self):
#     pass
#
#   def load_from_file(self, filename):
