#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "siginspect.h"
#include "decode_runfile_header.h"
#include "runBits.h"

#define VERBOSE 0
#define DELTATIME 1  // resolving time for timestamp selection
#define FILTER_10MHZ 0

#define EVENT_HEADER_LEN 17
#define WF_LEN 2018


/* ========================================================== */

int16_t* parse_event_data(unsigned int*evtdat, uint64_t* timestamp, uint32_t* energy, uint16_t* channel){

    //Actually decode the event data


    uint16_t chan = (evtdat[1] & 0xf);

    *channel = chan;

    *timestamp = evtdat[3] & 0xffff;
    *timestamp = *timestamp << 32;
    *timestamp += evtdat[2];

    *energy = evtdat[3] >> 16;
    *energy += (evtdat[4] & 0x000001ff) << 16;
    //energy is in 2's complement, take abs value if necessary
    if (*energy & 0x1000000) *energy = (~*energy & 0x1ffffff) + 1;

    // printf("time %lu, energy %lu, ", timestamp, energy);
    int16_t * sig= (int16_t *) evtdat + EVENT_HEADER_LEN;
    // for (int i=0;i<WF_LEN;++i){
    //   sig[i] = sig_loc[i];
    // }
    // printf("signal: %d %d %d %d... %d %d %d\n", sig[0], sig[1], sig[2], sig[3], sig[2012-3],sig[2012-2], sig[2012-1]);
    return sig;

}

int get_next_event(FILE *f_in,  unsigned int*evtdat, int dataIdRun, int dataIdG ){
  unsigned int  head[2];
  int    board_type, evlen, current_runNumber;
  int slot, crate;
  // static int totevts=0, out_evts=0;

  if (fread(head, sizeof(head), 1, f_in) != 1) return -1;

  board_type = head[0] >> 18;
  evlen = (head[0] & 0x3ffff);

  if (board_type == dataIdRun) {
    if (fread(evtdat, 8, 1, f_in) != 1) return -1;
    if (head[1] & 0x21) {
      printf("------- START Run %d at %d\n", evtdat[0], evtdat[1]);
      current_runNumber = evtdat[0];
    }
    return 0;
  }

  if (board_type != dataIdG) {
    if (evlen > 10000) {
      printf("\n >>>> ERROR: Event length too long??\n"
             " >>>> This file is probably corruped, ending scan!\n");
      return -1;
    }
    fseek(f_in, 4*(evlen-2), SEEK_CUR);
    return 0;
  }

  slot  = (head[1] >> 16) & 0x1f;
  crate = (head[1] >> 21) & 0xf;

  if (crate < 0 || crate > NCRATES || slot  < 0 || slot > 20) {
    printf("ERROR: Illegal VME crate or slot number %d %d\n", crate, slot);
    if (fread(evtdat, sizeof(int), evlen-2, f_in) != evlen-2) return -1;
    return -1;
  }

  /* ========== read in the rest of the event data ========== */
  if (fread(evtdat, sizeof(int), evlen-2, f_in) != evlen-2) {
    printf("  No more data...\n");
    return -1;
  }

  // ++out_evts;
  // if (++totevts % 2000 == 0) {
  //   printf(" %8d evts in, %d out\n", totevts, out_evts); fflush(stdout);
  // }
  return 1;
}
