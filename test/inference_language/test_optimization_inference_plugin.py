# Copyright (c) 2014-2017 MIT Probabilistic Computing Project.
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
from scipy.stats import norm
from scipy.optimize import minimize

from nose.tools import assert_almost_equal

from venture import shortcuts

# XXX Pretty hacky initial draft that was run with pytest mostly (not Venture's
# standard (Nose).

# TODO: get rid of this global variable mess.
TRUE_SCALE = 2
TRUE_MU = 3
N = 50
SEED = 0
np.random.seed(seed=SEED)
SAMPLES = np.random.normal(TRUE_MU, TRUE_SCALE, (N,))
PRINT_OPTIMIZATION = True

# TODO: remove this. Just facilitates printing if one tests with Venture's
# testing harness.
import sys
def help_print(str2print):
    print >> sys.stderr, str2print


def logpdf(parameters, sign=-1.):
    """Logpdf for simple normal - function to test scipy's optimize."""
    return sum(sign * norm.logpdf(SAMPLES, loc=parameters[0], scale=parameters[1]))

def der_logpdf(parameters, sign=-1.):
    """Partial derivative of logpdf for simple normal - function to test scipy's
    optimize."""
    partial_mu = sign * sum((SAMPLES - parameters[0])/parameters[1]**2)
    partial_std = sign * sum((parameters[0] - SAMPLES)**2 - parameters[1]**2)/parameters[1]**3
    return np.array([partial_mu, partial_std])

def get_normal_ripl(seed):
    ripl = shortcuts.make_lite_ripl(seed=seed)
    ripl.execute_program('''
        assume mu ~ uniform_continuous(0,10);
        assume std ~ uniform_continuous(0,10);
        assume obs_func = () -> {normal(mu, std)};
    ''')
    mu_0 = ripl.sample('mu')
    std_0 = ripl.sample('std')
    for sample in SAMPLES:
        ripl.observe('obs_func()', sample)
    return ripl, mu_0, std_0

def run_gradient_ascent(ripl):
    ripl.execute_program('''
         grad_ascent(default, all, 0.01, 1, 100)
    ''')
    mu_after_ascent = ripl.sample('mu')
    std_after_ascent = ripl.sample('std')
    return mu_after_ascent, std_after_ascent

def compare_to_grad_ascent(mu_after_optimization, std_after_optimization):
    """Compare the result of some other optimization method to gradient ascent.
    """
    ripl, mu_0, std_0  = get_normal_ripl(SEED)
    mu_after_ascent, std_after_ascent = run_gradient_ascent(ripl)
    decimals = 4
    assert_almost_equal(mu_after_optimization, mu_after_ascent, places=decimals)
    assert_almost_equal(std_after_optimization, std_after_ascent, places=decimals)

def test_did_I_get_derivative_right():
    """Simple test, to compare a grad ascent step taken with Venture with a
    manually computed one, to ascertain that I got the derivative right."""
    ripl, mu_0, std_0 = get_normal_ripl(SEED)
    ripl.execute_program('''
         grad_ascent(default, all, 0.1, 1, 1)
    ''')
    mu_1 = ripl.sample('mu')
    std_1 = ripl.sample('std')

    assert mu_0 != mu_1
    assert std_0 != std_1

    analytical_gradient = der_logpdf([mu_0, std_0], sign=1)
    assert_almost_equal(mu_1, mu_0 +  0.1 * analytical_gradient[0])
    assert_almost_equal(std_1, std_0 +  0.1 * analytical_gradient[1])

def test_scipy_optimize_raw():
    """Test whether I can find the same solution with scipy.optimize and
    venture's gradient ascent."""
    ripl, mu_0, std_0  = get_normal_ripl(SEED)
    mu_after_ascent, std_after_ascent = run_gradient_ascent(ripl)
    if PRINT_OPTIMIZATION:
        print "================"
        print "Venture"
        print [mu_after_ascent , std_after_ascent]
        print "================"
        print "Nelder-Mead"
        res_nelder_mead = minimize(
            logpdf,
            [mu_0, std_0],
            method='nelder-mead',
            options={'xtol': 1e-8, 'disp': True}
        )
        print res_nelder_mead.x
        print "================"
        print "BFGS"
        res_bfgs = minimize(
            logpdf,
            [mu_0, std_0],
            method='BFGS',
            jac=der_logpdf,
            options={'disp': True}
        )
        print res_bfgs.x
        print "================"
        print "Conjugate gradient"
        res_cg = minimize(
            logpdf,
            [mu_0, std_0],
            method='CG',
            jac=der_logpdf,
            options={'disp': True}
        )
        print res_cg
        print "================"
    decimals = 4
    assert_almost_equal(res_nelder_mead.x[0], mu_after_ascent, places=decimals)
    assert_almost_equal(res_nelder_mead.x[1], std_after_ascent, places=decimals)

    assert_almost_equal(res_bfgs.x[0], mu_after_ascent, places=decimals)
    assert_almost_equal(res_bfgs.x[1], std_after_ascent, places=decimals)

    assert_almost_equal(res_cg.x[0], mu_after_ascent, places=decimals)
    assert_almost_equal(res_cg.x[1], std_after_ascent, places=decimals)

def test_sanity_check_abstraction():
    """Sanity check the infrastructure for comparing other optimization to
    gradient ascent."""
    ripl, _, _  = get_normal_ripl(SEED)
    ripl.execute_program('''
         grad_ascent(default, all, 0.01, 1, 100)
    ''')
    mu_after_ascent = ripl.sample('mu')
    std_after_ascent = ripl.sample('std')
    compare_to_grad_ascent(mu_after_ascent, std_after_ascent)

def test_conjugate_gradient_by_comparison_to_grad_ascent():
    """Test venture's conjugate gradient optimization by comparison to gradient
    ascent."""
    ripl, _, _  = get_normal_ripl(SEED)
    ripl.execute_program('''
         conjugate_gradient_ascent(default, all)
    ''')
    mu_after_cg = ripl.sample('mu')
    std_after_cg = ripl.sample('std')
    compare_to_grad_ascent(mu_after_cg, std_after_cg)

def test_bfgs_by_comparison_to_grad_ascent():
    """Test venture's bfgs optimization by comparison to gradient ascent."""
    ripl, _, _  = get_normal_ripl(SEED)
    ripl.execute_program('''
         bfgs_optimize(default, all)
    ''')
    mu_after_bfgs = ripl.sample('mu')
    std_after_bfgs = ripl.sample('std')
    compare_to_grad_ascent(mu_after_bfgs, std_after_bfgs)

def test_lbfgs_by_comparison_to_grad_ascent():
    """Test venture's bfgs optimization by comparison to gradient ascent."""
    ripl, _, _  = get_normal_ripl(SEED)
    ripl.execute_program('''
         lbfgs_optimize(default, all)
    ''')
    mu_after_nelder = ripl.sample('mu')
    std_after_nelder = ripl.sample('std')
    compare_to_grad_ascent(mu_after_nelder, std_after_nelder)