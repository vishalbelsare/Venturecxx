# Copyright (c) 2016 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
import math

from venture.lite.orderedset import OrderedFrozenSet
from venture.lite.scaffold import constructScaffold, Scaffold
from venture.lite.smap import SamplableMap

# The language of possible subproblem selection phrases.  The item in
# each field is expected to be one of these, except Lookup.key,
# Edge.edge, and FetchTag.name are expected to be objects.

Intersect = namedtuple("Intersect", ["source1", "source2"])
Lookup = namedtuple("Lookup", ["key", "dictionary"])
Random1 = namedtuple("Random1", ["source"])
Edge = namedtuple("Edge", ["source", "edge"])
Extent = namedtuple("Extent", ["source"])
UnionDict = namedtuple("UnionDict", ["source"])
Union = namedtuple("Union", ["sources"])
FetchTag = namedtuple("FetchTag", ["name"])
Top = namedtuple("Top", [])
MinimalSubproblem = namedtuple("MinimalSubproblem", ["source"])

# TODO Not supporting ordered scaffolds (as for pgibbs) yet, though I
# guess we could, by adding an "ordered list of sets of nodes" object
# and an appropriate AST node to make one of those from a dictionary.
# But maybe pgibbs should just be written as a (horrible) inference
# program.

# TODO This is called an "Indexer" because we never renamed
# "BlockScaffoldIndexer" to anything more sensible.  The theory in the
# original nomenclature was that mixmh was "indexed" by some computed
# auxiliary variable.
class TraceSearchIndexer(object):
  def __init__(self, prog):
    # TODO Not supporting subsampling yet, because that's too old and
    # confusing, and this is too new.
    # TODO Also not supporting delta kernels, for a similar reason.
    self.prog = prog

  def sampleIndex(self, trace):
    (scaffold, _weight) = interpret(self.prog, trace)
    assert isinstance(scaffold, Scaffold)
    return scaffold


# The return value of interpret is expected to be one of
# - A single node
# - An OrderedSet or OrderedFrozenSet of nodes
# - A SamplableMap from keys to nodes
# - A Scaffold
# - The Top() object (serving as a special token denoting the top of the trace)
def interpret(prog, trace):
  # if isinstance(prog, Intersect):
  #   return intersect(
  #     interpret(prog.source1, trace),
  #     interpret(prog.source2, trace))
  if isinstance(prog, Lookup):
    (d, w) = interpret(prog.dictionary, trace)
    return (d[prog.key], w)
  elif isinstance(prog, Random1):
    (thing, wt) = interpret(prog.source, trace)
    ans = sample_one(thing, trace.py_rng)
    wt2 = -1 * math.log(len(thing))
    return (ans, wt + wt2)
  # elif isinstance(prog, Edge): # TODO
  elif isinstance(prog, Extent):
    (thing, wt) = interpret(prog.source, trace)
    return (extent(thing, trace), wt)
  # elif isinstance(prog, UnionDict):
  # elif isinstance(prog, Union):
  elif isinstance(prog, FetchTag):
    return (trace.scopes[prog.name], 0) # TODO What to do with the default scope, if we still have that idea?
  elif isinstance(prog, Top):
    return (Top, 0) # Hack: Top as a node set is also a special token, reusing the same token
  elif isinstance(prog, MinimalSubproblem):
    (nodes, wt) = interpret(prog.source, trace)
    return (constructScaffold(trace, [nodes]), wt)
  else:
    raise Exception("Unknown trace search term %s" % (prog,))

# def intersect(thing1, thing2):
#   ...

def sample_one(thing, prng):
  if isinstance(thing, SamplableMap):
    return thing.sample(prng)[1]
  elif isinstance(thing, OrderedFrozenSet):
    return prng.sample(list(thing),1)[0]
  else:
    raise Exception("Can only sample one element of a collection, not %s" % (thing,))

def extent(thing, trace):
  if isinstance(thing, Top):
    return trace.scopes["default"] # TODO ???
  return set_fmap(thing, lambda nodes: trace.randomChoicesInExtent(nodes, None, None))

def set_fmap(thing, f):
  "Lift an f :: set -> a to accept sets, single nodes (by upgrading), or dictionaries (pointwise)."
  if isinstance(thing, SamplableMap):
    ans = SamplableMap()
    for k, v in thing.iteritems():
      ans[k] = f(v)
    return ans
  elif isinstance(thing, OrderedFrozenSet):
    return f(thing)
  else:
    return f(OrderedFrozenSet([thing]))