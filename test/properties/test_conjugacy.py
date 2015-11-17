# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

import numpy as np

from venture.test.config import default_num_samples
from venture.test.config import default_num_transitions_per_sample
from venture.test.config import get_ripl, collectIidSamples
from venture.test.stats import reportSameContinuous
from venture.test.stats import statisticalTest
import venture.value.dicts as v

def extract_sample(maker, params, index):
  r = get_ripl()
  r.assume("maker", maker)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    ans = r.sample(expr)[-1]
    r.forget("made")
    return ans
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

def extract_cross_sample(maker, params, index1, index2, combiner):
  r = get_ripl()
  r.assume("maker", maker)
  index = max(index1, index2)
  expr = v.app(v.sym("list"), *[v.app(v.sym("made")) for _ in range(index+1)])
  def one_sample():
    r.assume("made", v.app(v.sym("maker"), *params))
    vec = r.sample(expr)
    r.forget("made")
    return combiner(vec[index1], vec[index2])
  results = [one_sample() for _ in range(default_num_samples(5))]
  return results

@statisticalTest
def checkSameMarginal(name, maker2, params, index):
  package = simulation_agreement_packages[name]
  native = package['native']
  report = package['reporter']
  return report(extract_sample(native, params, index),
                extract_sample(maker2, params, index))

@statisticalTest
def checkSameCross(name, maker2, params, index1, index2):
  package = simulation_agreement_packages[name]
  native = package['native']
  report = package['reporter']
  combiner = package['combiner']
  one = extract_cross_sample(native, params, index1, index2, combiner)
  other = extract_cross_sample(maker2, params, index1, index2, combiner)
  return report(one, other)

native_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (lambda () (normal mean stddev))))"""

suff_stat_nig_normal = """(lambda (m V a b)
  (let ((variance (inv_gamma a b))
        (mean (normal m (sqrt (* V variance))))
        (stddev (sqrt variance)))
    (make_suff_stat_normal mean stddev)))"""

simulation_agreement_packages = {
  'nig_normal' : {
    'native' : native_nig_normal,
    'optimized' : ['make_nig_normal', 'make_uc_nig_normal',
                   suff_stat_nig_normal],
    'param_sets': [(1.0, 1.0, 1.0, 1.0),
                   (2.0, 3.0, 4.0, 5.0)],
    'reporter' : reportSameContinuous,
    'combiner' : lambda x, y: x*y
  }
}

def testNigNormalSimulationAgreement():
  name = 'nig_normal'
  package = simulation_agreement_packages[name]
  for maker in package['optimized']:
    for params in package['param_sets']:
      for index in [0, 10]:
        yield checkSameMarginal, name, maker, params, index
      for index1, index2 in [(1,2), (3,7)]:
        yield checkSameCross, name, maker, params, index1, index2

native_fixed_normal = """(lambda (mu sigma)
  (lambda () (normal mu sigma)))"""

def extract_assessment(maker, params, data):
  r = get_ripl()
  r.assume("maker", maker)
  r.assume("made",
           v.app(v.sym("maker"),
                 *[v.app(v.sym("exactly"), p) for p in params]))
  for item in data:
    r.observe("(made)", item)
  ans = r.infer("global_likelihood")
  return ans

def checkSameAssessment(maker, params, data):
  assert np.allclose(extract_assessment(native_fixed_normal, params, data),
                     extract_assessment(maker, params, data))

def testSameAssessment():
  frob = \
  [-1.81, -1.62, -1.53, -1.35, -1.02, -0.85, -0.69, -0.65, -0.55, -0.48,
   -0.39, -0.28, -0.20, -0.18, -0.16, -0.03, 0.02, 0.06, 0.07, 0.19,
   0.22, 0.27, 0.31, 0.39, 0.46, 0.50, 0.52, 0.56, 0.57, 0.60,
   0.60, 0.61, 0.63, 0.70, 0.70, 0.74, 0.76, 0.78, 0.80, 0.85,
   0.90, 0.92, 0.94, 0.96, 1.00, 1.06, 1.12, 1.17, 1.21, 1.23,
   1.25, 1.27, 1.28, 1.31, 1.35, 1.37, 1.40, 1.43, 1.47, 1.48,
   1.49, 1.53, 1.53, 1.55, 1.62, 1.67, 1.74, 1.76, 1.78, 1.80,
   1.83, 1.87, 1.89, 1.92, 2.03, 2.07, 2.10, 2.12, 2.14, 2.19,
   2.25, 2.27, 2.29, 2.43, 2.52, 2.57, 2.59, 2.65, 2.70, 2.71,
   2.75, 2.80, 2.84, 3.03, 3.20, 3.37, 3.50, 3.58, 3.76, 4.16, 4.34]
  for params in [(0.0, 1.0),
                 (2.0, 3.0),
                 (-2.0, 30.0),
                 (5.0, 0.1),
               ]:
    for dataset in [[0.0],
                    map(float, range(10)),
                    frob]:
      checkSameAssessment('make_suff_stat_normal', params, dataset)

@statisticalTest
def testUCKernel():
  r = get_ripl()
  r.assume("made", "(tag 'latent 0 (make_uc_nig_normal 1 1 1 1))")
  for i in range(5):
    r.predict("(tag 'data %d (made))" % i, label="datum_%d" % i)
  def samples(infer):
    return collectIidSamples(r, address="datum_0",
                             num_samples=default_num_samples(),
                             infer=infer)
  prior = samples("pass")
  geweke = """(repeat %d (do (mh 'latent one 1)
    (mh 'data all 1)))""" % default_num_transitions_per_sample()
  geweke_result = samples(geweke)
  return reportSameContinuous(prior, geweke_result)