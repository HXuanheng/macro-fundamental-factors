import pandas as pd
import csv
from full_fred.fred import Fred
from parameters import *
from pandas.tseries.offsets import *


# Initialize the Fred class
fred = Fred(resources + "key.txt")

# TO_CSV
to_csv=dict(sep=',', na_rep='.', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding="utf-8-sig", compression='infer', quoting=csv.QUOTE_ALL, quotechar='"', line_terminator='\r\n', chunksize=10000, date_format=None, doublequote=True, escapechar='\\', decimal='.', errors='strict')
# READ_CSV
read_csv=dict(sep=',', delimiter=None, header='infer', names=None, index_col=None, usecols=None, prefix=None, dtype=str, engine=None, converters=None, true_values=None, false_values=None, skipinitialspace=False, skiprows=None, skipfooter=0, nrows=None, na_values=None, keep_default_na=True, na_filter=True, verbose=False, skip_blank_lines=True, parse_dates=False, infer_datetime_format=False, keep_date_col=False, date_parser=None, dayfirst=False, cache_dates=True, iterator=False, chunksize=None, compression='infer', thousands=None, decimal='.', lineterminator=None, quotechar='"', quoting=csv.QUOTE_ALL, doublequote=True, escapechar='\\', comment=None, encoding=None, dialect=None, delim_whitespace=False, low_memory=True, memory_map=False, float_precision=None)

# Define the FRED series codes
series_codes=pd.read_csv(resources + "codes.csv", **read_csv)['codes'].tolist()

# Retrieve the FRED data using full_fred
pulled_data = [None] * len(series_codes)
for index, code in enumerate(series_codes):
    pulled_data[index] = fred.get_series_df(series_id=code, observation_start=start_date, observation_end=end_date, frequency=frequency, aggregation_method=aggregation_method).iloc[:, 2:]
    pulled_data[index] = pulled_data[index].rename(columns={'value': code})
    pulled_data[index] = pulled_data[index].set_index('date')
fred_data = pd.concat(pulled_data, axis=1)
fred_data.index = pd.to_datetime(fred_data.index)
fred_data = fred_data.sort_index()

if (frequency == 'm') & (aggregation_method == 'eop'):
    fred_data.index = fred_data.index + MonthEnd(0)

# Save the data to a CSV file
fred_data.to_csv(results + 'fred.csv')

print('Pulled data from Fred...')
