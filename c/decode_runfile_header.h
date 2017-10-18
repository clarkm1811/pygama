#ifndef _MJD_DECODERUNFILE_H
#define _MJD_DECODERUNFILE_H

#include "MJDSort.h"

/* ---------------------------------------------------------------------------
   decode_runfile_header():
   read through file header and extract detector info etc from the XML
   and populate the data structure array DetsReturn.
   input:   f_in (opened file pointer)
   output:  populated data structures DetsReturn[NMJDETS]
   returns: -1 on error
   .        otherwise the actual number of detectors found in the header
   --------------------------------------------------------------------------- */

int decode_runfile_header(FILE *f_in, MJDetInfo *DetsReturn, MJRunInfo *runInfo);

#endif
