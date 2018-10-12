from collections import namedtuple
from itertools import product

import numpy as np
import pandas as pd
import pytest

from arch.multivariate.distribution import MultivariateNormal
from arch.multivariate.mean import ConstantMean, VARX
from arch.multivariate.volatility import ConstantCovariance, EWMACovariance
from arch.multivariate.utility import vech

dataset = namedtuple('dataset', ['y', 'x', 'lags', 'constant'])


def generate_data(nvar, nobs, nexog, common, lags, constant, pandas):
    rs = np.random.RandomState(1)
    y = rs.standard_normal((nobs, nvar))
    if nexog > 0:
        x = rs.standard_normal((nobs, nexog))
    else:
        x = None
    if pandas:
        index = pd.date_range('2000-1-1', periods=nobs)
        cols = ['y{0}'.format(i) for i in range(nvar)]
        y = pd.DataFrame(y, index=index, columns=cols)
        if nexog > 0:
            cols = ['x{0}'.format(i) for i in range(nexog)]
            x = pd.DataFrame(y, index=index, columns=cols)
    if not common:
        if pandas:
            x = {c: x for c in y}
        else:
            x = [x] * nvar
    return dataset(y=y, x=x, lags=lags, constant=constant)


NVAR = [1, 2, 10]
NOBS = [100, 500]
NEXOG = [0, 1, 3]
COMMON = [True, False]
LAGS = [1, [1], 3, [1, 3], None]
CONSTANT = [True, False]
PANDAS = [True, False]
params = list(product(NVAR, NOBS, NEXOG, COMMON, LAGS, CONSTANT, PANDAS))
ID = """nvar:{0}, nobs:{1}, nexog:{2}, common:{3}, lags:{4}, const:{5}, pd:{6}"""
ids = [ID.format(*map(str, p)) for p in params]


@pytest.fixture(scope='module', params=params, ids=ids)
def var_data(request):
    nvar, nobs, nexog, common, lags, constant, pandas = request.param
    return generate_data(nvar, nobs, nexog, common, lags, constant, pandas)


def test_constant():

    vol = ConstantCovariance()
    dist = MultivariateNormal(np.random.RandomState(1))
    cm = ConstantMean(None, vol, dist, nvar=3)
    mu = np.array([.1, .2, .3])
    cov = np.ones(3) + np.diag(np.ones(3))
    tcov = vech(cov)
    params = np.r_[mu, tcov]
    sim = cm.simulate(params, 1000)

    cm = ConstantMean(sim.data, vol, dist)
    cm.fit(cov_type='mle')


def test_ewma():
    vol = EWMACovariance()
    dist = MultivariateNormal(np.random.RandomState(1))
    cm = ConstantMean(None, vol, dist, nvar=3)
    mu = np.array([.1, .2, .3])
    params = mu
    cov = np.ones(3) + np.diag(np.ones(3))
    sim = cm.simulate(params, 1000, initial_cov=cov)

    cm = ConstantMean(sim.data, vol, dist)
    cm.fit(cov_type='mle')


def test_var_sim():
    varx = VARX(np.random.standard_normal((500, 2)), lags=2, constant=True, nvar=2,
                volatility=ConstantCovariance(), distribution=MultivariateNormal())
    params = np.array([.1, .1, .1, .1, 0, .2, .2, .2, .2, 0, 2, 1, 2])
    varx.simulate(params, 500)
