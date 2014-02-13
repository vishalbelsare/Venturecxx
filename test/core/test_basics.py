from venture.test.config import get_ripl
from venture.ripl import Ripl

def testRIPL():
  assert isinstance(get_ripl(), Ripl)

def testConstant():
  assert 1 == get_ripl().predict(1)

def testLambda():
  assert 2 == get_ripl().predict("((lambda (x) x) 2)")

def testTriviality():
  assert 4 == get_ripl().predict("(+ 2 2)")
