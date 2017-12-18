from libc.stdio cimport *
from libc.stdint cimport *

cdef extern from "siginspect.h":
  # cdef void signalselect(FILE *f_in, MJDetInfo *detInfo, MJRunInfo *runInfo);
  cdef int16_t* parse_event_data(unsigned int* evtdat,  uint64_t* timestamp, uint32_t* energy, uint16_t* channel)
  cdef int get_next_event(FILE *f_in,  unsigned int*evtdat, int dataIdRun, int dataIdG, int* slotout, int* crateout, uint16_t* board_id);
