#include "lzload.h"

#include <stdio.h>

#include <libpsl.h>
#include <dlfcn.h>

char *pow_arr[] = { "pow", NULL };
char *floor_arr[] = { "floor", NULL };

int main(int argc, char **argv) {
  void *handle = dlopen("/home/aspire/lzload/test/libpsl.so.5", RTLD_NOW);
  if (handle == NULL) {
	  fprintf(stderr, "Failed to load libpsl.so.5\n");
	  return 1;
  }

  psl_ctx_t* (*psl_load_file)(const char *) = dlsym(handle, "psl_load_file");
  psl_load_file("test.txt");

  return 0;
}
