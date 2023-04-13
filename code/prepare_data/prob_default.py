import pandas as pd
import numpy as np
import datetime as dt
from scipy.stats import norm
from pandas.tseries.offsets import *
from scipy import optimize
from tqdm import tqdm
import math


tqdm.pandas()

# File position
resource = "data/pulled/"
results = "data/generated/"

"""
Script to calculate distance-to-default
"""
def calcVolatility(x): 
    return np.std(np.log(np.divide(x[1:],x[:-1])))*np.sqrt(252)

def BlackScholesCallValue(S,X,r,sigma,T):
    d1=(np.log(S/X)+(r+0.5*sigma**2)*T)/(sigma*np.sqrt(T));
    d2=d1-sigma*np.sqrt(T);
    delta=norm.cdf(d1)
    CP=S*delta-X*np.exp(-r*T)*norm.cdf(d2);
    return [CP, delta]    

# def diff_BlackScholesCallValue(S,C,X,r,sigma,T):
#     [C_0,D0]=BlackScholesCallValue(S,X,r,sigma,T)
#     return C - C_0

# def BlackScholesZero(C,X,r,sigma,T):
#     # solves Black Scholes Call option formula by using optimize.root
#     sol = optimize.root(diff_BlackScholesCallValue, x0=C+X, args=(C,X,r,sigma,T))
#     Va=sol.x[0]
#     return Va
    
def BlackScholesZero(C,X,r,sigma,T):
    # solves Black Scholes Call option formula for S using Newton's method
    if X==0:
        return C
    UpperS=C+X*np.exp(-r*T);
    if sigma==0 or X==0:
        return UpperS
    LowerS=C
    tol=0.0001*C
    delta=C; itercount=0; x0=LowerS; x1=UpperS
    while abs(delta)>tol and itercount<=100:
        itercount=itercount+1
        [bs0,D0]=BlackScholesCallValue(x0,X,r,sigma,T)
        y0=bs0-C
        [bs1,D1]=BlackScholesCallValue(x1,X,r,sigma,T)
        y1=bs1-C
        if D0<0.01:
            xguess=(x0*y1-x1*y0)/(y1-y0);
        else:
            xguess = x0 - y0/D0;
        if xguess>UpperS:
            xguess=UpperS
        elif xguess<LowerS:
            xguess=LowerS
        [bsxg,Dxg]=BlackScholesCallValue(xguess,X,r,sigma,T)
        delta=bsxg-C
        x0=xguess
    if abs(delta)>tol:
        return np.nan
    else:
        return xguess
    
def dailyDLIcalcs(Ve,X,r,sigma_a,T):
    Va=[]
    for v in Ve:
        Va.append(BlackScholesZero(v,X,r,sigma_a,T))
    Va=np.array(Va)
    return [Va, calcVolatility(Va)]

def calc_DD(rf, X, Ve, T):
    sigma_a=calcVolatility(Ve)
    sigma_previous=sigma_a
    delta=1.0
    itercount=0
    while not np.isnan(delta) and delta>0.0001 and itercount<100:
        itercount=itercount+1
        [Va, sigma_a]=dailyDLIcalcs(Ve,X,rf,sigma_a,T)
        delta=abs(sigma_a-sigma_previous)
        sigma_previous=sigma_a
    # compute drift term
    mu=np.mean(np.log(np.divide(Va[1:],Va[:-1])))
    if X==0: # no probability of default
        DD=100
    elif sigma_a==0: # if stock is not traded
        DD=np.nan
    else:
        DD=(np.log(Va[-1]/X)+(mu-(0.5*sigma_a**2))*T) / (sigma_a*np.sqrt(T))
    p_def = norm.cdf(-DD)
    return [Va[-1], sigma_a, p_def, DD]

def row_dd(x,market,T):
    # market data from last 12 months
    end_date = x['date']
    start_date = end_date + MonthEnd(-12)
    result = market[(market['permno'] == x['permno']) & (market['date'] > start_date) & (market['date'] <= end_date)].loc[:, ['date','me']]
    r = x['DGS1']
    Ve = result['me'].values
    # print(start_date,end_date,x['permno'],len(Ve))
    if len(Ve) >= 240:
        X = x['debt']
        [Va, sigma_a, p_def, DD]=calc_DD(r, X, Ve, T)
    else: 
        Va, sigma_a, p_def, DD = np.nan, np.nan, np.nan, np.nan
    return Va, sigma_a, p_def, DD

def preparing_comp():
    # read compustat pulled data
    comp = pd.read_csv(resource + "wrds_comp.csv", parse_dates=['datadate'])
    # fill the nan in current and long debt data
    comp['dlc']=comp['dlc'].fillna(0)
    comp['dltt']=comp['dltt'].fillna(0)
    # select the columns
    comp=comp[['gvkey','datadate','dlc', 'dltt']] 
    return comp

def preparing_crsp(year):
    # read crsp pulled data
    year_bf = str(year-1)
    year_str = str(year)
    # Read the first CSV file
    crsp1 = pd.read_csv(resource + f"wrds_crsp_d_{year_bf[2:]}.csv", parse_dates=['date'])
    # Read the second CSV file
    crsp2 = pd.read_csv(resource + f"wrds_crsp_d_{year_str[2:]}.csv", parse_dates=['date'])
    # Concatenate the DataFrames
    crsp_d = pd.concat([crsp1, crsp2])
    # crsp_d = pd.read_csv(resource + f"wrds_crsp_d_{year_bf[2:]}{year_str[2:]}.csv", parse_dates=['date'])
    # change variable format to int
    crsp_d[['permco','permno']]=crsp_d[['permco','permno']].astype(int)

    # perm_list = [10031,54594,29591,17057] ########################################
    # crsp_d = crsp_d[crsp_d['permno'].isin(perm_list)] ########################################

    # calculate market equity
    crsp_d['me']=crsp_d['prc'].abs()*crsp_d['shrout'] 
    crsp_d=crsp_d.drop(['prc','shrout'], axis=1)
    crsp_d = crsp_d[crsp_d['me'] != 0]
    crsp_d = crsp_d.dropna(subset=['me'], how='any')
    crsp_d=crsp_d.sort_values(by=['date','permco','me'])
    ### Aggregate Market Cap ###
    # sum of me across different permno belonging to same permco a given date
    crsp_summe = crsp_d.groupby(['date','permco'])['me'].sum().reset_index()
    # largest mktcap within a permco/date
    crsp_maxme = crsp_d.groupby(['date','permco'])['me'].max().reset_index()
    # join by jdate/maxme to find the permno
    crsp=pd.merge(crsp_d, crsp_maxme, how='inner', on=['date','permco','me'])
    # drop me column and replace with the sum me
    crsp=crsp.drop(['me'], axis=1)
    # join with sum of me to get the correct market cap info
    crsp=pd.merge(crsp, crsp_summe, how='inner', on=['date','permco'])
    # sort by permno and date and also drop duplicates
    crsp=crsp.sort_values(by=['permno','date']).drop_duplicates()
    crsp['day']=crsp['date'].dt.day
    crsp['month']=crsp['date'].dt.month
    crsp['year']=crsp['date'].dt.year
    return crsp

def preparing_ccm(comp):
    ccm = pd.read_csv(resource + "wrds_ccm.csv", parse_dates=['linkdt', 'linkenddt'])
    # if linkenddt is missing then set to today date
    ccm['linkenddt']=ccm['linkenddt'].fillna(pd.to_datetime('today'))
    ccm=pd.merge(comp,ccm,how='left',on=['gvkey'])
    ccm['start_disclosure_date']=ccm['datadate'] + MonthEnd(4)
    # set link date bounds
    ccm=ccm[(ccm['start_disclosure_date']>=ccm['linkdt'])&(ccm['start_disclosure_date']<=ccm['linkenddt'])]
    ccm=ccm[['gvkey','permno','datadate','start_disclosure_date','dlc','dltt']]
    ccm['debt']=ccm['dlc']+.5*ccm['dltt']*1000  # The CRSP data is in thousands while Compustat data is in millions
    ccm=ccm.drop(['dlc','dltt'], axis=1)
    ccm['end_public_date']=ccm.groupby(['gvkey'])['start_disclosure_date'].shift(-1)
    ccm['end_public_date']=ccm['end_public_date'].fillna(ccm['start_disclosure_date']+MonthEnd(12))
    return ccm

def main():
    print('preparing compustat...')
    comp = preparing_comp()
    years = [2005,2006,2007,2008]
    for year in years:
        print(f'preparing crsp for {str(year)}...')
        crsp = preparing_crsp(year)
        print('preparing cmm...')
        ccm = preparing_ccm(comp)
        default_p = crsp.groupby(['permno','year','month'])['day'].max().reset_index()
        default_p['date'] = pd.to_datetime(default_p[['year','month', 'day']]) + MonthEnd(0)
        default_p=default_p.drop(['year','month','day'], axis=1)
        default_p = pd.merge(default_p, ccm, how='left', on=['permno'])
        default_p = default_p.loc[(default_p.start_disclosure_date < default_p.date) & (default_p.date <= default_p.end_public_date)]
        fred = pd.read_csv(resource + "fred.csv", parse_dates=['date'])
        rf = fred[['date','DGS1']] # 1 year T-bill
        default_p=pd.merge(default_p, rf, how='left', on=['date'])
        T = 1

        # default_p[['Va', 'sigma_a', 'p_def', 'DD']] = default_p.progress_apply(lambda x:  row_dd(x,crsp,T), axis=1, result_type='expand') #########################
        # default_p.dropna(subset=['Va'], inplace=True)
        # default_p.to_csv(results + 'prova_default.csv', index=False) #################################

        # Select the rows where the 'date' column is in the current year
        year_data = default_p[default_p['date'].dt.year == year]
        year_data[['Va', 'sigma_a', 'p_def', 'DD']] = year_data.progress_apply(lambda x:  row_dd(x,crsp,T), axis=1, result_type='expand')
        year_data.dropna(subset=['Va'], inplace=True)
        # output the prepared data
        year_data.to_csv(results + f'p_def_{year}.csv', index=False)

if __name__ == '__main__':
    main()