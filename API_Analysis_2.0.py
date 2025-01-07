import pandas as pd
import numpy as np
from datetime import date
from glob import glob

# Define file paths and columns to drop/reorder
USER_ACCOUNTS = 'QuickBase-Account*.csv'
USER_READS = 'user_reads*.csv'
INTEGRATION_READS = 'integration_reads*.csv'

USER_ACCOUNTS_DROP = [
    'FIRST NAME', 'LAST NAME', 'USERNAME', 'LAST ACCESS >180 D AGO', 'IN ANY GROUP',
    'GROUP MANAGER', 'CAN CREATE APPS', 'APP MANAGER', 'IN REALM DIRECTORY', 
    'REALM APPROVED', 'IS SERVICE ACCOUNT']
USER_READS_DROP = ['ACTION']
INTEGRATION_READS_DROP = ['TYPE', 'ACTION', 'ACCOUNT_ID', 'CHANNEL']

USER_ACCOUNTS_REORDER = ['USER ID', 'LAST ACCESS', 'ACCESS STATUS', 'EMAIL']
USER_READS_REORDER = ['USER_ID', 'APP_ID', 'TIMESTAMP', 'USER_AGENT']
INTEGRATION_READS_REORDER = ['USER_ID', 'APP_ID', 'PIPELINE_ID', 'TIMESTAMP', 'USER_AGENT']

ACC_USER = [ # Email, App_ID
    ['karen.small@email.com', 'abcdefghi'], #96385274 and should have 2
    ['kevin.tall@gmail.com', 'jklmnopqr']]  #98765432 and should have 1

def Handle_errors(func):
    """Decorator for handling errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, KeyError) as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return pd.DataFrame()
    return wrapper

@Handle_errors
def Read_csv(pattern, col_to_drop, col_order):
    """Read and process CSV files matching the pattern."""
    csv_files = glob(pattern)
    if not csv_files:
        raise FileNotFoundError("No files found matching the pattern.")
    
    # Read the first CSV file and check if PIPELINE_ID column exists
    df = pd.read_csv(csv_files[0], usecols=lambda col: col not in set(col_to_drop))

    # If PIPELINE_ID exists, read it as a string
    if 'PIPELINE_ID' in df.columns:
        df = pd.read_csv(csv_files[0], usecols=lambda col: col not in set(col_to_drop), dtype={'PIPELINE_ID': str})
    
    return df[col_order]

@Handle_errors
def Save_csv(df):
    """Save DataFrame to CSV file."""
    filename = f'user_insight_summary_{date.today().strftime("%d%b%Y")}.csv'
    df.to_csv(filename, index=False)

@Handle_errors
def Clean_user_acc(df):
    """Clean user account data."""
    df['NUM_ID'] = df['USER ID'].str.split('.', expand=True)[0]
    df = df[df['ACCESS STATUS'] == 'Paid seat'].copy()
    df = df.drop(columns=['LAST ACCESS', 'ACCESS STATUS'])
    df['NUM_ID'] = df['NUM_ID'].astype(int)
    return df

@Handle_errors
def Get_date_range(df):
    """Get the date range from the TIMESTAMP column."""
    df['DATE'] = pd.to_datetime(df['TIMESTAMP']).dt.date
    return df['DATE'].min(), df['DATE'].max()

@Handle_errors
def Calc_freq(df):
    """Calculate frequency of occurrences."""
    df = df.drop(columns=['USER_AGENT'])

    freq_by_all = df[df['PIPELINE_ID'].notna() & df['USER_ID'].notna() & df['APP_ID'].notna()].groupby(['PIPELINE_ID', 'USER_ID', 'APP_ID']).size().reset_index(name='FREQUENCY')
    freq_by_pip_user = df[df['PIPELINE_ID'].notna() & df['USER_ID'].notna() & df['APP_ID'].isna()].groupby(['PIPELINE_ID', 'USER_ID']).size().reset_index(name='FREQUENCY')
    freq_by_pip_app = df[df['PIPELINE_ID'].notna() & df['USER_ID'].isna() & df['APP_ID'].notna()].groupby(['PIPELINE_ID', 'APP_ID']).size().reset_index(name='FREQUENCY')
    freq_by_user_app = df[df['PIPELINE_ID'].isna() & df['USER_ID'].notna() & df['APP_ID'].notna()].groupby(['USER_ID', 'APP_ID']).size().reset_index(name='FREQUENCY')
    freq_by_pip = df[df['PIPELINE_ID'].notna() & df['APP_ID'].isna() & df['USER_ID'].isna()].groupby('USER_ID').size().reset_index(name='FREQUENCY')
    freq_by_user = df[df['PIPELINE_ID'].isna() & df['APP_ID'].isna() & df['USER_ID'].notna()].groupby('USER_ID').size().reset_index(name='FREQUENCY')
    freq_by_app = df[df['PIPELINE_ID'].isna() & df['USER_ID'].isna() & df['APP_ID'].notna()].groupby('APP_ID').size().reset_index(name='FREQUENCY')
        
    return  pd.concat([freq_by_all, freq_by_pip_user, freq_by_pip_app, freq_by_user_app, freq_by_pip, freq_by_user, freq_by_app], ignore_index=True)

@Handle_errors
def Clean_frequency_columns(df, columns):
    """Replace infinite values with NaN, fill NaN with 0, and convert to appropriate types."""
    for col in columns:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0)
        if col == 'USER_ID' or col == 'ANNUALIZED_FREQUENCY':
            df[col] = df[col].astype(int)
    return df

@Handle_errors
def Annualized_api(df, days):
    """Calculate annualized API."""
    df['ANNUALIZED_FREQUENCY'] = (df['FREQUENCY'] / days) * 365
    df['ANNUALIZED_FREQUENCY'] = df['ANNUALIZED_FREQUENCY'].round()
    return df

@Handle_errors
def User_id_full(df, user_id):
    """Update user info with full user ID."""
    df_is_zero = df[df['USER_ID'] == 0]
    df_non_zero = df[df['USER_ID'] != 0]

    merged_df = pd.merge(df_non_zero, user_id, left_on='USER_ID', right_on='NUM_ID')

    final_df = pd.concat([df_is_zero, merged_df], ignore_index=True)
    final_df.drop(columns=['NUM_ID', 'USER_ID'], inplace=True)

    return final_df

@Handle_errors
def Populate_data(df):
    """Populate missing APP_IDs based on email addresses."""
    for email, app_id in ACC_USER:
        df.loc[(df['APP_ID'].isna()) & (df['EMAIL'] == email), 'APP_ID'] = app_id
    return df

@Handle_errors
def Frequency(df, time, user_acc):
    """Calculate and clean frequency data, then save the results."""
    freq = Calc_freq(df)

    freq_columns = ['FREQUENCY', 'PIPELINE_ID', 'USER_ID', 'APP_ID']
    freq = Clean_frequency_columns(freq, freq_columns)
    
    annualized = Annualized_api(freq, time)
    annualized = Clean_frequency_columns(annualized, ['ANNUALIZED_FREQUENCY'])

    annualized_df = User_id_full(annualized, user_acc)
    annualized_df.replace(0, np.nan, inplace=True)
    annualized_df = Populate_data(annualized_df)

    Save_csv(annualized_df)

@Handle_errors
def Main(user_acc, user_read, int_read):
    """Main function to clean data, calculate frequencies, and save results."""
    user_acc = Clean_user_acc(user_acc)

    reads_both = pd.concat([int_read, user_read])
    reads_both['TIMESTAMP'] = reads_both['TIMESTAMP'].str.strip()
    
    fdate, ldate = Get_date_range(reads_both)
    if fdate is None or ldate is None:
        print("Error: Unable to determine date range.")
        return
    day_amnt = ((ldate - fdate).days)
    print(day_amnt)
    
    reads_both = reads_both.drop(columns=['TIMESTAMP', 'DATE'])

    Frequency(reads_both, day_amnt, user_acc)

df_user_acc = Read_csv(USER_ACCOUNTS, USER_ACCOUNTS_DROP, USER_ACCOUNTS_REORDER)
df_user_read = Read_csv(USER_READS, USER_READS_DROP, USER_READS_REORDER)
df_int_read = Read_csv(INTEGRATION_READS, INTEGRATION_READS_DROP, INTEGRATION_READS_REORDER)

Main(df_user_acc, df_user_read, df_int_read)

print("Finished!")
