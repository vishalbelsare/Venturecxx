#ifndef GKERNEL_H
#define GKERNEL_H

#include "types.h"

struct Scaffold;
struct ConcreteTrace;
struct Trace;

struct GKernel
{
  pair<Trace*,double> propose(ConcreteTrace * trace,
			      shared_ptr<Scaffold> scaffold);

  void accept();
  void reject();
  
};


#endif
