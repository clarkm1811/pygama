import numpy as np
import pandas as pd
import sys
from scipy import signal

from .dataloading import DataLoader

__all__ = ['Gretina4MDecoder', 'SIS3302Decoder']


class Digitizer(DataLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode_event(self,event_data_bytes, event_number, header_dict):
        pass

    # def decode_header():
    #     pass

class Gretina4MDecoder(Digitizer):
    '''
    min_signal_thresh: multiplier on noise ampliude required to process a signal: helps avoid processing a ton of noise
    chanList: list of channels to process
    '''
    def __init__(self, *args, **kwargs):
        self.decoder_name = 'ORGretina4MWaveformDecoder' #ORGretina4M'
        self.class_name = 'ORGretina4MModel'

        super().__init__(*args, **kwargs)

        #The header length "should" be 32 -- 30 from gretina header, 2 from orca header
        #but the "reserved" from 16 on seems to be good baseline info, so lets try to use it
        self.event_header_length = 18

        self.wf_length = 2018
        self.sample_period = 10#ns

        self.active_channels = []

        return


    def decode_event(self,event_data_bytes, event_number, header_dict):
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

        # import matplotlib.pyplot as plt
        # #Get the right digitizer information:
        # card_info = self.object_info.loc[(crate, card)]
        # prere_cnt = card_info["Prerecnt"][channel]
        # postre_cnt = card_info["Postrecnt"][channel]
        # ft_cnt = card_info["FtCnt"][channel]
        # print("{},{},{}".format(prere_cnt, postre_cnt, ft_cnt))
        #
        # event_data_float = event_data.astype(np.float_)
        # event_data_float -= np.mean(event_data_float[100:800])
        #
        # plt.ion()
        # plt.plot(event_data_float, ls="steps-mid")
        # plt.axvline(self.event_header_length, ls=":", c="r")
        # plt.axvline( len(event_data)-ft_cnt-1, c="r", ls=":" )
        # inp = input("q to quit, else")
        # if inp == "q": exit()

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

    def parse_event_data(self,event_data):
        '''
        event_data is a pandas df row from a decoded event
        '''
        #TODO: doesn't handle full-time downsampling (channel_sum, channel_div)
        #TODO: adaptive presum handling could be done better
        #TODO: you're hosed if presum div is set to be the same as number of presum

        #cast wf to double
        wf_data = event_data["waveform"][0].astype('float_')

        #we save crate_card_chan (for historical reasons), so decode that
        crate = event_data['channel'] >> 9
        card =  (event_data['channel'] & 0xf0) >> 4
        chan =  event_data['channel'] & 0xf

        #Get the right digitizer information:
        card_info = self.object_info.loc[(crate, card)]

        # if card_info["PreSum Enabled"][chan]:
        #Correct for presumming
        multirate_sum = 10 if card_info["Mrpsrt"][chan] == 3 else 2 **(card_info["Mrpsrt"][chan]+1)
        multirate_div = 2**card_info["Mrpsdv"][chan]
        ratio = multirate_sum/multirate_div
        # "channel_div": 2**card["Chpsdv"][channum],
        # "channel_sum": 10 if card["Chpsrt"][channum] == 3 else 2 **(card["Chpsrt"][channum]+1),

        prere_cnt = card_info["Prerecnt"][chan]
        postre_cnt = card_info["Postrecnt"][chan]
        ft_cnt = card_info["FtCnt"][chan]
        ms_start_offset = 0

        idx_ft_start_expected = len(wf_data) - ft_cnt -1
        idx_bl_end_expected = len(wf_data) - prere_cnt - postre_cnt - ft_cnt

        filter_len = 20
        filter_win_mult = 1

        filter_window = np.ones(filter_len)
        filter_window[:int(filter_len/2)]*=1
        filter_window[int(filter_len/2):]*=-1

        #TODO: doing the convolution on the whole window is unnecessarily slow
        wf_data_cat = np.concatenate((np.ones(filter_win_mult*filter_len)*wf_data[0], wf_data, np.ones(filter_win_mult*filter_len)*wf_data[-1]))
        wf_diff = signal.convolve(wf_data_cat, filter_window, "same")

        idx_bl_end = np.argmax(np.abs(  wf_diff[filter_win_mult*filter_len:-filter_win_mult*filter_len][:idx_bl_end_expected+4]))
        idx_ft_start = np.argmax(np.abs(   wf_diff[filter_win_mult*filter_len:-filter_win_mult*filter_len][idx_ft_start_expected-5:])) + idx_ft_start_expected-5

        # if (idx_bl_end < idx_bl_end_expected - 4) or (idx_bl_end > idx_bl_end_expected):
            #baseline is probably very near zero, s.t. its hard to see the jump.  just assume it where its meant to be.
            # idx_bl_end = idx_bl_end_expected
        if (idx_ft_start < idx_ft_start_expected - 2) or (idx_ft_start > idx_ft_start_expected):
            idx_ft_start = idx_ft_start_expected
            # raise ValueError()

        wf_data[:idx_bl_end] /= (ratio)
        wf_data[idx_ft_start:] /= (ratio)

        time_pre = np.arange(idx_bl_end)*self.sample_period*multirate_sum - (len(wf_data) - self.wf_length)
        time_full  = np.arange(idx_ft_start-idx_bl_end)*self.sample_period + time_pre[-1] +self.sample_period# + ms_start_offset)
        time_ft = np.arange(ft_cnt+1)*self.sample_period*multirate_sum + time_full[-1] + 0.5*(self.sample_period*multirate_sum + ms_start_offset)

        time = np.concatenate((time_pre, time_full, time_ft))

        return time[-self.wf_length:], wf_data[-self.wf_length:]


class SIS3302Decoder(Digitizer):
    def __init__(self, *args, **kwargs):
        self.decoder_name = 'ORSIS3302DecoderForEnergy'
        self.class_name = 'SIS3302_placeholder' #what should this be?

        super().__init__(*args, **kwargs)
        self.values = dict()
        self.event_header_length = 1

        return

    def get_name(self):
        return self.decoder_name

    def decode_event(self,event_data_bytes, event_number, header_dict, verbose=False):
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
