'''Weight-balanced trees.

This program is based on

  Stephen Adams, Implementing Sets Efficiently in a Functional
     Language, CSTR 92-10, Department of Electronics and Computer
     Science, University of Southampton, 1992.

but only implements the operations that are useful for Venture Lite.
The actual implementation is cribbed close to verbatim from wt-trees
in MIT Scheme, which were written by Stephen Adams and modified by
Chris Hansen and Taylor Campbell.'''

# TODO I imagine much memory can be saved by representing the
# node structure with just a tuple and None, manely
# data Tree k v = Maybe (k,v,Node k v,Node k v,Int)
# instead of the below classes
# data Tree k v = Either EmptyNode (Node k v)

# Style note: all node keys and subtress are always listed in function
# arguments in-order.

class EmptyNode(object): #pylint: disable=W0232
  def size(self): return 0
  def isEmpty(self): return True

class Node(object):
  def __init__(self, left, key, value, right):
    self.left = left
    self.key = key
    self.value = value
    self.right = right
    self.ct = left.size() + right.size() + 1

  def size(self): return self.ct
  def isEmpty(self): return False

# TODO Manually inline this?
def node_weight(node):
  return node.size() + 1

def single_left(x, akey, avalue, r):
  return Node(Node(x, akey, avalue, r.left), r.key, r.value, r.right)

def single_right(l, bkey, bvalue, z):
  return Node(l.left, l.key, l.value, Node(l.right, bkey, bvalue, z))

def double_left(x, akey, avalue, r):
  return Node(Node(x, akey, avalue, r.left.left),
              r.left.key, r.left.value,
              Node(r.left.right, r.key, r.value, r.right))

def double_right(l, ckey, cvalue, z):
  return Node(Node(l.left, l.key, l.value, l.right.left),
              l.right.key, l.right.value,
              Node(l.right.right, ckey, cvalue, z))

# For the provenance of these constants, see Yoichi Hirai and Kazuhiko
# Yamamoto, `Balancing Weight-Balanced Trees', Journal of Functional
# Programming 21(3), 2011.
_DELTA = 3
_GAMMA = 2

def t_join(l, key, value, r):
  l_w = node_weight(l)
  r_w = node_weight(r)
  if r_w > _DELTA * l_w:
    # Right is too big
    if node_weight(r.left) < _GAMMA * node_weight(r.right):
      return single_left(l, key, value, r)
    else:
      return double_left(l, key, value, r)
  elif l_w > _DELTA * r_w:
    # Left is too big
    if node_weight(l.right) < _GAMMA * node_weight(l.left):
      return single_right(l, key, value, r)
    else:
      return double_right(l, key, value, r)
  else:
    return Node(l, key, value, r)

def node_popmin(node):
  if node.isEmpty():
    raise Exception("Trying to pop the minimum off an empty node")
  elif node.left.isEmpty():
    return (node.key, node.value, node.right)
  else:
    # TODO Is this constant creation and desctruction of tuples
    # actually any more efficient than just finding the minimum in one
    # pass and removing it in another?
    (mink, minv, newl) = node_popmin(node.left)
    return (mink, minv, t_join(newl, node.key, node.value, node.right))

def node_lookup(node, key):
  if node.isEmpty():
    return None
  elif key < node.key:
    return node_lookup(node.left, key)
  elif node.key < key:
    return node_lookup(node.right, key)
  else:
    return node.value

def node_insert(node, key, value):
  if node.isEmpty():
    return Node(EmptyNode(), key, value, EmptyNode())
  elif key < node.key:
    return t_join(node_insert(node.left, key, value),
                  node.key, node.value, node.right)
  elif node.key < key:
    return t_join(node.left, node.key, node.value,
                  node_insert(node.right, key, value))
  else:
    return Node(node.left, key, value, node.right)

def node_adjust(node, key, f):
  if node.isEmpty():
    # TODO Optimize the not-found case by not reconstructing the tree
    # on the way up?
    return node
  elif key < node.key:
    return Node(node_adjust(node.left, key, f),
                node.key, node.value, node.right)
  elif node.key < key:
    return Node(node.left, node.key, node.value,
                node_adjust(node.right, key, f))
  else:
    return Node(node.left, key, f(node.value), node.right)

def node_delete(node, key):
  if node.isEmpty():
    return node
  elif key < node.key:
    return t_join(node_delete(node.left, key),
                  node.key, node.value, node.right)
  elif node.key < key:
    return t_join(node.left, node.key, node.value,
                  node_delete(node.right, key))
  else:
    # Deleting the key at this node
    if node.right.isEmpty():
      return node.left
    elif node.left.isEmpty():
      return node.right
    else:
      [min_r_k, min_r_v, new_r] = node_popmin(node.right)
      return t_join(node.left, min_r_k, min_r_v, new_r)

class Map(object):
  """Persistent map backed by a weight-balanced tree.

  The lookup method returns None if the key is not found.  Do not
  insert None as a value or you will get confused."""
  def __init__(self, root=None):
    self.root = root if root is not None else EmptyNode()
  def lookup(self, key):
    return node_lookup(self.root, key)
  def contains(self, key):
    return node_lookup(self.root, key) is not None
  def insert(self, key, value):
    return Map(node_insert(self.root, key, value))
  def adjust(self, key, f):
    """adjust :: (Map k v) -> k -> (v -> v) -> Map k v

    Returns a new Map obtained from this one by applying the given
    function to the value at the given key.  Returns the original Map
    unchanged if the key is not present.  The name is chosen by
    analogy to Data.Map.adjust from the Haskell standard library."""
    return Map(node_adjust(self.root, key, f))
  def delete(self, key):
    return Map(node_delete(self.root, key))

# Testing TODO:
# - Correctness, per Daniel's rbtree tests
# - Balance, either as asymptotics with the timings framework or
#   through an explicit check.
