from abc import ABCMeta, abstractmethod
import numpy as np
import pandas as pd
import sys

import matplotlib.pyplot as plt

def get_next_event(f_in):
    """
    Gets the next event, and some basic information about it \n
    Takes the file pointer as input \n
    Outputs: \n
        event_data: a byte array of the data produced by the card (could be header + data) \n
        slot: \n
        crate: \n
        data_id: This is the identifier for the type of data-taker (i.e. Gretina4M, etc) \n
    """
    # number of bytes to read in = 8 (2x 32-bit words, 4 bytes each)

    # The read is set up to do two 32-bit integers, rather than bytes or shorts
    # This matches the bitwise arithmetic used elsewhere best, and is easy to implement
    # Using a

    # NCRATES = 10

    try:
        head = np.fromstring(f_in.read(4),dtype=np.uint32)     # event header is 8 bytes (2 longs)
    except Exception as e:
        print(e)
        raise Exception("Failed to read in the event orca header.")

    # Assuming we're getting an array of bytes:
    # record_length   = (head[0] + (head[1]<<8) + ((head[2]&0x3)<<16))
    # data_id         = (head[2] >> 2) + (head[3]<<8)
    # slot            = (head[6] & 0x1f)
    # crate           = (head[6]>>5) + head[7]&0x1
    # reserved        = (head[4] + (head[5]<<8))

    # Using an array of uint32
    record_length   =int( (head[0] & 0x3FFFF))
    data_id         =int( (head[0] >> 18))
    # slot            =int( (head[1] >> 16) & 0x1f)
    # crate           =int( (head[1] >> 21) & 0xf)
    # reserved        =int( (head[1] &0xFFFF))

    # /* ========== read in the rest of the event data ========== */
    try:
        event_data = f_in.read(record_length*4-4)     # record_length is in longs, read gives bytes
    except Exception as e:
        print("  No more data...\n")
        print(e)
        raise EOFError

    # if (crate < 0 or crate > NCRATES or slot  < 0 or slot > 20):
    #     print("ERROR: Illegal VME crate or slot number {} {} (data ID {})".format(crate, slot,data_id))
    #     raise ValueError("Encountered an invalid value of the crate or slot number...")

    # return event_data, slot, crate, data_id
    return event_data, data_id

def get_decoders():
    """
        Looks through all the data takers that exist in this Data_Loader class and see which ones exist.
    """

    decoders = []
    for sub in Data_Loader.__subclasses__():
        for subsub in sub.__subclasses__():
            try:
                a = subsub()
                # n = a.name
                # print("name: ",n)
                decoders.append(a)
            except Exception as e:
                print(e)
                pass

    return decoders



class Data_Loader(metaclass=ABCMeta):
    def __init__(self):
        self.decoded_values = []

    @abstractmethod
    def decode_event(self,event_data_bytes, event_number):
        pass

    # @abstractmethod
    # def decode_header(self):
    #     pass

    def to_file(self, file_name):
        df_data = pd.DataFrame.from_dict(self.decoded_values)
        df_data.to_hdf(file_name, key=self.name, mode='a')


class Digitizer(Data_Loader):
    def __init__(self):
        super().__init__()

    def decode_event(self,event_data_bytes, event_number):
        pass

    # def decode_header():
    #     pass

class Poller(Data_Loader):
    def __init__(self):
        super().__init__()

    def decode_event(self,event_data_bytes, event_number):
        pass

class Gretina4m_Decoder(Digitizer):
    '''
    min_signal_thresh: multiplier on noise ampliude required to process a signal: helps avoid processing a ton of noise
    chanList: list of channels to process
    '''
    def __init__(self):
        super().__init__()

        self.name = 'ORGretina4MWaveformDecoder' #ORGretina4M'

        self.event_header_length = 30
        self.wf_length = 2018

        self.active_channels = []


        return


    def decode_event(self,event_data_bytes, event_number):
        # parse_event_data(evtdat, &timestamp, &energy, &channel)
        """
            Parse the header for an individual event
        """

        event_data = np.fromstring(event_data_bytes,dtype=np.uint16)

        # this is for a uint32
        # channel = event_data[1]&0xF
        # board_id = (event_data[1]&0xFFF0)>>4
        # timestamp = event_data[2] + ((event_data[3]&0xFFFF)<<32)
        # energy = ((event_data[3]&0xFFFF0000)>>16) + ((event_data[4]&0x7F)<<16)
        # wf_data = event_data[self.event_header_length:(self.event_header_length+self.wf_length)]


        # this is for a uint16
        card = event_data[1]&0x1F
        crate = (event_data[1]>>5)&0xF

        channel = event_data[4] & 0xf
        board_id =(event_data[4]&0xFFF0)>>4
        timestamp = event_data[6] + (event_data[7]<<16) + (event_data[8]<<32)
        energy = event_data[9] + ((event_data[10]&0x7FFF)<<16)
        wf_data = event_data[self.event_header_length:]#(self.event_header_length+self.wf_length)*2]

        crate_card_chan = (crate << 9) + (card << 4) + (channel)


        data_dict = self.format_data(energy,timestamp, crate_card_chan, wf_data, board_id)
        data_dict["event_number"] = event_number
        self.decoded_values.append(data_dict)

        return data_dict


    def format_data(self,energy,timestamp,crate_card_chan,wf_arr, board_id):
        """
        Format the values that we get from this card into a pandas-friendly format.
        """

        data = {
            "energy": energy,
            "timestamp": timestamp,
            "channel": crate_card_chan,
            "board_id":board_id,
            "waveform": [np.array(wf_arr, dtype=np.int16)]
        }
        return data

    def test_decode_event(self,):
        """
            Runs a fake waveform through the decoder.
        """
        event_data_bytes = bytes.fromhex("00000a00aaaaaaaad1000000e178f14429009b9de2510b20eb43290003000000fefffffffafff9fffcfff5fffbfffafffdfffdff0300fbfff9fffafffefff9fff5fffffffefffbfff6fff6fffeff0300fdfff9fffdfff7fff8fffcfff5fff8fffafffcfffcfffefffefffafff4fff9fffbfff8fffafffbff0400f8fff8fff9fff7fff9fffdff0000fbff0400fbfff6fffcfffefffefff7fff8fffdfff9fffafffefffafff9fffcff01000000fdfff8fff9fffafffeff00000200f9fff8fffcfffbff0000f9fff8fffcff0000fbfffcfffbfffeffffffffff0200fffffafff5fff7fff7fffeff0200fefff8fffdfffcfff6fff8fffcfffdff")

        wf = self.decode_event(event_data_bytes)

        print(self.values["channel"])
        print(self.values["timestamp"])
        print(self.values["energy"])
        print(self.values["waveform"])

        return

    def parse_event_data(self,data):
        pass


class SIS3302_Decoder(Digitizer):
    def __init__(self):
        super().__init__()
        self.values = dict()
        self.event_header_length = 1

        self.name = 'ORSIS3302DecoderForEnergy'
        return

    def get_name(self):
        return self.name

    def decode_event(self,event_data_bytes, event_number, verbose=False):
        """
        The SIS3302 can produce a waveform from two sources:
            1: ADC raw data buffer: This is a normal digitizer waveform
            2: Energy data buffer: Not sure what this is

        Additionally, the ADC raw data buffer can take data in a buffer wrap mode, which seems
        to cyclicly fill a spot on memory, and it requires that you have to re-order the records
        afterwards.

        The details of how this header is formatted apparently wasn't important enough for the
        SIS engineers to want to put it in the manual, so this is a guess in some places


        0   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^--------------------------------most  sig bits of num records lost
            ------------------------------^^^^-^^^--least sig bits of num records lost
                    ^ ^^^---------------------------crate
                         ^ ^^^^---------------------card
                                ^^^^ ^^^^-----------channel
                                                  ^--buffer wrap mode
        1   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-length of waveform (longs)
        2   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-length of energy   (longs)

        3   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^^ ^^^^ ^^^^--------------------- timestamp[47:32]
                                ^^^^ ^^^^ ^^^^ ^^^^- "event header and ADC ID"
        4   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^^ ^^^^ ^^^^--------------------- timestamp[31:16]
                                ^^^^ ^^^^ ^^^^ ^^^^- timestamp[15:0]

            If the buffer wrap mode is enabled, there are two more words of header:

      (5)   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-adc raw data length (longs)
      (6)   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-adc raw data start index (longs)

            After this, it will go into the two data buffers directly.
            These buffers are packed 16-bit words, like so:

            xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^^ ^^^^ ^^^^--------------------- sample N + 1
                                ^^^^ ^^^^ ^^^^ ^^^^- sample N

            The first data buffer is the adc raw data buffer, which is the usual waveform
            The second is the energy data buffer, which might be the output of the energy filter

            This code should handle arbitrary sizes of both buffers.

            An additional complexity arises if buffer wrap mode is enabled.
            This apparently means the start of the buffer can be anywhere in the buffer, and
            it must be read circularly from that point. Not sure why it is done that way, but
            this should work correctly to disentagle that.

            Finally, there should be a footer of 4 long words at the end:
       -4   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-Energy max value
       -3   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-Energy value from first value of energy gate
       -2   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx-This word is said to contain "pileup flag, retrigger flag, and trigger counter" in no specified locations...
       -1   1101 1110 1010 1101 1011 1110 1110 1111- Last word is always 0xDEADBEEF

        """

        event_data_uint = np.fromstring(event_data_bytes,dtype=np.uint32)
        event_data_uint16 = np.fromstring(event_data_bytes,dtype=np.uint16)

        event_data = event_data_uint

        # print(event_data[0])
        buffer_wrap_mode    = (event_data[0]&0x1)
        n_lost_records_msb  = ((event_data[0]>>25)&0x7F)
        n_lost_records_lsb  = ((event_data[0]>>2 )&0x7F)
        n_lost_records = (n_lost_records_msb<<7) + (n_lost_records_lsb)
        channel             = ((event_data[0]>>8) &0xFF)
        card                = ((event_data[0]>>16)&0x1F)
        crate               = ((event_data[0]>>21)&0xF)

        crate_card_chan = (crate << 9) + (card << 4) + (channel)

        adc_raw_data_length     = event_data[1]     # number of long words long, not the number of points
        energy_data_length      = event_data[2]

        event_header_id = (event_data[3]&0xFF)
        timestamp = event_data[4] + ((event_data[3]>>16)&0xFFFF)

        if(buffer_wrap_mode):
            sisHeaderLength = 4

            adc_raw_data_length = event_data[5]
            adc_raw_data_start_index = event_data[6]

            adc_raw_data_start_1    = 2*adc_raw_data_start_index
            adc_raw_data_stop_1     = 2*adc_raw_data_buffer_stop

            adc_raw_data_start_2    = 2*adc_raw_data_buffer_start
            adc_raw_data_stop_2     = 2*adc_raw_data_start_1 - 2

            wf_data_1 = np.zeros(adc_raw_data_stop_1 - adc_raw_data_start_1)
            wf_data_2 = np.zeros(adc_raw_data_stop_2 - adc_raw_data_start_2)

        else:
            sisHeaderLength = 2

        # all lengths here are in long words (32-bytes)
        totalRecordLength = len(event_data_uint)    # entire thing we get handed here
        orcaHeaderLength = 3                        # this is the crate/card/channel/bufferwrap
        footerLength = 4                            # this is the 0xDEADBEEF
        # expectedWFLength = totalRecordLength - orcaHeaderLength - sisHeaderLength - energy_data_length - footerLength

        wf_data = np.zeros(adc_raw_data_length*2)
        energy_data = np.zeros(energy_data_length*2)

        # These values are in number of 16-bit short words
        adc_raw_data_buffer_start = 2*(orcaHeaderLength+sisHeaderLength)                  # wfStart: waveform starting position in the uint16
        adc_raw_data_buffer_stop = 2*(totalRecordLength - energy_data_length - footerLength)    # wfStop: waveform stopping position in uint16
        energy_data_buffer_start = adc_raw_data_buffer_stop
        energy_data_buffer_stop = orcaHeaderLength+sisHeaderLength+adc_raw_data_length+energy_data_length
        footerStart = energy_data_buffer_stop                               # position of start of footer (after adc and energy buffers)


        # Pull the values out of the footer as best we can
        energy_max_value = event_data_uint[footerStart]
        energy_first_value = event_data_uint[footerStart+1]
        pileup_retrigger_counter_word = event_data_uint[footerStart+2]
        lastword = event_data_uint[-1]

        # basic check for data integrity:
        if(lastword != 0xDEADBEEF):
            print("ERROR: Last word of SIS3302 record was ", lastword, " instead of 0xDEADBEEF!!! This may indicate a serious issue!")
            # for now, we'll just continue blindly, hoping that we can recover...

        if(verbose):
            print(hex(lastword))

            print("buffer wrap mode: ",buffer_wrap_mode)
            print("number of lost records: ", n_lost_records)
            print("channel: ", channel)
            print("card: ",card)
            print("crate", crate)
            print("waveform length", adc_raw_data_length)
            print("energy length", energy_data_length)
            print("length of event data (longs)", len(event_data_uint))
            print("timestamp: ", timestamp)
            print("event header word: ",hex(event_header_id))
            print("energy max val: ", energy_max_value)
            print("energy first val: ", energy_first_value)
            print("pileup/retrigger word: ", hex(pileup_retrigger_counter_word))

        # If there is a waveform, store it
        if(adc_raw_data_length>0):
            if(buffer_wrap_mode):
                wf_data_1 = event_data_uint16[adc_raw_data_start_1:adc_raw_data_stop_1]
                wf_data_2 = event_data_uint16[adc_raw_data_start_2:adc_raw_data_stop_2]

                wf_data = np.concatenate([wf_data_1,wf_data_2])

            else:   # not buffer wrap mode
                wf_data = event_data_uint16[adc_raw_data_buffer_start:adc_raw_data_buffer_stop]

        # If there is an energy waveform, store it
        if(energy_data_length > 0):
            energy_data = event_data_uint16[energy_data_buffer_start:energy_data_buffer_stop]

        data_dict = self.format_data(energy_max_value, energy_first_value, timestamp, crate_card_chan, event_header_id, wf_data,energy_data)

        data_dict["event_number"] = event_number
        self.decoded_values.append(data_dict)

        return data_dict

    def format_data(self,energy_max_value,energy_first_value,timestamp,crate_card_chan,event_header_id,wf_data,energy_data):
        """
        Format the values that we get from this card into a pandas-friendly format.
        """

        data = {
            "energy": energy_max_value,
            "energy_first" : energy_first_value,
            "timestamp": timestamp,
            "channel": crate_card_chan,
            "board_id":event_header_id,
            "waveform": [np.array(wf_data, dtype=np.int16)],
            "energy_wf": [np.array(energy_data, dtype=np.int16)]
        }
        return data


# Polled devices

class MJDPreamp_Decoder(Poller):
    def __init__(self):
        super().__init__()
        self.event_header_length = -1

        self.name = 'ORMJDPreAmpDecoderForAdc' #MJDPreAmpModel'

        return

    def decode_event(self,event_data_bytes,event_number, verbose=False):
        """
            Decodes the data from a MJDPreamp Object.
            Returns:
                adc_val     : A list of floating point voltage values for each channel
                timestamp   : An integer unix timestamp
                enabled     : A list of 0 or 1 values indicating which channels are enabled

            Data Format:
            0 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
                                       ^^^^ ^^^^ ^^^^- device id
            1 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  unix time of measurement
            2 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  enabled adc mask
            3 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 0 encoded as a float
            4 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 1 encoded as a float
            ....
            ....
            18 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 15 encoded as a float

        """

        event_data_uint = np.fromstring(event_data_bytes,dtype=np.uint32)
        event_data_float = np.fromstring(event_data_bytes,dtype=np.float32)

        device_id = (event_data_uint[0]&0xFFF)
        timestamp = event_data_uint[1]
        enabled = np.zeros(16)
        adc_val = np.zeros(16)

        for i,val in enumerate(enabled):
            enabled[i] = (event_data_uint[2]>>(i) & 0x1)

            if(verbose):
                if(enabled[i] != 0):
                    print("Channel %d is enabled" % (i))
                else:
                    print("Channel %d is disabled" % (i))

        for i,val in enumerate(adc_val):
            adc_val[i] = event_data_float[3+i]

        if(verbose):
            print(adc_val)

        data_dict = self.format_data(adc_val, timestamp, enabled, device_id, event_number)
        self.decoded_values.append(data_dict)

        return data_dict

    def format_data(self, adc_val, timestamp, enabled, device_id, event_number):
        """
        Format the values that we get from this card into a pandas-friendly format.
        """

        data = {
            "adc" : adc_val,
            "timestamp" : timestamp,
            "enabled" : enabled,
            "device_id" : device_id, #The first number is just which preamp object it is in the data record, and the second one is which preamp it is in the orca dialog.
            "event_number" : event_number
        }
        return data

class ISegHV_Decoder(Poller):
    def __init__(self):
        super().__init__()
        self.event_header_length = -1
        self.name = 'ORiSegHVCardDecoderForHV' #ORiSegHVCard'

        return

    def decode_event(self,event_data_bytes, event_number, verbose=False):
        """
            Decodes an iSeg HV Card event

            xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^^ ^^^^ ^^----------------------- Data ID (from header)
            -----------------^^ ^^^^ ^^^^ ^^^^ ^^^^- length
        0   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ----------^^^^-------------------------- Crate number
            ---------------^^^^--------------------- Card number

        1    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx -ON Mask
        2    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx -Spare
        3    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  time in seconds since Jan 1, 1970
        4    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 0)
        5    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 0)
        6    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 1)
        7    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 1)
        8    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 2)
        9    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 2)
        10   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 3)
        11   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 3)
        12   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 4)
        13   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 4)
        14   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 5)
        15   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 5)
        16   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 6)
        17   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 6)
        18   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 7)
        19   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 7)
        """

        event_data_int = np.fromstring(event_data_bytes,dtype=np.uint32)
        event_data_float = np.fromstring(event_data_bytes,dtype=np.float32)

        # print(event_data_int)
        # print(event_data_float)

        crate   = (event_data_int[0]>>20)&0xF
        card    = (event_data_int[0]>>16)&0xF


        enabled = np.zeros(8)     #enabled channels
        voltage = np.zeros(8)
        current = np.zeros(8)
        timestamp = event_data_int[3]

        for i,j in enumerate(enabled):
            enabled[i] = (event_data_int[1]>>(4*i) & 0xF)

            if(verbose):
                if(enabled[i] != 0):
                    print("Channel %d is enabled" % (i))
                else:
                    print("Channel %d is disabled" % (i))

        for i,j in enumerate(voltage):
            voltage[i] = event_data_float[4+(2*i)]
            current[i] = event_data_float[5+(2*i)]

        if(verbose):
            print("HV voltages: ",voltage)
            print("HV currents: ",current)

        # self.values["channel"] = channel

        data_dict = self.format_data(timestamp, voltage, current, enabled, crate, card, event_number)
        self.decoded_values.append(data_dict)

        return data_dict

    def format_data(self, timestamp, voltage, current, enabled, crate, card, event_number):
        """
        Format the values that we get from this card into a pandas-friendly format.
        """

        data = {
            "timestamp" : timestamp,
            "voltage" : voltage,
            "current" : current,
            "enabled" : enabled,
            "crate" : crate,
            "card" : card,
            "event_number" : event_number
        }

        return data
