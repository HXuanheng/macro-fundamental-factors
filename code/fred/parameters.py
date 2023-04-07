# Define start and end dates
start_date = '1800-01-01'           #YYYY-MM-DD
end_date = '2022-12-31'             #YYYY-MM-DD

# Define some parameters
'''
Frequency without period description can be one of:
                "d": Daily
                "w": Weekly
                "bw": Biweekly
                "m": Monthly
                "q": Quarterly
                "sa": Semiannual
                "a": Annual
'''
frequency = 'm'

'''
aggregation_method is moot. Can be one of:
                "avg": average
                "sum": sum
                "eop": end of period.
'''
aggregation_method = 'eop'

# File position (do not change)
resources="code/fred/"
results="data/pulled/"