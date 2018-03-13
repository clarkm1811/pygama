from abc import ABCMeta, abstractmethod
import struct
import numpy as np
import sys
import matplotlib.pyplot as plt

class Data_Loader(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def decode_event(self,event_data_bytes):
        pass

    # @abstractmethod
    # def decode_header(self):
    #     pass

    def get_next_event(f_in, dataIdRun, dataIdG):
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

        # print(head)
        # print("event length: ",record_length)
        # print("data id: ",data_id)
        # print("slot: ", slot)
        # print("crate: ", crate)
        # print("reserved value: ", reserved)

        # if (crate < 0 or crate > NCRATES or slot  < 0 or slot > 20):
        #     print("ERROR: Illegal VME crate or slot number %d %d\n" %( crate, slot))
        #     raise Exception("Encountered an invalid value of the crate or slot number...")

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
        # a = Data_Loader()
        # subs = a.__subclasses__()
        names = []
        for sub in Data_Loader.__subclasses__():
            # print(sub.__name__)
            for subsub in sub.__subclasses__():
                # print(subsub.__name__)
                try:
                    a = subsub()
                    n = a.get_name()
                    # print("name: ",n)
                    names.append(n)
                except Exception as e:
                    print(e)
                    pass

        return names
    
    def get_decodable_ids(decoders,name_to_id):
        decodable_ids = []
        for value in decoders:
            print(value)        
            try:
                decodable_ids.append(name_to_id[value])
                decodable_names.append(value)
            except KeyError as e:
                print("No instances of ",value, " produced data in this run...")

        return decodable_ids

    def get_next_event_old(f_in, dataIdRun, dataIdG):
        """
            Gets the next event, and some basic information about it \n
            Takes the file pointer as input \n
            Outputs: \n
                result: Was it successful in getting the next event? Maybe this could be handled with exceptions instead... \n
                event_data: a byte array of the data produced by the card (could be header + data) \n
                slot: \n
                crate: \n
                data_id: This is the idenitifier for the type of data-taker this is \n
                board_id: This is\n
        """
        # int get_next_event(FILE *f_in,  unsigned int*evtdat, int dataIdRun, int dataIdG, int* slotout, int* crateout, unsigned short* board_id_out ){
        head = np.zeros(2)
        data_id = None
        board_id = 0
        board_type, evlen, current_runNumber = [0,0,0]
        slot, crate = [0,0]
        NCRATES = 10

        try:
            head = f_in.read(2)
        except:
            # print("Failed to read in the event orca header. Quitting...")
            print(head)
            raise Exception("Failed top read in the event orca header.")
            # sys.exit()

        # if (f_in.read(len(head)) != 1):
        #     return -1

        # board_type = head[1] >> 2
        # evlen = (head[0] & 0xffff) + (head[1]&0x3)<<16
        # data_id = (head[2] & 0xffff)

        # if(head[3] != 0):
        #     print("That should have a zero in the top of word 3...")

        board_type = head[0] >> 18
        evlen = (head[0] & 0x3ffff)
        board_id = (head[1] & 0xffff)

        # print(head)
        # print("Board type: ", board_type)
        # print("event length: ",evlen)
        # print("data id: ",data_id)
        # print("data ID G: ", dataIdG)
        # print("data ID Run: ", dataIdRun)

        if (data_id == dataIdRun):
            try:
                event_data = f_in.read(1)
            # if (fread(evtdat, 8, 1, f_in) != 1):
                status = -1
            except:
                raise Exception("Failed to read in a word of the run type data?")
                status = 0

            # if (head[1] & 0x21):
            #     #// printf("------- START Run %d at %d\n", evtdat[0], evtdat[1]);
            #     current_runNumber = evtdat[0]
            # return 0

        # if (board_type != dataIdG):
        #     if (evlen > 10000):
        #         print("\n >>>> ERROR: Event length too long??\n")
        #         print(" >>>> This file is probably corrupted, ending scan!\n")
        #         status = -1
            
        #     f_in.seek(4*(evlen-2))#, SEEK_CUR)
        #     status = 0

        slot  = (head[1] >> 16) & 0x1f
        crate = (head[1] >> 21) & 0xf

        print("slot: ", slot)
        print("crate: ", crate)
        # slotout = slot
        # crateout = crate
        # board_id_out = board_id

        if (crate < 0 or crate > NCRATES or slot  < 0 or slot > 20):
            print("ERROR: Illegal VME crate or slot number %d %d\n" %( crate, slot))
            raise Exception("Encountered an invalid value of the crate or slot number...")

            # if (len(f_in.read(evtdat, sizeof(int), evlen-2, f_in) != evlen-2):
            #     return -1
            status = -1
        

        # /* ========== read in the rest of the event data ========== */
        # if ( != evlen-2):
        try:
            event_data = f_in.read(evlen*2-2)

        except :
            print("  No more data...\n")
            raise EOFError
            status = -1
        

        # // ++out_evts;
        # // if (++totevts % 2000 == 0) {
        # //   printf(" %8d evts in, %d out\n", totevts, out_evts); fflush(stdout);
        # // }
        # status = 1
        return event_data, slot, crate, board_id, data_id


class Digitizer(Data_Loader):
    def decode_event(self,event_data_bytes):
        pass

    # def decode_header():
    #     pass

class Gretina4m_Decoder(Digitizer):
    def __init__(self):
        self.values = dict()
        self.event_header_length = 30
        self.wf_length = 2018

        self.name = 'ORGretina4M'

        return

    def get_name(self):
        return self.name
    
    def decode_event(self,event_data_bytes):
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
        board_id =(event_data[2]&0xFFF0)>>4     # unused
        timestamp = event_data[4] + (event_data[5]<<16) + (event_data[6]<<32)
        energy = event_data[7] + ((event_data[8]&0x7FFF)<<16)
        wf_data = event_data[self.event_header_length:]#(self.event_header_length+self.wf_length)*2]
        

        # print(len(wf_data))
        # print(len(event_data))

        # plt.plot(wf_data)
        # plt.show()

        
        # sys.exit()

        # d = []
        # for v in event_data[:self.event_header_length*2]:
        #     d.append(hex(v))
        # print(d)

        # print(event_data[0])
        # print(event_data[1])
        
        # channel = event_data[4] & 0xf
        # timestamp = ((event_data[8]) + event_data[9]<<8  + event_data[10]<<16 + event_data[11]<<24 + event_data[12]<<32 + event_data[13]<<40)
        # energy = (event_data[14] + event_data[15]<<8 + event_data[16]<<16)

        # wf_data = event_data[self.event_header_length*4:self.event_header_length*4+self.wf_length*4]

        self.values["channel"] = channel
        self.values["timestamp"] = timestamp
        self.values["energy"] = energy
        self.values["waveform"] = wf_data

        # print(self.values)
        # print("   channel: %lu, energy: %lu, time: %lu" % (channel, energy, timestamp))
        # print(channel)
        # print(timestamp)
        # print(energy)
        return timestamp, energy, channel, wf_data

    def format_data(self,energy,timestamp,crate_card_chan,wf_arr):
        """
        Format the values that we get from this card into a panda-friendly format.
        """

        data = {
            "energy": energy,
            "timestamp": timestamp,
            "channel": crate_card_chan,
            "waveform": [np.copy(wf_arr)]
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
        self.values = dict()
        self.event_header_length = 1

        self.name = 'ORSIS3302'
        return

    def get_name(self):
        return self.name

    def decode_event(self,event_data_bytes):
        pass

