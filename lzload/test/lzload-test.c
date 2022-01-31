#include "lzload.h"

#include <stdio.h>

char *pow_arr[] = { "pow", NULL };
char *floor_arr[] = { "floor", NULL };

int main(int argc, char **argv) {
double (*_pow)(double, double) = __loadsym(pow_arr);
  if (_pow == NULL) return 1;

  double x = _pow(2.0,8.0);
  printf("pow(2.0,8.0):%.2f\n", x);

  double (*_floor)(double) = __loadsym(floor_arr);
  if (_floor == NULL) return 1;

  double y = _floor(2.7);
  printf("floor(2.7):%.2f\n", y);

  return 0;
}
