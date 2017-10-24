#ifndef _SIG_INSPECT_H
#define _SIG_INSPECT_H

int16_t* parse_event_data(unsigned int* evtdat,  uint64_t* timestamp, uint32_t* energy, uint16_t* channel);
int get_next_event(FILE *f_in,  unsigned int*evtdat, int dataIdRun, int dataIdG, int* slotout, int* crateout  );
// void signalselect(FILE *f_in, MJDetInfo *detInfo, MJRunInfo *runInfo);

#endif
