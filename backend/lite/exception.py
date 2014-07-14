class VentureError(Exception):
  """A runtime error with a stack trace."""
  stack_frame = None

  def __str__(self):
    return '\n'.join(['Stack Trace:', str(self.stack_frame), '*** ' + self.message])

class VentureTypeError(VentureError):
  """This exception means that some SP was passed arguments of the wrong type."""

class VentureValueError(VentureError):
  """This exception means that some SP was passed an inappropriate value
of correct type (by analogy to ValueError in Python)."""

class VentureBuiltinSPMethodError(VentureError):
  """This exception means that an unimplemented method was called on a built-in PSP."""

class VentureWarning(UserWarning):
  '''Base class for Venture warnings'''
  pass

class GradientWarning(VentureWarning):
  '''Warnings related to gradients for automatic differentiation'''
  pass

class StackFrame(object):
  """Contains the part of a stack trace generated by a request or top level evaluation."""
  def __init__(self, exp, index, child=None):
    self.exp = exp
    self.index = index
    self.child = child

  def __str__(self):
    s = unparse(self.exp)
    s += '\n'
    s += underline(self.exp, self.index)
    if self.child is not None:
      s += '\n' + str(self.child)
    return s

def unparse(exp):
  """Unparses a Venture expression."""
  if isinstance(exp, list):
    return '(%s)' % ' '.join(map(unparse, exp))
  return str(exp)

def annotate(exp, index):
  """Gives text ranges for a subexpression."""
  if len(index) > 0:
    begin, length = annotate(exp[index[-1]], index[:-1])
    begin += 1 + len(' '.join(map(unparse, exp[:index[-1]])))
    return begin, length
  else:
    return 0, len(unparse(exp))

def underline(exp, index):
  """Underlines the subexpression."""
  begin, length = annotate(exp, index)
  return ''.join([' '] * begin + ['^'] * length)
