from abc import ABCMeta, abstractmethod
import numpy as np
import pandas as pd

class Data_Loader(metaclass=ABCMeta):
    def __init__(self):
        self.decoded_values = []

    @abstractmethod
    def decode_event(self,event_data_bytes):
        pass

    # @abstractmethod
    # def decode_header(self):
    #     pass

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

        head = np.zeros(2)
        data_id = None
        # board_id = 0
        # current_runNumber = 0
        slot = 0
        crate = 0
        NCRATES = 10

        try:
            head = np.fromstring(f_in.read(8),dtype=np.uint32)     # event header is 8 bytes (2 longs)
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
        record_length   = (head[0] & 0x3FFFF)
        data_id         = (head[0] >> 18)
        slot            = (head[1] >> 16) & 0x1f
        crate           = (head[1] >> 21) & 0xf
        reserved        = (head[1] &0xFFFF)

        if (crate < 0 or crate > NCRATES or slot  < 0 or slot > 20):
            print("ERROR: Illegal VME crate or slot number %d %d\n" %( crate, slot))
            raise Exception("Encountered an invalid value of the crate or slot number...")

        # /* ========== read in the rest of the event data ========== */
        try:
            event_data = f_in.read(record_length*4-8)     # record_length is in longs, read gives bytes
        except Exception as e:
            print("  No more data...\n")
            print(e)
            raise EOFError

        return event_data, slot, crate, data_id

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

    def to_file(self, file_name):
        df_data = pd.DataFrame.from_dict(self.decoded_values)
        df_data.to_hdf(file_name, key=self.name, mode='w')


class Digitizer(Data_Loader):
    def __init__(self):
        super().__init__()

    def decode_event(self,event_data_bytes):
        pass

    # def decode_header():
    #     pass

class Poller(Data_Loader):
    def __init__(self):
        super().__init__()

    def decode_event(self,event_data_bytes):
        pass

class Gretina4m_Decoder(Digitizer):
    '''
    min_signal_thresh: multiplier on noise ampliude required to process a signal: helps avoid processing a ton of noise
    chanList: list of channels to process
    '''
    def __init__(self):
        super().__init__()

        self.name = 'ORGretina4M'

        self.event_header_length = 30
        self.wf_length = 2018

        self.active_channels = []


        return


    def decode_event(self,event_data_bytes, crate=0, card=0):
        # parse_event_data(evtdat, &timestamp, &energy, &channel)
        """
            Parse the header for an individual event
            Expects that event_data looks like an array of 16-bit short words, so hopefully it is
        """

        event_data = np.fromstring(event_data_bytes,dtype=np.uint16)

        # this is for a uint32
        # channel = event_data[1]&0xF
        # board_id = (event_data[1]&0xFFF0)>>4
        # timestamp = event_data[2] + ((event_data[3]&0xFFFF)<<32)
        # energy = ((event_data[3]&0xFFFF0000)>>16) + ((event_data[4]&0x7F)<<16)
        # wf_data = event_data[self.event_header_length:(self.event_header_length+self.wf_length)]


        # this is for a uint16
        channel = event_data[2] & 0xf
        board_id =(event_data[2]&0xFFF0)>>4
        timestamp = event_data[4] + (event_data[5]<<16) + (event_data[6]<<32)
        energy = event_data[7] + ((event_data[8]&0x7FFF)<<16)
        wf_data = event_data[self.event_header_length:]#(self.event_header_length+self.wf_length)*2]

        crate_card_chan = (crate << 9) + (card << 4) + (channel)


        data_dict = self.format_data(energy,timestamp, crate_card_chan, wf_data, board_id)
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
            "waveform": [np.array(wf_arr, dtype=np.uint16)]
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
        self.event_header_length = 1

        self.name = 'ORSIS3302'
        return

    def decode_event(self,event_data_bytes):
        pass


# Polled devices

class MJDPreamp_Decoder(Poller):
    def __init__(self):
        super().__init__()
        self.event_header_length = -1

        self.name = 'MJDPreAmpModel'

        return

    def decode_event(self,event_data_bytes,verbose=False):
        """
            Decodes the data from a MJDPreamp Object.
            Returns:
                adc_val     : A list of floating point voltage values for each channel
                timestamp   : An integer unix timestamp
                enabled     : A list of 0 or 1 values indicating which channels are enabled

            Data Format:
            0 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  unix time of measurement
            1 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  enabled adc mask
            2 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 0 encoded as a float
            3 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 1 encoded as a float
            ....
            ....
            17 xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  adc chan 15 encoded as a float

        """

        event_data_uint = np.fromstring(event_data_bytes,dtype=np.uint32)
        event_data_float = np.fromstring(event_data_bytes,dtype=np.float32)

        timestamp = event_data_uint[0]
        enabled = np.zeros(16)
        adc_val = np.zeros(16)

        for i,val in enumerate(enabled):
            enabled[i] = (event_data_uint[1]>>(i) & 0x1)

            if(verbose):
                if(enabled[i] != 0):
                    print("Channel %d is enabled" % (i))
                else:
                    print("Channel %d is disabled" % (i))

        for i,val in enumerate(adc_val):
            adc_val[i] = event_data_float[2+i]

        if(verbose):
            print(adc_val)

        data_dict={}
        data_dict["adc"] = adc_val
        data_dict["timestamp"] = timestamp
        data_dict["enabled"] = enabled

        self.decoded_values.append(data_dict)

        return data_dict


class ISegHV_Decoder(Poller):
    def __init__(self):
        super().__init__()
        self.event_header_length = -1
        self.name = 'ORiSegHVCard'

        return

    def decode_event(self,event_data_bytes,verbose=False):
        """
            Decodes an iSeg HV Card event

            xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ^^^^ ^^^^ ^^^^ ^^----------------------- Data ID (from header)
            -----------------^^ ^^^^ ^^^^ ^^^^ ^^^^- length
            xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx
            ----------^^^^-------------------------- Crate number
            ---------------^^^^--------------------- Card number

        0    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx -ON Mask
        1    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx -Spare
        2    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  time in seconds since Jan 1, 1970
        3    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 0)
        4    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 0)
        5    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 1)
        6    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 1)
        7    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 2)
        8    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 2)
        9    xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 3)
        10   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 3)
        11   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 4)
        12   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 4)
        13   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 5)
        14   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 5)
        15   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 6)
        16   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 6)
        17   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Voltage encoded as a float (chan 7)
        18   xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx  actual Current encoded as a float (chan 7)
        """

        event_data_int = np.fromstring(event_data_bytes,dtype=np.uint32)
        event_data_float = np.fromstring(event_data_bytes,dtype=np.float32)

        # print(event_data_int)
        # print(event_data_float)

        enabled = np.zeros(8)     #enabled channels
        voltage = np.zeros(8)
        current = np.zeros(8)
        timestamp = event_data_int[2]

        for i,j in enumerate(enabled):
            enabled[i] = (event_data_int[0]>>(4*i) & 0xF)

            if(verbose):
                if(enabled[i] != 0):
                    print("Channel %d is enabled" % (i))
                else:
                    print("Channel %d is disabled" % (i))

        for i,j in enumerate(voltage):
            voltage[i] = event_data_float[3+(2*i)]
            current[i] = event_data_float[4+(2*i)]

        if(verbose):
            print("HV voltages: ",voltage)
            print("HV currents: ",current)

        # self.values["channel"] = channel
        data_dict={}
        data_dict["timestamp"] = timestamp
        data_dict["voltage"] = voltage
        data_dict["current"] = current
        data_dict["enabled"] = enabled

        self.decoded_values.append(data_dict)

        return data_dict
