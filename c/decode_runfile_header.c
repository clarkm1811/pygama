/*
   decode_runfile_header.c

   code to read through file header and extract detector info etc from the XML
   and populate the detector info data structures

   David Radford  Nov 2016
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MJDSort.h"
#include "decode_runfile_header.h"

#define NMJPTS    0  // max number of pulser-tag channels in MJ model
#define NMJSTRS   0  // max number of detector strings in MJ model
#define NMJVSEGS  0  // max number of veto segments in MJ model
#define NGEDIGS   1  // max number of GRETINA digitizers
#define NGEHV     0  // max number of Ge HV channels
#define NGeCCS    0  // max number of preamp controller cards

/*  ------------------------------------------------------------ */
/*  Use these definitions to adjust the function of this program */
#define VERBOSE   0
#define VERB_DIG  0
#define FIX_PT1_SLOT 1    // apply fix to pulser tag 1 (crate 1 slot 8 -> slot 10)
/*  ------------------------------------------------------------ */


/*  -- -- -- first some convenience functions -- -- -- */

#define CHECK_FOR_STRING(A) if (!strstr(line, A)) {printf("ERROR: Missing %s\n %s\n", A, line); return 1;}

/* read_int(): function to read a single integer
   into dest
   from file f_in
   using reads into string line.   (NOTE: line must be at least 256 chars!) */
int read_int(FILE *f_in, int *dest, char *line) {
  char   *c;

  fgets(line, 256, f_in);
  if (strstr(line, "<false/>")) {
    *dest = 0;
  } else if (strstr(line, "<true/>")) {
    *dest = 1;
  } else if ((c=strstr(line, "<real>")) &&
             (1 == sscanf(c+6, "%d", dest))) {
  } else if (!(c=strstr(line, "<integer>")) ||
             (1 != sscanf(c+9, "%d", dest))) {
    fprintf(stderr, "\n ERROR decoding read_int:\n %s\n", line);
    return -1;
  }
  fgets(line, 256, f_in);  // read next line of input file, for use by calling function
  return 0;
}  /* read_int() */


/* read_int_array(): function to read array of integers or booleans
   of length dest_size
   into array dest[]
   from file f_in
   using reads into string line.   (NOTE: line must be at least 256 chars!) */
int read_int_array(FILE *f_in, int *dest, int dest_size, char *line) {
  int    i;
  float  f;
  char   *c;

  fgets(line, 256, f_in);
  if (!strstr(line, "<array>")) {
    fprintf(stderr, "\n ERROR in read_int_array! Missing <array>...\n %s\n", line);
    return -1;
  }
  fgets(line, 256, f_in);
  for (i = 0; i<dest_size; i++) {
    if (strstr(line, "<false/>")) {
      dest[i] = 0;
    } else if (strstr(line, "<true/>")) {
      dest[i] = 1;
    } else if ((c=strstr(line, "<real>"))) {
      if (1 != sscanf(c+6, "%f", &f)) {
        fprintf(stderr, "\n ERROR decoding read_int_array:\n %s\n", line);
        return -1;
      }
      dest[i] = lrintf(f);
    } else if (!(c=strstr(line, "<integer>")) ||
               (1 != sscanf(c+9, "%d", &dest[i]))) {
      fprintf(stderr, "\n ERROR decoding read_int_array:\n %s\n", line);
      return -1;
    }
    fgets(line, 256, f_in);
  }
  if (!strstr(line, "</array>")) {
    fprintf(stderr, "\n ERROR in read_int_array! Missing </array>... dest_size too small?\n %s\n", line);
    return -1;
  }

  fgets(line, 256, f_in);  // read next line of input file, for use by calling function
  // printf("read_int_array() returning %d values\n", i);
  return i;
}  /* read_int_array() */


/* read_float_array(): function to read array of floats
   of length dest_size
   into array dest[]
   from file f_in
   using reads into string line.   (NOTE: line must be at least 256 chars!) */
int read_float_array(FILE *f_in, float *dest, int dest_size, char *line) {
  int    i, j;
  char   *c;

  fgets(line, 256, f_in);
  if (!strstr(line, "<array>")) {
    fprintf(stderr, "\n ERROR in read_float_array! Missing <array>...\n %s\n", line);
    return -1;
  }
  fgets(line, 256, f_in);
  for (i = 0; i<dest_size; i++) {
    j=0;
    if ((c=strstr(line, "<integer>"))) j = sscanf(c+9, "%f", &dest[i]);
    if ((c=strstr(line, "<real>")))    j = sscanf(c+6, "%f", &dest[i]);
    if (j!=1) {
      fprintf(stderr, "\n ERROR decoding read_float_array [%d]:\n %s\n", i, line);
      return -1;
    }
    fgets(line, 256, f_in);
  }
  if (!strstr(line, "</array>")) {
    fprintf(stderr, "\n ERROR in read_float_array! Missing </array>... dest_size too small?\n %s\n", line);
    return -1;
  }

  fgets(line, 256, f_in);  // read next line of input file, for use by calling function
  // printf("read_float_array() returning %d values\n", i);
  return i;
}  /* read_float_array() */


/* check_false(): function to check array of booleans are all false
   and that string check is in first line.
   array length = size
   uses reads into string line   (NOTE: line must be at least 256 chars!)
   from file f_in */
int check_false(FILE *f_in, int size, char *line, char *check) {
  int    i;

  CHECK_FOR_STRING(check);
  fgets(line, 256, f_in);
  if (!strstr(line, "<array>")) {
    fprintf(stderr, "\n ERROR in check_false %s! Missing <array>...\n %s\n", check, line);
    return -1;
  }
  for (i = 0; i<size; i++) {
    fgets(line, 256, f_in);
    if (!strstr(line, "<false/>")) {
      fprintf(stderr, "\n check_false %s: %d NOT false\n %s\n", check, i, line);
      return -1;
    }
  }
  fgets(line, 256, f_in);
  if (!strstr(line, "</array>")) {
    fprintf(stderr, "\n ERROR in check_false %s! Missing </array>...\n %s\n", check, line);
    return -1;
  }
  fgets(line, 256, f_in);  // read next line of input file, for use by calling function
  return 0;
}  /* check_false() */


/* discard(): function to discard num lines from file f_in
   and that string check is in first line.
   uses reads into string line   (NOTE: line must be at least 256 chars!) */
int discard(FILE *f_in, int num, char *line, char *check) {
  int    i;

  CHECK_FOR_STRING(check);
  for (i=0; i<num; i++) fgets(line, 256, f_in);
  return 0;
}  /* discard() */


/* ---------------------------------------------------------------------------
   decode_runfile_header():
   read through file header and extract detector info etc from the XML
   and populate the data structure array DetsReturn.
   input:   f_in (opened file pointer)
   output:  populated data structures DetsReturn[NMJDETS]
   returns: -1 on error
   .        otherwise the actual number of detectors found in the header
   --------------------------------------------------------------------------- */

int decode_runfile_header(FILE *f_in, MJDetInfo *DetsReturn, MJRunInfo *runInfo) {

  int    i, j, k, jj, kk, crateNum, slotNum, buf[25], reclen, reclen2;
  int    dataId[32], idNum = 0, dataIdG = 0;
  char   *c, line[256];

  typedef struct{    // Ge WF digitizer info from ORGretin4MModel
    int  crate, slot, serial;
    int  ClockSource, ClockPhase, CollectionTime, IntegrationTime, DownSample;
    int  NoiseWindow;
    int  Chpsdv[10], Chpsrt[10], Mrpsdv[10], Mrpsrt[10];
    int  ChEnabled[10], PreSumEnabled[10], FtCnt[10], Postrecnt[10], Prerecnt[10];
    int  TrigPolarity[10], TrigMode[10], LEDThreshold[10], TrapThreshold[10], TrapEnabled[10];
    int  forceFullInitCard, forceFullInitCh[10];
  } GeDigInfo;

  MJDetInfo   MJMDets[NMJDETS];
  GeDigInfo   GeDig[NGEDIGS];
  int         nMJDets=0, nMJPTs=0, nMJStrs=0, nMJVSegs=0;
  int         nGeHV=0, nGeDig=0, nGeCC=0;

  /* initialize a few things */
  runInfo->dataIdG = runInfo->idNum = runInfo->nV = 0;

  /* read unformatted data and plist at start of orca file */
  fread(buf, sizeof(buf), 1, f_in);
  reclen = (unsigned int) buf[0];   // length of header in long words
  reclen2 = (unsigned int) buf[1];  // length of header in bytes

  /* loop through the lines of the XML data until we find the end of the plist */
  while (fgets(line, sizeof(line), f_in) && strncmp(line, "</plist>", 8)) {

    /* decode some run information */
    /* =========================== */
    if (strstr(line, "<key>date</key>")) {
      fgets(line, sizeof(line), f_in);
      CHECK_FOR_STRING("</string>");
      *(strstr(line, "</string>")) = '\0';
      strncpy(runInfo->date, strstr(line, "<string>")+8, 32);      // run date and time
    }
    if (strstr(line, "<key>documentName</key>")) {
      fgets(line, sizeof(line), f_in);
      CHECK_FOR_STRING("</string>");
      *(strstr(line, "</string>")) = '\0';
      strncpy(runInfo->orcaname, strstr(line, "<string>")+8, 256); // ORCA setup file name
    }
    if (strstr(line, "<key>RunNumber</key>"))
      if (read_int(f_in, &runInfo->runNumber, line)) return -1;    // run number
    if (strstr(line, "<key>quickStart</key>"))
      if (read_int(f_in, &runInfo->quickStart, line)) return -1;   // quick start flag
    if (strstr(line, "<key>refTime</key>"))
      if (read_int(f_in, &runInfo->refTime, line)) return -1;      // reference time? CHECK ME; enough bits?
    if (strstr(line, "<key>runType</key>"))
      if (read_int(f_in, &runInfo->runType, line)) return -1;      // run bits?
    if (strstr(line, "<key>startTime</key>"))
      if (read_int(f_in, &runInfo->startTime, line)) return -1;    // start time;     CHECK ME; enough bits?

    /* decode readout dataId's */
    /* ======================= */
    if (strstr(line, "<key>dataId</key>")) {
      if (idNum >= 32) {
        printf("ERROR: More than 32 dataIDs found in file header! Extra ones ingnored.\n\n");
      } else {
        while (!(c = strstr(line, "<integer>"))) fgets(line, sizeof(line), f_in);
        sscanf(c+9, "%d", &j);
        runInfo->dataId[idNum] = dataId[idNum] = j >> 18;
        while (!strstr(line, "<key>decoder</key>")) fgets(line, sizeof(line), f_in);
        while (!(c = strstr(line, "</string>"))) fgets(line, sizeof(line), f_in);
        *c = '\0';
        c = strstr(line, "<string>")+8;
        strncpy(runInfo->decoder[idNum], c, 32);
        if (VERBOSE) printf(" dataId = %2d  -> %s\n", j>>18, c);
        if (strstr(line, "Gretina4M")) runInfo->dataIdG = dataIdG = dataId[idNum];
        runInfo->idNum = ++idNum;
      }
    }

    /* decode card info             */
    /*    GRETINA digitizers        */
    /* ============================ */
    // first read GRETINA digitizer BLREnabled array - seems to be out of order?
    if (strstr(line, "<key>Baseline Restore Enabled</key>")) {
      // just check that these are all false, don't bother to keep the values
      if (check_false(f_in, 10, line, "<key>Baseline Restore Enabled</key>")) return -1;
    }

    // read Card slot number
    if (strstr(line, "<key>Card</key>")) {
      fgets(line, sizeof(line), f_in);
      if (!(c = strstr(line, "<integer>"))) {
        fprintf(stderr, "\n ERROR in Card format! Missing <integer>...\n %s\n", line);
        return -1;
      }
      if (1 != sscanf(c+9, "%d", &slotNum)) {
        fprintf(stderr, "\n ERROR decoding Card slot number:\n %s\n", line);
        return -1;
      }
      fgets(line, sizeof(line), f_in);
      if (strstr(line, "<key>Chpsdv</key>")) { //GRETINA v1.07 card (why does Chpdsv come before Class Name??)
        /* ------------- GRETINA4M digitizer card info ------------ */
        if (VERBOSE) printf(" GRETINA card found! Slot %d\n", slotNum);
        if (nGeDig >= NGEDIGS) {
          fprintf(stderr, "\n ERROR: Maximum number of GRETINA digitizers (%d) reached!\n\n", nGeDig);
          return -1;
        }

        GeDig[nGeDig].crate = -99;     // crate number not yet known; -99 is a space holder to be replaced later
        GeDig[nGeDig].slot = slotNum;
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Chpsdv[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Chpsrt</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Chpsrt[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Class Name</key>");
        fgets(line, sizeof(line), f_in);
        CHECK_FOR_STRING("<string>ORGretina4MModel</string>");
        fgets(line, sizeof(line), f_in);
        CHECK_FOR_STRING("<key>Clock Phase</key>");
        if (read_int(f_in, &GeDig[nGeDig].ClockPhase, line)) return -1;
        CHECK_FOR_STRING("<key>Clock Source</key>");
        if (read_int(f_in, &GeDig[nGeDig].ClockSource, line)) return -1;
        CHECK_FOR_STRING("<key>Collection Time</key>");
        if (read_int(f_in, &GeDig[nGeDig].CollectionTime, line)) return -1;
        if (check_false(f_in, 10, line, "<key>Debug Mode</key>")) return -1;
        CHECK_FOR_STRING("<key>Down Sample</key>");
        if (read_int(f_in, &GeDig[nGeDig].DownSample, line)) return -1;
        CHECK_FOR_STRING("<key>Enabled</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].ChEnabled[0], 10, line)) return -1;
        if (discard(f_in, 2, line, "<key>Ext Trig Length</key>")) return -1;
        if (discard(f_in, 2, line, "<key>External Window</key>")) return -1;
        CHECK_FOR_STRING("<key>FtCnt</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].FtCnt[0], 10, line)) return -1;
        if (discard(f_in, 2, line, "<key>Hist E Multiplier</key>")) return -1;
        CHECK_FOR_STRING("<key>Integration Time</key>");
        if (read_int(f_in, &GeDig[nGeDig].IntegrationTime, line)) return -1;
        CHECK_FOR_STRING("<key>LED Threshold</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].LEDThreshold[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Mrpsdv</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Mrpsdv[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Mrpsrt</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Mrpsrt[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Noise Window</key>");
        if (read_int(f_in, &GeDig[nGeDig].NoiseWindow, line)) return -1;
        // just check that these are all false, don't bother to keep the values
        if (check_false(f_in, 10, line, "<key>PZ Trace Enabled</key>")) return -1;
        if (check_false(f_in, 10, line, "<key>Pile Up</key>")) return -1;
        if (discard(f_in, 2, line, "<key>Pile Up Window</key>")) return -1;
        if (check_false(f_in, 10, line, "<key>Pole Zero Enabled</key>")) return -1;
        if (discard(f_in, 13, line, "<key>Pole Zero Multiplier</key>")) return -1;
        CHECK_FOR_STRING("<key>Postrecnt</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Postrecnt[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>PreSum Enabled</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].PreSumEnabled[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Prerecnt</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].Prerecnt[0], 10, line)) return -1;
        if (strstr(line, "<key>Serial Number</key>")) {
          if (read_int(f_in, &GeDig[nGeDig].serial, line)) return -1;
        }
        CHECK_FOR_STRING("<key>TPol</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].TrigPolarity[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>TRAP Threshold</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].TrapThreshold[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Trap Enabled</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].TrapEnabled[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>Trigger Mode</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].TrigMode[0], 10, line)) return -1;
        if (discard(f_in, 2, line, "<key>baseAddress</key>")) return -1;
        CHECK_FOR_STRING("<key>forceFullInit</key>");
        if (10 != read_int_array(f_in, &GeDig[nGeDig].forceFullInitCh[0], 10, line)) return -1;
        CHECK_FOR_STRING("<key>forceFullInitCard</key>");
        if (read_int(f_in, &GeDig[nGeDig].forceFullInitCard, line)) return -1;
        nGeDig++;
      } // end of digitizer card info

      if (strstr(line, "<key>Class Name</key>")) {
        fgets(line, sizeof(line), f_in);
      } // end of HV card info
    }

    /* decode crate info */
    /* ================ */
    if (strstr(line, "<key>CrateNumber</key>")) {
      fgets(line, sizeof(line), f_in);
      if (!(c = strstr(line, "<integer>"))) {
        fprintf(stderr, "\n ERROR in CrateNumber format! Missing <integer>...\n %s\n", line);
        return -1;
      }
      if (1 != sscanf(c+9, "%d", &crateNum)) {
        fprintf(stderr, "\n ERROR decoding CrateNumber:\n %s\n", line);
        return -1;
      }
      for (j=0; j<nGeDig; j++) {
        if (GeDig[j].crate == -99) {  // replace space holders now that we know the crate number
          GeDig[j].crate = crateNum;
          if (VERBOSE)
            printf(" >>> GeDig # %2d crate %d, slot %2d\n", j, GeDig[j].crate, GeDig[j].slot);
        }
      }
    }
  }  /* ============== end of loop reading XML ================= */

  /* report results summary */
  if (dataIdG == 0) {
    printf("\n ERROR; no data ID found for Gretina4M data!\n\n");
  } else if (VERBOSE) {
    printf("\n Data ID %d found for Gretina4M data\n\n", dataIdG);
  }
  // if (!strstr(runInfo->argv[0], "rundiff")) {
    printf("%3d veto segments\n", nMJVSegs);
    printf("%3d Ge HV channels\n", nGeHV);
    printf("%3d Controller cards and %d Pulser-tag chs\n", nGeCC, nMJPTs);
    printf("%3d GRETINA WF digitizers\n", nGeDig);
    printf("%3d Detectors in %d strings\n\n", nMJDets, nMJStrs);
  // }
  /* add CnPnDn names and re-order detector IDs in CnPnDn order */
  for (i=0; i<1; i++) {
    sprintf(MJMDets[i].StrName, "Det%.2d", i);
    sprintf(MJMDets[i].DetName, "Det%.2d", i);
    MJMDets[i].crate = GeDig[0].crate;
    MJMDets[i].slot = GeDig[0].slot;
    MJMDets[i].chanHi = i;
    MJMDets[i].chanLo = i+5;
    if (VERBOSE)  // report results
      printf(" Detector %2d  %8s %9s   HG ch %d,%2.2d,%d"
             "   HV %d,%2.2d,%d   MaxV %d\n",
             i, MJMDets[i].StrName,
             MJMDets[i].DetName, MJMDets[i].crate,  MJMDets[i].slot,   MJMDets[i].chanHi,
             MJMDets[i].HVCrate, MJMDets[i].HVCard, MJMDets[i].HVChan, MJMDets[i].HVMax);
  }
  nMJDets = i;
  /*  --------------- give details of digizer settings ------------------ */
  if (VERB_DIG) {
    for (jj=0; jj<nGeDig; jj++) {
      for (kk=0; kk<10; kk++) {
        if (GeDig[0].ChEnabled[kk]) break;  // find first channel that is enabled
      }
      if (kk < 10) break;
    }
    printf("Common digitizer values:\n"
           "  ClockSource       %4d \n"
           "  CollectionTime    %4d        IntegrationTime   %4d\n"
           "  DownSample        %4d        NoiseWindow       %4d\n"
           "  Mrpsdv[]          %4d        Mrpsrt[]          %4d\n"
           "  PreSumEnabled[]   %4d        FtCnt[]           %4d\n"
           "  Postrecnt[]       %4d        Prerecnt[]        %4d\n"
           "  TrigPolarity[]    %4d        TrigMode[]        %4d\n"
           "  TrapEnabled[]     %4d\n"
           "  forceFullInitCard %4d        forceFullInitCh[] %4d\n",
           GeDig[jj].ClockPhase, GeDig[jj].CollectionTime, GeDig[jj].IntegrationTime,
           GeDig[jj].DownSample, GeDig[jj].NoiseWindow, GeDig[jj].Mrpsdv[kk], GeDig[jj].Mrpsrt[kk],
           GeDig[jj].PreSumEnabled[kk], GeDig[jj].FtCnt[kk], GeDig[jj].Postrecnt[kk],
           GeDig[jj].Prerecnt[kk], GeDig[jj].TrigPolarity[kk], GeDig[jj].TrigMode[kk],
           GeDig[jj].TrapEnabled[kk], GeDig[jj].forceFullInitCard, GeDig[jj].forceFullInitCh[kk]);
    printf("Variable digitizer values:\n"
           "  ClockPhase        %4d\n"
           "  Chpsdv[]          %4d        Chpsrt[]          %4d\n\n",
           GeDig[jj].ClockSource,
           GeDig[jj].Chpsdv[kk], GeDig[jj].Chpsrt[kk]);

    for (j=0; j<nGeDig; j++) {  // slot
      for (k=0; k<10; k++) {    // ch
        if (GeDig[j].ChEnabled[k]) {
          if (GeDig[j].ClockSource         != GeDig[jj].ClockSource        ||
              GeDig[j].CollectionTime      != GeDig[jj].CollectionTime     ||
              GeDig[j].IntegrationTime     != GeDig[jj].IntegrationTime    ||
              GeDig[j].DownSample          != GeDig[jj].DownSample         ||
              GeDig[j].NoiseWindow         != GeDig[jj].NoiseWindow        ||
              GeDig[j].Mrpsdv[k]           != GeDig[jj].Mrpsdv[kk]         ||
              GeDig[j].Mrpsrt[k]           != GeDig[jj].Mrpsrt[kk]         ||
              GeDig[j].PreSumEnabled[k]    != GeDig[jj].PreSumEnabled[kk]  ||
              GeDig[j].FtCnt[k]            != GeDig[jj].FtCnt[kk]          ||
              GeDig[j].Postrecnt[k]        != GeDig[jj].Postrecnt[kk]      ||
              GeDig[j].Prerecnt[k]         != GeDig[jj].Prerecnt[kk]       ||
              GeDig[j].TrigPolarity[k]     != GeDig[jj].TrigPolarity[kk]   ||
              GeDig[j].TrigMode[k]         != GeDig[jj].TrigMode[kk]       ||
              GeDig[j].TrapEnabled[k]      != GeDig[jj].TrapEnabled[kk]    ||
              GeDig[j].forceFullInitCard   != GeDig[jj].forceFullInitCard  ||
              GeDig[j].forceFullInitCh[k]  != GeDig[jj].forceFullInitCh[kk]) {
            printf("Digitizer in crate %d slot %2d ch %d is enabled,"
                   " but has different values than above!\n",
                   GeDig[j].crate, GeDig[j].slot, k);
            printf("\n Digitizer values:\n"
                   " ClockSource       %4d\n"
                   " CollectionTime    %4d        IntegrationTime   %4d\n"
                   " DownSample        %4d        NoiseWindow       %4d\n"
                   " Mrpsdv[]          %4d        Mrpsrt[]          %4d\n"
                   " PreSumEnabled[]   %4d        FtCnt[]           %4d\n"
                   " Postrecnt[]       %4d        Prerecnt[]        %4d\n"
                   " TrigPolarity[]    %4d        TrigMode[]        %4d\n"
                   " TrapEnabled[]     %4d\n"
                   " forceFullInitCard %4d        forceFullInitCh[] %4d\n\n",
                   GeDig[j].ClockSource, GeDig[j].CollectionTime, GeDig[j].IntegrationTime,
                   GeDig[j].DownSample, GeDig[j].NoiseWindow, GeDig[j].Mrpsdv[k], GeDig[j].Mrpsrt[k],
                   GeDig[j].PreSumEnabled[k], GeDig[j].FtCnt[k], GeDig[j].Postrecnt[k],
                   GeDig[j].Prerecnt[k], GeDig[j].TrigPolarity[k], GeDig[j].TrigMode[k],
                   GeDig[j].TrapEnabled[k], GeDig[j].forceFullInitCard, GeDig[j].forceFullInitCh[k]);
          }
        }
      }
    }
  } // --------------- end of digizer settings report --------------------

  /* Figure out which digitizer slots digitize the WFs
     from the preamps controlled by each of the controller cards  */
  /* store actual HV target values, digitizer channel info, and CC card info
     ----------------------------------------------------------------------- */
  k = 0;
  for (i=0; i<nMJDets; i++) {
    // GRETINA digitizer values
    for (j=0; j<nGeDig; j++) {
      if (MJMDets[i].crate == GeDig[j].crate &&
          MJMDets[i].slot  == GeDig[j].slot) {
        k = MJMDets[i].chanHi;
        MJMDets[i].HGChEnabled     = GeDig[j].ChEnabled[k];
        MJMDets[i].HGPreSumEnabled = GeDig[j].PreSumEnabled[k];
        MJMDets[i].HGPostrecnt     = GeDig[j].Postrecnt[k];
        MJMDets[i].HGPrerecnt      = GeDig[j].Prerecnt[k];
        MJMDets[i].HGTrigPolarity  = GeDig[j].TrigPolarity[k];
        MJMDets[i].HGTrigMode      = GeDig[j].TrigMode[k];
        MJMDets[i].HGLEDThreshold  = GeDig[j].LEDThreshold[k];
        MJMDets[i].HGTrapThreshold = GeDig[j].TrapThreshold[k];
        MJMDets[i].HGTrapEnabled   = GeDig[j].TrapEnabled[k];
        k = MJMDets[i].chanLo;
        MJMDets[i].LGChEnabled     = GeDig[j].ChEnabled[k];
        MJMDets[i].LGPreSumEnabled = GeDig[j].PreSumEnabled[k];
        MJMDets[i].LGPostrecnt     = GeDig[j].Postrecnt[k];
        MJMDets[i].LGPrerecnt      = GeDig[j].Prerecnt[k];
        MJMDets[i].LGTrigPolarity  = GeDig[j].TrigPolarity[k];
        MJMDets[i].LGTrigMode      = GeDig[j].TrigMode[k];
        MJMDets[i].LGLEDThreshold  = GeDig[j].LEDThreshold[k];
        MJMDets[i].LGTrapThreshold = GeDig[j].TrapThreshold[k];
        MJMDets[i].LGTrapEnabled   = GeDig[j].TrapEnabled[k];
        break;
      }
    }

    /* write out final results */
    if (VERBOSE) {
      if (i%20 == 0)
        printf("#    DetID      pos      name     HiGain GAT Enab Thresh     HVch  MaxV Target"
               "     Pulser times enab  ampl atten\n");
      printf(" %3d  was %2d %8s %9s   %d,%2.2d,%d %4d %3d %6d %3d,%2.2d,%d"
             " %5d %6d %9d %7d %3d %5d %3d %d\n", i,
             MJMDets[i].OrcaDetID,       MJMDets[i].StrName,
             MJMDets[i].DetName,         MJMDets[i].crate,
             MJMDets[i].slot,            MJMDets[i].chanHi,
             MJMDets[i].crate*512 + MJMDets[i].slot*16 + MJMDets[i].chanHi,
             MJMDets[i].HGChEnabled,     MJMDets[i].HGTrapThreshold,
             MJMDets[i].HVCrate,         MJMDets[i].HVCard,
             MJMDets[i].HVChan,          MJMDets[i].HVMax,
             MJMDets[i].HVtarget,
             MJMDets[i].pulseHighTime,   MJMDets[i].pulseLowTime,
             MJMDets[i].pulserEnabled,   MJMDets[i].amplitude,
             MJMDets[i].attenuated,      MJMDets[i].finalAttenuated);
    }
  }
  printf("copying...\n");
  /* copy results to returned data structures */
  for (i=0; i<nMJDets; i++)
    memcpy(&DetsReturn[i], &MJMDets[i], sizeof(MJDetInfo));
  runInfo->nGe = nMJDets;

  for (i=0; i<nGeDig; i++) {
    runInfo->GDcrate[i] = GeDig[i].crate;
    runInfo->GDslot[i]  = GeDig[i].slot;
  }
  runInfo->nGD = nGeDig;
  runInfo->nPT = nMJPTs;
  runInfo->nCC = nGeCC;

  if (VERBOSE)
    printf("File is at %d %ld; moving to reclen*4 = %d\n\n", reclen2+8, ftell(f_in), reclen*4);
  //fseek(f_in, reclen*4, SEEK_SET); // position file at start of events data
  fread(line, reclen*4-reclen2-8, 1, f_in);
  if (VERBOSE) printf("\n All Done.\n\n");
  runInfo->fileHeaderLen = reclen;

  return nMJDets;
}
/*
  typedef struct{    // pulser-tag-channel info from MJ orca model
    char Description[32];
    int  VME, Slot, Chan, PADig, PAChan;
    // char Cable[32], Type[32];
  } MJModelPT;

  typedef struct{    // Veto segment info from MJ orca model
    int  kSegmentNumber, crate, slot, chan, HVCrate, HVCard, HVChan;
  } MJModelVeto;

  typedef struct{    // Ge WF digitizer info from ORGretin4MModel
    int  crate, slot, serial;
    int  ClockSource, ClockPhase, CollectionTime, IntegrationTime, DownSample;
    int  NoiseWindow;
    int  Chpsdv[10], Chpsrt[10], Mrpsdv[10], Mrpsrt[10];
    int  ChEnabled[10], PreSumEnabled[10], FtCnt[10], Postrecnt[10], Prerecnt[10];
    int  TrigPolarity[10], TrigMode[10], LEDThreshold[10], TrapThreshold[10], TrapEnabled[10];
    int  forceFullInitCard, forceFullInitCh[10];
  } GeDigInfo;

  typedef struct{    // ControlerCard info from ORMJDPreAmpModel
    int   crate, slot;     // serial control/readout link goes to this VME crate and slot
    int   adcEnabledMask, enabled[2], attenuated[2], finalAttenuated[2];
    int   preampID, pulseHighTime, pulseLowTime, pulserMask;
    int   amplitudes[16];
    float baselineVoltages[16];
    char  detectorNames[16][16];
    int   GeSlot[2];       // slots where the Ge _signals_ are digitized
  } CCInfo;

  MJDetInfo   MJMDets[NMJDETS];
  MJModelPT   MJMPTs[NMJPTS];
  MJModelVeto MJMVSegs[NMJVSEGS];
  GeDigInfo   GeDig[NGEDIGS];
  CCInfo      GeCC[NGeCCS];
  int         nMJDets=0, nMJPTs=0, nMJVSegs=0, nGeDig=0, nGeCC=0;
*/
