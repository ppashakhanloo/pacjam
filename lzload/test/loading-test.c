#include "lzload.h"

#include <stdio.h>

#include <sys/types.h>
#include <unistd.h>

char *floor_arr[] = { "floor", NULL };

int main(int argc, char **argv) {
  double (*_floor)(double) = __loadsym(floor_arr);

  if (fork() == 0) {
  	if (execl("/home/aspire/lzload/build/dlopen-test", (char *) NULL) < 0) {
	  printf("didnt run\n");
	}
  } else {
  	double (*_floor)(double) = __loadsym(floor_arr);
  }

  return 0;
}
