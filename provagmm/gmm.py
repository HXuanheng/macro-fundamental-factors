from numpy import hstack, zeros, ones, array, mat, tile, reshape, squeeze, eye, asmatrix
from numpy.linalg import inv
from pandas import read_csv, Series 
from scipy.linalg import kron
from scipy.optimize import fmin_bfgs
import numpy as np
import statsmodels.api as sm

iteration = 0
lastValue = 0
functionCount = 0

# A callable function is used to produce iteration-by-iteration output when using the non-linear optimizer.
def iter_print(params):
    global iteration, lastValue, functionCount
    iteration += 1
    print('Func value: {0:}, Iteration: {1:}, Function Count: {2:}'.format(lastValue, iteration, functionCount))

# The GMM objective which needs to be minimized (to get betas and lambdas)
def gmm_objective(params, pRets, fRets, Winv, out=False):
    global lastValue, functionCount
    T,N = pRets.shape
    T,K = fRets.shape
    beta = squeeze(array(params[:(N*K)]))
    lam = squeeze(array(params[(N*K):]))
    beta = reshape(beta,(N,K))
    lam = reshape(lam,(K,1))
    betalam = beta @ lam
    expectedRet = fRets @ beta.T
    e = pRets - expectedRet
    instr = tile(fRets,N)
    moments1  = kron(e,ones((1,K)))
    moments1 = moments1 * instr     # E[(R^{ex,i} - beta^i*FF)*FF]=0 (orthogon. conditions for the time series regression) 
    moments2 = pRets - betalam.T    # E[R^{ex,i} – beta^i*lambda] = 0 (pricing equations using the MPR)
    moments = hstack((moments1,moments2))

    avgMoment = moments.mean(axis=0)
    
    J = T * mat(avgMoment) * mat(Winv) * mat(avgMoment).T
    J = J[0,0]
    lastValue = J
    functionCount += 1
    if not out:
        return J
    else:
        return J, moments
    
# The GMM objective which needs to be minimized (to get factor loading b)
def gmm_objective_b(params, pRets, fRets, Winv, out=False):
    '''
    --------------------------------------------------------------------
    This function computes the objective function of the GMM given 
    parameter values and an estimate of the weighting matrix.
    --------------------------------------------------------------------
    INPUTS:
    params  =   an array of coefficients to be estimated (in this case the stochastic discount factor loadings b)
    pRets   =   a matrix of size (T,N) representing the T-periods historical returns of N assets
    fRets   =   a matrix of size (T,K) representing the T-periods historical returns of K factors
    Winv    =   weight matrix of size (N,N) used in the GMM estimation
    out     =   a boolean flag indicating whether the function should return both the objective 
                function value and the moments or just the objective function value
    --------------------------------------------------------------------
    '''
    global lastValue, functionCount
    # excess return of size (T,N), T period and N portfolios
    T,N = pRets.shape
    # factor return of size (T,K), T period and K factors
    T,K = fRets.shape
    # reshapes the params array into a column vector of size (K,1)
    b = squeeze(array(params)) 
    b = reshape(b,(K,1))
    # calculates the SDF (stochastic discount factor) as 1-FF*b for each period T, size (T,1)
    sdf = ones((T,1)) - fRets @ b
    # E[R^{ex,i}*(1-b*FF)] = 0 (SDF representation)
    # at each period t, the excess return of each portfolio n is multiplied by the sdf at the same period t
    moments = pRets * kron(sdf,ones((1,N)))    #pRets is (T,N) and kron(sdf,ones((1,N))) is (T,N)

    # for each portfolio, take the mean across time: take the mean of each column
    avgMoment = moments.mean(axis=0)
    
    J = T * mat(avgMoment) * mat(Winv) * mat(avgMoment).T   # it is T or 1/T 
    # convert the matrix J into a scalar
    J = J[0,0] 
    lastValue = J
    functionCount += 1
    if not out:
        return J
    else:
        return J, moments
    
# The `G` matrix, which is the derivative of the GMM moments with respect to the parameters, is defined.
def gmm_G(params, p_rets, f_rets):
    t,n = p_rets.shape
    t,k = f_rets.shape
    beta = squeeze(array(params[:(n*k)]))
    lam = squeeze(array(params[(n*k):]))
    beta = reshape(beta,(n,k))
    lam = reshape(lam,(k,1))
    G = np.zeros((n*k+k,n*k+n))
    ffp = (f_rets.T @ f_rets) / t
    G[:(n*k),:(n*k)] = kron(eye(n),ffp)
    G[:(n*k),(n*k):] = kron(eye(n),-lam)
    G[(n*k):,(n*k):] = -beta.T
    
    return G