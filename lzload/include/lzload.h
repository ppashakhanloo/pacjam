#ifndef __LZLOAD_H
#define __LZLOAD_H

#define LZLOAD_LIB        "LZLOAD_LIB"
#define LZ_LIBRARY_PATH   "LZ_LIBRARY_PATH"
#define LZLOAD_TRACE      "LZLOAD_TRACE"

#define LZLOAD_REPO "var/lib/lzload"

void* __loadsym(char **symbols);

#endif
