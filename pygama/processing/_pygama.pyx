cimport numpy as np

import numpy as np
import os, re, sys
import pandas as pd
import h5py
from future.utils import iteritems

from ..utils import update_progress
from ..decoders import *
from ..decoders.digitizers import Digitizer
from ._header_parser import *
from .processors import Calculator, Transformer, DatabaseLookup, Tier0Passer

def ProcessTier0( filename, output_file_string = "t1", chan_list=None, n_max=np.inf, verbose=False, output_dir=None, decoders=None):
  '''
  Reads in "raw," or "tier 0," Orca data and saves to a hdf5 format using pandas
    filename: path to an orca data file
    output_file_string: output file name will be <output_file_string>_run<runNumber>.h5
    n_max: maximum number of events to process (useful for debugging)
    verbose: spits out a progressbar to let you know how the processing is going
    output_dir: where to stash the t1 file
  '''

  SEEK_END = 2

  directory = os.path.dirname(filename)
  output_dir = os.getcwd() if output_dir is None else output_dir

  #parse the header (in python)

  reclen, reclen2, headerDict = parse_header(filename)

  #TODO: do something useful with parsing out the MJ model
  # detector_info = StringIO( headerDict["ObjectInfo"]["MajoranaModel"]["DetectorGeometry"] )
  # df = pd.read_csv(detector_info, index_col=0, na_values="--")
  # df = df.dropna()
  # print (df)
  # exit()

  print("Header parsed.")
  print("   %d longs (in plist header)" % reclen)
  print("   %d bytes in the header" % reclen2)

  f_in = open(filename.encode('utf-8'), "rb")
  if f_in == None:
      print("Couldn't file the file %s" % filename)   # file the file?
      sys.exit(0)

  #figure out the total size
  f_in.seek(0, SEEK_END)
  file_size = float(f_in.tell())
  f_in.seek(0,0)    # rewind
  file_size_MB = file_size/1e6
  print("Total file size: %3.3f MB" % file_size_MB)

  # skip the header
  f_in.seek(reclen*4)   # reclen is in number of longs, and we want to skip a number of bytes

  # pull out the run number
  runNumber = get_run_number(headerDict)
  print("Run number: {}".format(runNumber))

  #TODO: This is all pretty hard to read & comprehend easily.  Can we clean it up?  Move to header_parser?

  #id_dict = flip_data_ids(headerDict)
  id_dict = get_decoder_for_id(headerDict)

  print("The Data IDs present in this file (header) are:")
  for id in id_dict:
    print("    {}: {}".format(id, id_dict[id]))

  #find unique decoders actually used in the data
  used_decoder_names =  set([id_dict[id] for id in id_dict])

  if decoders is None:
    # The decoders variable is a list of all the decoders that exist in pygama
    decoders = get_decoders(headerDict)
    decoder_names = [d.decoder_name for d in decoders]

    print("Warning: No decoder implemented for the following data takers: ")
    for d in used_decoder_names:
      if d not in decoder_names:
        print("  {}".format(d))

  #kill unnecessary decoders
  for d in decoders:
    if d.decoder_name not in used_decoder_names: decoders.remove(d)
    if chan_list is not None and isinstance(d, Digitizer): d.chan_list = chan_list

  decoder_names = [d.decoder_name for d in decoders]

  #Build a map from data id to decoder
  id_to_decoder = {}
#  id_to_decoder = id_dict
  for id in id_dict:
    try:
      id_to_decoder[id] = decoders[decoder_names.index(id_dict[id])]
    except ValueError:
      #if there isn't a decover available, we already warned everyone
      pass

  print("id_to_decoder contains:")
  for key in id_to_decoder:
    print("    {}: {}".format(key, id_to_decoder[key].decoder_name))

  #keep track of warnings we've raised for missing decoders
  unrecognized_data_ids = []
  board_id_map = {}
  appended_data_map = {}

  print("Beginning Tier 0 processing of file {}...".format(filename))
  event_number = 0 #number of events decoded
  while (event_number < n_max and f_in.tell() < file_size):# and f_in.tell() < file_size):
    event_number +=1
    if verbose and event_number%1000==0:
        update_progress( float(f_in.tell()) / file_size )

    try:
        event_data, data_id = get_next_event(f_in)
    except EOFError:
        break
    except Exception as e:
        print("Failed to get the next event... (Exception: {})".format(e))
        break

    try:
        decoder = id_to_decoder[data_id]
    except KeyError:
        if data_id not in id_dict and data_id not in unrecognized_data_ids:
          unrecognized_data_ids.append(data_id)
        continue

    decoder.decode_event(event_data, event_number, headerDict )

  f_in.close()
  if verbose: update_progress(1)

  if len(unrecognized_data_ids) > 0:
    print("\nGarbage Report!:")
    print("Found the following data IDs which were not present in the header:")
    for id in unrecognized_data_ids:
      print ("  {}".format(id))
    print("hopefully they weren't important!\n")


  t1_file_name = os.path.join(output_dir, output_file_string+'_run{}.h5'.format(runNumber))


  if os.path.isfile(t1_file_name):
    if verbose: print("Over-writing tier1 file {}...".format(t1_file_name))
    os.remove(t1_file_name)

  if verbose: print("Writing {} to tier1 file {}...".format(filename, t1_file_name))
  [d.to_file(t1_file_name) for d in decoders]

def ProcessTier1(filename,  processorList, digitizer_list=None, output_file_string="t2", verbose=False, output_dir=None):
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

  if digitizer_list is None:
    #digitize everything available
    digitizer_list = get_digitizers()
  digitizer_decoder_names = [d.class_name for d in digitizer_list]

  #find the available keys
  f = h5py.File(filename, 'r')
  for d in digitizer_list:
    if d.decoder_name not in f.keys():
      digitizer_list.remove(d)

  print("Beginning Tier 1 processing of file {}...".format(filename))

  for digitizer in digitizer_list:
    print("   Processing from digitizer {}".format(digitizer.class_name))

    object_info = pd.read_hdf(filename,key=digitizer.class_name)
    digitizer.load_object_info(object_info)

    event_df = pd.read_hdf(filename,key=digitizer.decoder_name)

    appended_data = []

    for i, (index, event_data) in enumerate(event_df.iterrows()):
      if verbose and i%100==0: update_progress( float(i)/ len(event_df.index))

      waveform = digitizer.parse_event_data(event_data)
      #Currently, I'll just mandate that we only process full waveform data i guess
      wf_data = waveform.get_waveform()

      # import matplotlib.pyplot as plt
      # print(waveform.full_sample_range)
      # plt.plot(waveform.data)
      # plt.show()
      # exit()

      # try:
        #convert the stored waveform (which is int16) to a float, throw it to the processorList
      processorList.Reset( wf_data )
      try:
        processorList.param_dict["fs_start"] = waveform.full_sample_range[0]
        processorList.param_dict["fs_end"] = waveform.full_sample_range[1]
      except AttributeError:
        #in case it isn't a multisampled waveform object
        pass

      paramDict = processorList.Process(event_data)
      appended_data.append(paramDict)
      # except Exception as e:
      #   print(e)
      #   import matplotlib.pyplot as plt
      #   plt.plot(wf_data)
      #   plt.show()
      #   exit()

  if verbose: update_progress(1)

  verbose=True
  if verbose: print("Creating dataframe for file {}...".format(filename))
  df_data = pd.DataFrame(appended_data)

  t2_file_name = output_file_string+'_run{}.h5'.format(runNumber)
  t2_path = os.path.join(output_dir,t2_file_name)

  if verbose: print("Writing {} to tier1 file {}...".format(filename, t2_path))

  df_data.to_hdf(t2_path, key="data", format='table', mode='w', data_columns=True)
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
