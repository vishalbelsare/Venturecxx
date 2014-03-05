from venture.test.config import get_ripl, default_num_transitions_per_sample
import itertools
from nose.plugins.attrib import attr
from nose.tools import assert_less, assert_greater
from nose import SkipTest
from venture.test.config import get_ripl, collectSamples, collect_iid_samples, defaultKernel

def mean(xs): return sum(xs) / float(len(xs))
    

def testCRPMix1a():
  """Baseline for testCRPMix1b"""
  ripl = get_ripl()

  ripl.assume('cluster_crp', "(lambda () 1)")
        
  ripl.assume('cv_shape', 4.0)
  ripl.assume('cv_scale', "(inv_gamma 1.0 1.0)")
        
  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.assume('get_cluster_variance', "(mem (lambda (cluster) (inv_gamma cv_shape cv_scale)))")
  ripl.assume('get_cluster', "(mem (lambda (point) (cluster_crp)))")
  ripl.assume('sample_cluster', "(lambda (cluster) (normal (get_cluster_mean cluster) (get_cluster_variance cluster)))")
  ripl.assume('get_point', "(mem (lambda (point) (sample_cluster (get_cluster point))))")

  ripl.predict("(get_cluster_mean (get_cluster 1))",label="cmean")
  ripl.observe("(get_point 1)","5")

  B = 100
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)

def testCRPMix1b():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.assume('sample_cluster', "(lambda (cluster) (normal (get_cluster_mean cluster) 1))")

  ripl.assume("mu","(get_cluster_mean 1)",label="cmean")
  
  ripl.observe("(normal mu 1)","5")

  B = 100
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)

def testCRPMix1b_2():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.predict("(get_cluster_mean 1)",label="cmean")
  
  ripl.observe("(normal (get_cluster_mean 1) 1)","5")

  B = 100
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)

def testCRPMix1b_3():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.predict("(get_cluster_mean false)",label="cmean")
  
  ripl.observe("(normal (get_cluster_mean false) 1)","5")

  B = 100
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)


def testCRPMix1c():
  """Makes sure basic clustering model behaves reasonably"""
  ripl = get_ripl()

  ripl.assume('cluster_crp', "(lambda () (if (flip) 1 1))")
          
  ripl.assume('cv_shape', 4.0)
  ripl.assume('cv_scale', "(inv_gamma 1.0 1.0)")
        
  ripl.assume('get_cluster_mean', "(mem (lambda (cluster) (uniform_continuous -10.0 10.0)))")
  ripl.assume('get_cluster_variance', "(mem (lambda (cluster) (inv_gamma cv_shape cv_scale)))")
  ripl.assume('get_cluster', "(mem (lambda (point) (cluster_crp)))")
  ripl.assume('sample_cluster', "(lambda (cluster) (normal (get_cluster_mean cluster) (get_cluster_variance cluster)))")
  ripl.assume('get_point', "(mem (lambda (point) (sample_cluster (get_cluster point))))")

  ripl.predict("(get_cluster_mean (get_cluster 1))",label="cmean")
  ripl.observe("(get_point 1)","5")

  B = 100
  T = 100

  mus = []

  for _ in range(T):
    ripl.infer(B)
    mus.append(ripl.report("cmean"))

  assert_less(mean(mus),5.5)
  assert_greater(mean(mus),4.5)
  
