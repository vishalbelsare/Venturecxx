#ifndef VALUE_H
#define VALUE_H

#include "types.h"
#include "srs.h"
#include <vector>
#include "Eigen/Dense"

#include <boost/python/object.hpp>
#include <boost/python/dict.hpp>
#include <boost/unordered_map.hpp>

using Eigen::MatrixXd;
using Eigen::VectorXd;

using std::vector;
using std::pair;

struct HashVentureValuePtr;
struct VentureValuePtrsEqual;

template <typename T>
struct VentureValuePtrMap : boost::unordered_map<VentureValuePtr, T, HashVentureValuePtr, VentureValuePtrsEqual> {};

// TODO AXCH
// We need to be more consistent about whether this unboxes
struct VentureValue
{
  virtual double getDouble() const;
  virtual int getInt() const;
  virtual int getAtom() const;
  virtual bool getBool() const;
  virtual const string & getSymbol() const;
  virtual const vector<VentureValuePtr>& getArray() const;
  virtual bool isNil() const { return false; }
  
  virtual const VentureValuePtr& getCar() const;
  virtual const VentureValuePtr& getCdr() const;
  
  virtual const Simplex& getSimplex() const;
  virtual const VentureValuePtrMap<VentureValuePtr>& getDictionary() const;
  virtual const MatrixXd& getMatrix() const;
  
  virtual const vector<ESR>& getESRs() const;
  virtual const vector<shared_ptr<LSR> >& getLSRs() const;

  virtual Node * getNode() const;

  /* for containers */
  virtual VentureValuePtr lookup(VentureValuePtr index) const;
  virtual bool contains(VentureValuePtr index) const;
  virtual int size() const;
  
  virtual boost::python::dict toPython() const 
    { 
      cout << "toPython() -- " << toString() << endl;
      assert(false); throw "need to override toPython()"; 
    };

  /* for unordered_maps */
  virtual bool equals(const VentureValuePtr & other) const;
  virtual size_t hash() const;
  
  virtual string toString() const { return "Unknown VentureValue"; };
};

/* for unordered map */
struct VentureValuePtrsEqual
{
  bool operator() (const VentureValuePtr& a, const VentureValuePtr& b) const
  {
    return a->equals(b);
  }
};

struct HashVentureValuePtr
{
  size_t operator() (const VentureValuePtr& a) const
  {
    return a->hash();
  }
};

#endif
