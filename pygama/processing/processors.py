from future.utils import iteritems

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
      if getattr(val, '__iter__', False):
        self.args[arg] = val
      elif val in param_dict.keys():
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
