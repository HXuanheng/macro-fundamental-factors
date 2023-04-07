import pandas as pd
import datetime as dt


# File position
resource = "data/pulled/"
results = "data/generated/"

data = pd.read_csv(resource + 'wrds_crsp_d.csv', parse_dates=['date'])

for year in data['date'].dt.year.unique():
    # Select the rows where the 'date' column is in the current year
    year_data = data[data['date'].dt.year == year]
    
    # Write the selected rows to a new CSV file
    year_data.to_csv(results + f'crsp_d/crsp_d_{year}_data.csv', index=False)