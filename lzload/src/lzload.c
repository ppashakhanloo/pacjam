#include "lzload.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dlfcn.h>
#include <sys/types.h> 

#include <pthread.h>

#define DEBUG

/* ============================================================================= */
typedef struct {
  char *libname;
  void *handle;
  char *package;
} lzlib;

lzlib *libtable;
unsigned long numlibs;
unsigned long libtable_size;

typedef struct {
  char *sym;
  char *lib;
} lzsym;

lzsym* symtable;
unsigned long numsyms;
unsigned long symtable_size;

pid_t pid;
char tracename[256];

pthread_mutex_t loader_lock = PTHREAD_MUTEX_INITIALIZER; 

/* ============================================================================= */
unsigned long hash(char *str) {
  unsigned long hash = 5381;
  int c;
  while ((c = *str++))
    hash = ((hash << 5) + hash) + c; /* hash * 33 + c */
  return hash;
}

lzlib* lookup_lib(char *l) {
  unsigned long i = hash(l) % libtable_size;
  unsigned long j = i;
  do {
    if (libtable[j].libname == NULL) {
      break;
    }
    if (strcmp(l, libtable[j].libname) == 0) {
      return &libtable[j];
    }
    j = (j + 1) % libtable_size;
  } while (j != i);
  return NULL;
} 

lzlib* insert_lib(char *l) {
  unsigned long i = hash(l) % libtable_size;
  unsigned long j = i;
  do {
    if (libtable[j].libname == NULL) {
      libtable[j].libname = malloc(strlen(l) + 1);     
      strcpy(libtable[j].libname,l);
      return &libtable[j];
    }
    j = (j + 1) % libtable_size;
  } while (j != i);
  return NULL;
}

lzsym* lookup_sym(char *s) {
  unsigned long i = hash(s) % symtable_size;
  unsigned long j = i;
  do {
    if (symtable[j].sym == NULL) {
      break;
    }
    if (strcmp(s, symtable[j].sym) == 0) {
      return &symtable[j];
    }
    j = (j + 1) % symtable_size;
  } while (j != i);
  return NULL;
} 

lzsym* insert_sym(char *s, char *l) {
  unsigned long i = hash(s) % symtable_size;
  unsigned long j = i;
  do {
    if (symtable[j].sym == NULL) {
      symtable[j].sym = malloc(strlen(s) + 1);     
      symtable[j].lib = malloc(strlen(l) + 1);     
      strcpy(symtable[j].sym,s);
      strcpy(symtable[j].lib,l);
      return &symtable[j];
    }
    j = (j + 1) % symtable_size;
  } while (j != i);
  return NULL;
}

char* findlib(char *libname) {
  char *ldpath = getenv(LZ_LIBRARY_PATH);
  if (ldpath == NULL)
    return NULL;

  char *ldpath2 = malloc(strlen(ldpath) + 1);
  strcpy(ldpath2, ldpath);
  char *p = strtok(ldpath2, ":");
  char buf[256];
  do {
    sprintf(buf, "%s/%s", p, libname);
    if (access(buf, F_OK) == 0) {
      char *l = malloc(strlen(buf) + 1);
      strcpy(l, buf);
      free(ldpath2);
      return l;
    }
  } while ((p = strtok(NULL, ":")) != NULL);

  free(ldpath2);
  return NULL;
}

int init() __attribute__((constructor));
int destroy() __attribute__((destructor));

int init() {
  char *lenv = getenv(LZLOAD_LIB);
  if (lenv == NULL)
    return -1;

  char *libs = malloc(strlen(lenv)+1);
  strcpy(libs,lenv); 

  pid = getpid();
  char *p = libs;
#ifdef DEBUG
  fprintf(stderr, "Initializing lzload (%ld)\n", pid);
#endif

  // No libs
  if (*p == 0) 
    return -1;

  numlibs = 1;
  while (*p != 0) {
    if (*p == ':') numlibs++;
    ++p;
  }

#ifdef DEBUG
  fprintf(stderr, "Caching %ld libraries\n", numlibs);
#endif

  libtable_size = numlibs * 2;
  libtable = malloc(sizeof(lzlib) * libtable_size);
  bzero(libtable, sizeof(lzlib) * libtable_size);



  char *l = strtok(libs, ":");
  do {
    insert_lib(l);
  } while ((l = strtok(NULL, ":")) != NULL);

  char *h = getenv("HOME");
  char buf[256];
  sprintf(buf, "%s/%s/symbol-out/symbols.txt", h, LZLOAD_REPO);
  FILE *f = fopen(buf, "r");
  if (f == NULL) {
    fprintf(stderr, "Failed to load symbol file %s\n", buf);
  }
  fscanf(f, "%ld", &numsyms);
#ifdef DEBUG
  fprintf(stderr, "Loading %ld symbols\n", numsyms);
#endif

  symtable_size = numsyms * 2;

  symtable = malloc(sizeof(lzsym) * symtable_size);
  bzero(symtable, sizeof(lzsym) * symtable_size);

  char sbuf[65536], lbuf[65536];
  while (fscanf(f, "%s %s", sbuf, lbuf) != EOF) {
    insert_sym(sbuf, lbuf);
  } 
  fclose(f);

  // Populate some lib meta info
  sprintf(buf, "%s/%s/symbol-out/packages.txt", h, LZLOAD_REPO);
  f = fopen(buf, "r");
  if (f == NULL) {
    fprintf(stderr, "Failed to load packages file %s\n", buf);
    free(libs);
    return 1;
  }
  while (fscanf(f, "%s %s", sbuf, lbuf) != EOF) {
    lzlib *l = lookup_lib(sbuf);
    if (!l) 
      continue;
    l->package = malloc(strlen(lbuf)+1);
    strcpy(l->package,lbuf);
  } 
  fclose(f);

  free(libs);

  char* def_name = getenv(LZLOAD_TRACE);
  if (!def_name) {
    def_name = "lzload.trace";
  }
  sprintf(tracename, "%s.%ld", def_name, pid); 

  return 0;
} 

int destroy() {
  // cleanup
  for (unsigned long i = 0; i < libtable_size; i++) {
    if (libtable[i].libname != NULL) {
      free(libtable[i].libname);
    }
    if (libtable[i].package != NULL) {
      free(libtable[i].package);
    }
  }

  for (unsigned long i = 0; i < symtable_size; i++) {
    if (symtable[i].sym != NULL) {
      free(symtable[i].sym);
      free(symtable[i].lib);
    }
  }
	
  free(libtable);
  free(symtable);

  return 0;
}

int loadlib(lzlib *l) {
  char *p = findlib(l->libname);
  if (p == NULL) {
    fprintf(stderr, "Error: could not find %s on LD_LIBRARY_PATH!\n", l->libname);
    free(p);
    return 0;
  }
  //if (pthread_mutex_lock(&loader_lock) != 0) {
   // fprintf(stderr, "Error: failed to lock loader\n");
    //free(p);	
  //}

  if (l->handle == NULL) {
    l->handle = dlopen(p, RTLD_LAZY | RTLD_DEEPBIND);
#ifdef DEBUG
    fprintf(stderr, "Loading %s from pid %d\n", l->libname, pid);
#endif
    FILE *trace_log = fopen(tracename, "a");
    if (!trace_log) {
      fprintf(stderr, "error: could not open tracefile: %s for writing\n", tracename);
      return 1;
    }
    fprintf(trace_log, "%s ", l->package);
    fflush(trace_log);
    fclose(trace_log);
  }
  if (l->handle == NULL)
    fprintf(stderr, "Error: failed to load %s\n", l->libname);

  //if (pthread_mutex_unlock(&loader_lock) != 0) 
   // fprintf(stderr, "Error: failed to unlock loader\n");

  free(p);	
  return (l->handle != NULL);
}

char* __get_lib_name(char *symbol) {
  lzsym *s = lookup_sym(symbol);
  if (s == NULL)
    return NULL;
  return s->lib;
}

void* __loadsym(char **symbols) {
  int i = 0;	
  char *symbol = NULL;
  char *libname = NULL;
  while (symbols[i] != NULL) {
#ifdef DEBUG
  //  fprintf(stderr,"__get_lib_name %s\n", symbols[i]);
#endif
    if ((libname = __get_lib_name(symbols[i])) != NULL) {
      symbol = symbols[i];
      break;
    }
    i++;
  }
  if (symbol == NULL) {
   // fprintf(stderr, "Error: could not find library for symbols\n");
    return NULL;
  }
#ifdef DEBUG
  //fprintf(stderr, "__loadsym %s:%s\n", libname, symbol);
#endif 
  lzlib *l = lookup_lib(libname);
  if (l == NULL) {
    fprintf(stderr, "Error: could not locate %s in library table\n", libname);
    return NULL;
  }
  if (l->handle == NULL && !loadlib(l)) {
    return NULL;
  }
  void *s = dlsym(l->handle, symbol);
  if (s == NULL) 
    fprintf(stderr, "Error: could not find symbol %s in %s\n", symbol, l->libname);
  return s;
} 
