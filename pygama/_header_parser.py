from plistlib import readPlistFromBytes
import sys

def parse_header(xmlfile):
    with open(xmlfile, 'rb') as xmlfile_handle:
        #read the first word:
        ba = bytearray(xmlfile_handle.read(8))

        #first 4 bytes: header length in long words
        i = int.from_bytes(ba[:4], byteorder=sys.byteorder)

        #second 4 bytes: header length in bytes
        j = int.from_bytes(ba[4:], byteorder=sys.byteorder)

        #read in the next that-many bytes
        ba = bytearray(xmlfile_handle.read(j))

        header_dict = readPlistFromBytes(ba)
        return i,j,header_dict

def get_run_number(header_dict):
    for d in (header_dict["ObjectInfo"]["DataChain"]):
        if "Run Control" in d:
            return (d["Run Control"]["RunNumber"])
    print ("No run number found in header!")
    exit()

def get_data_id(headerDict, class_name, super_name):
    #stored like this: headerDict["dataDescription"]["ORRunModel"]["Run"]["dataId"]
    #but integer needs to be bitshifted by 18

    id_int = headerDict["dataDescription"][class_name][super_name]["dataId"]

    return id_int >> 18

def get_header_dataframe_info(headerDict):
    #key by card-crate-channel
    d = []

    crates = headerDict["ObjectInfo"]["Crates"]
    for crate in crates:
        cards = crate["Cards"]
        for card in cards:
            if card["Class Name"] == "ORGretina4MModel":
                for (channum, en) in enumerate(card["Enabled"]):
                    if en == False: continue
                    ccc = (crate["CrateNumber"] << 14) + (card["Card"] << 4) + channum

                    row = { "channel": ccc,
                            "Collection Time": card["Collection Time"],
                            "Integration Time": card["Integration Time"],
                            "PreSum Enabled": card["PreSum Enabled"][channum],
                            "Prerecnt": card["Prerecnt"][channum],
                            "FtCnt": card["FtCnt"][channum],
                            "Postrecnt": card["Postrecnt"][channum],
                            "multirate_div": 2**card["Mrpsdv"][channum],
                            "multirate_sum": 10 if card["Mrpsrt"][channum] == 3 else 2 **(card["Mrpsrt"][channum]+1),
                            "channel_div": 2**card["Chpsdv"][channum],
                            "channel_sum": 10 if card["Chpsrt"][channum] == 3 else 2 **(card["Chpsrt"][channum]+1),
                    }
                    d.append(row)
    return d
