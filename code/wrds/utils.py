from datetime import datetime, timedelta


def split_years(start_date, end_date):
    # Convert the input dates to datetime objects
    start_date = datetime.strptime(start_date, '%m/%d/%Y')
    end_date = datetime.strptime(end_date, '%m/%d/%Y')

    # Initialize the current date to the start date
    current_date = start_date

    # Initialize the list of years
    years = []

    # Loop over the years in the time period
    while current_date < end_date:
        # Calculate the last day of the current year
        last_day_of_year = datetime(current_date.year, 12, 31)
        
        # If the last day of the year is before the end date,
        # add the current year to the list of years
        if last_day_of_year < end_date:
            years.append((current_date.strftime('%m/%d/%Y'), last_day_of_year.strftime('%m/%d/%Y')))
            current_date = last_day_of_year + timedelta(days=1)
        else:
            years.append((current_date.strftime('%m/%d/%Y'), end_date.strftime('%m/%d/%Y')))
            break
    
    return years