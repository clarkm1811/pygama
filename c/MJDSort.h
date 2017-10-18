/*
 *  MJDSort.h -- define data structures and functions used to process MJD raw data
 *  David Radford   Nov 2016
 */

#ifndef _MJD_SORT_H
#define _MJD_SORT_H


/* -------------- #defines -------------- */

#define NMJDETS 100  // max number of detectors in MJ model
#define GEVLEN 1026  // max number of 32-bit words per board-level event

#define NBDS      2  // max total number of boards (Ge digitizers + 1)
#define NCHS    200  // max total number of chs = 2*Ge(120) + 3*Veto(96) + PulserTag(8)
#define NCRATES   1  // total number of VME crates

#define PATH_TO_NONLIN_DATA   "nonlin_data"
#define E_THRESHOLDS_FILENAME "thresholds.input"
#define OB_TRAP_FILENAME      "times.input"
#define ECAL_FILENAME         "gains.input"


/* ----------- data structures ---------- */

/* define data structure to hold all required information about the MJD detectors
   and parameters from their digitizers channel, controller card, etc. */
typedef struct{
  // from ORCA model and HV supplies:
  int  OrcaDetID;
  int  crate, slot, chanLo, chanHi;               // digitizer crate, slot, and lo- and hi-gain chs
  int  HVCrate, HVCard, HVChan, HVMax, HVtarget;  // HV info
  char DetName[16], StrName[16];                  // e.g. P42698B and C1P1D1
  int  DetType;                                   // DetType = 0 for natural, 2 for enriched
  int  PreAmpDigitizer, PreAmpChan;
  // from digitizer params (HG = high gain,  LG = low gain):
  int  HGChEnabled, HGPreSumEnabled, HGPostrecnt, HGPrerecnt;
  int  HGTrigPolarity, HGTrigMode, HGLEDThreshold, HGTrapThreshold, HGTrapEnabled;
  int  LGChEnabled, LGPreSumEnabled, LGPostrecnt, LGPrerecnt;
  int  LGTrigPolarity, LGTrigMode, LGLEDThreshold, LGTrapThreshold, LGTrapEnabled;
  // from controller card params:
  int   CCnum;                                    // controller card ID
  int   pulseHighTime, pulseLowTime, pulserEnabled;
  int   amplitude, attenuated, finalAttenuated;
  float baselineVoltage;                          // first-stage preamp baseline at zero bias
  int   PTcrate, PTslot, PTchan;                  // pulser-tag crate, clot, ch
  double HGcalib[10], LGcalib[10];                // energy calibration coefficients
} MJDetInfo;

/* define data structure to hold all required information about run itself;
   dataIDs, start time, run number, etc    */
typedef struct{
  int    runNumber, runType, quickStart;
  char   filename[256], orcaname[256], date[32];
  int    refTime, startTime;                       // CHECK ME; enough bits?
  int    dataId[32], dataIdG, idNum;               // data stream IDs
  char   decoder[32][32];                          //             and types
  int    nGe;                                      // number of Ge detectors
  int    nGD, GDcrate[20], GDslot[20];             // Ge digitizer crate and slot info
  int    nPT, PTcrate[16], PTslot[16], PTchan[16]; // Pulser-tag WF crate, slot, chan info
  int    nV, Vcrate[10], Vslot[10];                // Veto data crate and slot info
  char   Vtype[10][32];                            //             and types
  int    nCC, CCcrate[10], CCslot[10];             // Ge controller card crate and slot info

  int    fileHeaderLen;
  int    analysisPass;     // to allow for multiple-pass analysis of the same file
  int    firstRunNumber;   // starting run number for a data subset
  int    argc;
  char   **argv;           // arguments to calling program (normally sortrun.c)
  // int   minChTimeDiff;     // minimum time diff for valid events in one Ge digitizer channel
} MJRunInfo;

typedef struct {
  int           evtID;          /* event/record number in the data file */
  int           evlen;          /* total length, in 32-bit words */
  int           crate;          /* digitizer crate ID */
  int           slot;           /* digitizer slot ID */
  unsigned int  orca_type;      /* orca dataId */
  unsigned int  evbuf[GEVLEN];  /* entire channel-event */
  long long int time;           /* timestamp for this channel-event */
  long long int time_offset;    /* timestamp correction for this channel-event */
  int           mod, ch;        /* module ID and channel (0-9) for gretina cards */
  int           det, chan;      /* detector (0-57) and channel (0-200) IDs */
  float         e;              /* trapmax energy (ADC units) */
  short         *sig;           /* pointer to signal (shorts) */
  int           siglen;         /* number of samples in signal */
} BdEvent;

typedef struct {
  float pos[200], fwhm[200];   // pulser energy peak positions and fwhm
  int   elo[200], ehi[200];    // pulser energy gates
  long long int pdt[200];      // pulser delta-time (us)
  long long int pt0[200];      // time of last previously observed pulser event
  long long int ccdt[10];      // pulser delta-time in CCs (us)
  long long int cct0[10];      // time of last previously observed pulser event in a CC
  int           nevts[100][8]; // number of pulser events per detector
} PTag;

typedef struct {
  float e0pos[200], e0fwhm[200];      // baseline E=0 peak mean and fwhm
  float bl[200], blrms[200];          // baseline average and rms values
  float t1[200], obt_offset[200];     // pulser t_1 and on-board-trap offset values
  int   bl_lo[200], bl_hi[200];       // baseline average limit
  int   blrms_hi[200];                // baseline rms limit
  int   blsl_lo[200], blsl_hi[200];   // baseline slope
  int   modified[200];                // values changed for given chan in ep_finalize.c
} DataClean;

typedef struct {
  float baseline[200];       // normal preamp resting baseline (ADC)m
  float tau[200];            // main preamp tau in microseconds
  float tau2[200];           // secondary tau (microseconds)
  float frac2[200];          //      and fractional amplitude
  float dcrlim[200];
  float dcr_ctc_slope[200];
  float dcr_e_slope[200];
  float e_dcr_slope[200];
  double e_dcr_gain[200];
} PZinfo;

/* ---------- function declarations ---------- */

/* read through file header and extract detector info etc from the XML
   and populate the data structure array DetsReturn.
   returns: -1 on error
            otherwise the actual number of detectors found in the header
 */
int decode_runfile_header(FILE *f_in, MJDetInfo *DetsReturn, MJRunInfo *runInfo);

/* read through channel-events in data file and build global events
   which are then passed out to eventprocess() for analysis.
   returns: -1 on error
            otherwise the actual number of channel-events processed
 */
int eventbuild(FILE *f_in, MJDetInfo *Dets, MJRunInfo *runInfo);

/* Process the global events that have been built in eventbuild()
   - extract energy, PSA cuts, etc
   - create histograms
   returns: -1 on error, +1 on bad event, 0 otherwise
 */
int eventprocess(MJDetInfo *Dets, MJRunInfo *runInfo,
                 int nChData, BdEvent *ChData[]);


/* ----------- defined in ep_util.c ----------- */

int trap_fixed(short *signal, int t0, int rise, int flat);
int trap_max(short *signal, int *tmax, int rise, int flat);
int trap_max_range(short *signal, int *tmax, int rise, int flat, int tlo, int thi);
float float_trap_fixed(float *signal, int t0, int rise, int flat);
float float_trap_max(float *signal, int *tmax, int rise, int flat);
float float_trap_max_range(float *signal, int *tmax, int rise, int flat, int tlo, int thi);

float sig_frac_time(short *signal, float fraction, int width, int tstart);
int sig_fit_t0(float *fsignal, int len, int chan, float e_adc);
double get_CTC_energy(float *fsignal, int len, int chan, float emax, int tmax,
                      MJDetInfo *Dets, int *t0, double *e_adc,
                      float *drift, float *ctc_factor);
                      // NOTE: t0, e_adc, drift, ctc_factor are all returned values

int checkForPulserEvent(MJDetInfo *Dets, MJRunInfo *runInfo,
                        int nChData, BdEvent *ChData[], PTag *pt);

int ep_init(MJDetInfo *Dets, MJRunInfo *runInfo, int module_lu[NCRATES+1][21],
            int det_lu[NBDS][16], int chan_lu[NBDS][16]);
void fillEvent(MJRunInfo *runInfo, int nChData, BdEvent *ChData[],
               int module_lu[][21], int det_lu[][16], int chan_lu[][16]);

int inl_correct(MJDetInfo *Dets, MJRunInfo *runInfo,
                short *signal_in, float *signal_out, int len, int chan);

int pulser_tag_info_write(MJRunInfo *runInfo, PTag *pt, int tell_results);
int pulser_tag_info_read(MJRunInfo *runInfo, PTag *pt);
int pulser_tag_init(MJDetInfo *Dets, MJRunInfo *runInfo, PTag *pt);

int peak_find(int *his, int lo, int hi);    // find highest-energy peak between chs lo and hi
float autopeak(int *his, int e, float *area_ret, float *fwhm_ret);
float autopeak2(int *his, int lo, int hi, float *area_ret, float *fwhm_ret);

/* ----- write signals to file, to look at with gf3 ----- */
int write_sig(short *sig, int nsamples, int chan, FILE *file);
/* ----- write histograms to file, to look at with gf3 ----- */
int write_his(int *his, int nch, int sp_id, char *sp_name, FILE *file);

int data_clean_info_write(MJRunInfo *runInfo, DataClean *dcInfo);
int data_clean_info_read(MJRunInfo *runInfo, DataClean *dcInfo);
int data_clean_init(MJRunInfo *runInfo, DataClean *dcInfo);
int data_clean(short *signal, int chan, DataClean *dcInfo);
int PZ_info_write(MJRunInfo *runInfo, PZinfo *PZI);
int PZ_info_read(MJRunInfo *runInfo, PZinfo *PZI);
int PZ_correct(short *signal, float *fsignal, int len, int chan, PZinfo *PZI);
int PZ_fcorrect(float *fsignal, int len, int chan, PZinfo *PZI);
int checkGranularity(MJDetInfo *Dets, MJRunInfo *runInfo, int nChData, BdEvent *ChData[]);
int compress_signal(short *sig_in, unsigned short *sig_out, int sig_len_in);
int decompress_signal(unsigned short *sig_in, short *sig_out, int sig_len_in);

#endif /*#ifndef _MJD_SORT_H */
