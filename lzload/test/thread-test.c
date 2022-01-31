#include "lzload.h"

#include <stdio.h>

#include <libpsl.h>
#include <pthread.h>

#define NTHREADS 100

char *floor_arr[] = { "floor", NULL };

pthread_t threads[NTHREADS];
pthread_barrier_t barrier;

void do_thread(void *param) {
  pthread_barrier_wait(&barrier);
  double (*_floor)(double) = __loadsym(floor_arr);
  fprintf(stderr, "%.2f\n", _floor(2.7));
}

int main(int argc, char **argv) {
  if (pthread_barrier_init(&barrier, NULL, NTHREADS) != 0) {
    perror("pthread_barrier_init");
    return 1;
  }

  for (int i = 0; i < NTHREADS; i++) {
    if (pthread_create(&threads[i], NULL, do_thread, NULL) != 0) {
      perror("pthread_create");
      return 1;
    }
  } 

  for (int i = 0; i < NTHREADS; i++) {
    pthread_join(threads[i], NULL);
  }

  return 0;
}
