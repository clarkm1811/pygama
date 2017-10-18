from libc.stdio cimport *
from libc.stdint cimport *

cdef extern from "MJDSort.h":
  ctypedef struct MJDetInfo:
    #from ORCA model and HV supplies:
    int  OrcaDetID;
    int  crate, slot, chanLo, chanHi;               # digitizer crate, slot, and lo- and hi-gain chs
    int  HVCrate, HVCard, HVChan, HVMax, HVtarget;  # HV info
    char DetName[16]
    char StrName[16];                  # e.g. P42698B and C1P1D1
    int  DetType;                                   # DetType = 0 for natural, 2 for enriched
    int  PreAmpDigitizer
    int PreAmpChan;
    # # from digitizer params (HG = high gain,  LG = low gain):
    int  HGChEnabled, HGPreSumEnabled, HGPostrecnt, HGPrerecnt;
    int  HGTrigPolarity, HGTrigMode, HGLEDThreshold, HGTrapThreshold, HGTrapEnabled;
    int  LGChEnabled, LGPreSumEnabled, LGPostrecnt, LGPrerecnt;
    int  LGTrigPolarity, LGTrigMode, LGLEDThreshold, LGTrapThreshold, LGTrapEnabled;
    # # from controller card params:
    int   CCnum;                                    # controller card ID
    int   pulseHighTime, pulseLowTime, pulserEnabled;
    int   amplitude, attenuated, finalAttenuated;
    float baselineVoltage;                          # first-stage preamp baseline at zero bias
    int   PTcrate, PTslot, PTchan;                  # pulser-tag crate, clot, ch
    double HGcalib[10]
    double LGcalib[10];                # energy calibration coefficients

  ctypedef struct MJRunInfo:
    int    runNumber, runType, quickStart;
    char   filename[256]
    char orcaname[256]
    char date[32];
    int    refTime, startTime;                       # CHECK ME; enough bits?
    int    dataId[32]
    int dataIdG, idNum;               # data stream IDs
    char   decoder[32][32];                          #             and types
    int    nGe;                                      # number of Ge detectors
    int    nGD, GDcrate[20], GDslot[20];             # Ge digitizer crate and slot info
    int    nPT, PTcrate[16], PTslot[16], PTchan[16]; # Pulser-tag WF crate, slot, chan info
    int    nV, Vcrate[10], Vslot[10];                # Veto data crate and slot info
    char   Vtype[10][32];                            #             and types
    int    nCC, CCcrate[10], CCslot[10];             # Ge controller card crate and slot info

    int    fileHeaderLen;
    int    analysisPass;     # to allow for multiple-pass analysis of the same file
    int    firstRunNumber;   # starting run number for a data subset
    int    argc;
    char   **argv;           # arguments to calling program (normally sortrun.c)

cdef extern from "siginspect.h":
  # cdef void signalselect(FILE *f_in, MJDetInfo *detInfo, MJRunInfo *runInfo);
  cdef int16_t* parse_event_data(unsigned int* evtdat,  uint64_t* timestamp, uint32_t* energy, uint16_t* channel)
  cdef int get_next_event(FILE *f_in,  unsigned int*evtdat, int dataIdRun, int dataIdG );

cdef extern from "decode_runfile_header.h":
  cdef int decode_runfile_header(FILE *f_in, MJDetInfo *DetsReturn, MJRunInfo *runInfo);
