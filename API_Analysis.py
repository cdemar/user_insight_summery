import pandas as pd
from datetime import date
from glob import glob

def Read_csv(pattern, col_to_drop, col_order): 
    try:
        csv_files = glob(pattern)
        if not csv_files:
            raise FileNotFoundError("No files found matching the pattern.")
        
        df = pd.read_csv(csv_files[0], usecols=lambda col: col not in set(col_to_drop))
        return df[col_order]
    
    except pd.errors.EmptyDataError:
        print(f"Error: The file is empty.")
    except pd.errors.ParserError:
        print(f"Error: The file could not be parsed.")
    except KeyError as e:
        print(f"Error: Column not found - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return pd.DataFrame()

def Save_to_csv(df):
    filename = f'user_insight_summary_{date.today().strftime("%d%b%Y")}.csv'
    try:
        df.to_csv(filename, index=False)
    except PermissionError:
        print(f"Permission denied: Unable to save {filename}.")
    except Exception as e:
        print(f"An unexpected error occurred while saving the file: {e}")

def Get_date_range(reads):
    try:
        reads['DATE'] = pd.to_datetime(reads['TIMESTAMP']).dt.date
        return reads['DATE'].min(), reads['DATE'].max()
    except KeyError:
        print("Error: 'TIMESTAMP' column not found.")
    except Exception as e:
        print(f"An unexpected error occurred while getting the date range: {e}")
    return None, None

def Clean_user_acc(user_acc):
    try:
        user_acc['NUM_ID'] = user_acc['USER ID'].str.split('.', expand=True)[0]
        user_acc = user_acc[user_acc['ACCESS STATUS'] == 'Paid seat'].copy()
        return user_acc.drop(columns=['LAST ACCESS', 'ACCESS STATUS'])
    except KeyError as e:
        print(f"Error: Column not found - {e}")
    except Exception as e:
        print(f"An unexpected error occurred while cleaning user accounts: {e}")
    return pd.DataFrame()

def Get_unique_values(df, col_name):
    try:
        return df[col_name].unique().tolist()
    except KeyError:
        print(f"Error: Column '{col_name}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred while getting unique values: {e}")
    return []

def User_agent(df, user_id, app_id, pl_id):
    return

def Frequency(df, user_id, app_id, pl_id):
    '''
    - Order of Summation
		- Sum frequency of api calls by Pipeline id where not blank. 
		- Sum freq. of api calls by userid+appid where pipeline id is blank and userid and appid are not blank
		- Sum freq. of api calls by userid where app id is blank and pipeline id is blank
        - Sum freq. of api calls by app id where pipeline id and user id are blank
    '''
    df = df.drop(columns=['USER_AGENT'])
    try:
        filtered_df_user = df[df['USER_ID'].isin(user_id)]
        filtered_df_app = df[df['APP_ID'].isin(app_id)]
        filtered_df_pl = df[df['PIPELINE_ID'].isin(pl_id)]
        
        combined_df = pd.concat([filtered_df_user, filtered_df_app, filtered_df_pl]).drop_duplicates().reset_index(drop=True)
        print(combined_df)

        combined_df['FREQUENCY'] = combined_df.groupby(['USER_ID', 'APP_ID', 'PIPELINE_ID']).transform('size')

        combined_df = combined_df[combined_df['FREQUENCY'] > 0]

        return combined_df
    except Exception as e:
        print(f"An unexpected error occurred while calculating frequency: {e}")
    return pd.DataFrame()

def Annualized_api(df, days):
    try:
        df['ANNUALIZED_FREQUENCY'] = (df['FREQUENCY'] / days) * 365
        df['ANNUALIZED_FREQUENCY'] = df['ANNUALIZED_FREQUENCY'].round()
        return df
    except Exception as e:
        print(f"An unexpected error occurred while calculating annualized API: {e}")
    return pd.DataFrame()

def User_id_full(df, user_id):
    df['USER_ID'] = df['USER_ID'].astype(int)
    user_id['NUM_ID'] = user_id['NUM_ID'].astype(int)
    try:
        merged_df = pd.merge(df, user_id, left_on='USER_ID', right_on='NUM_ID')
        merged_df.drop(columns=['NUM_ID', 'USER_ID'], inplace=True)
        return merged_df
    except Exception as e:
        print(f"An unexpected error occurred while updating user info: {e}")
        return pd.DataFrame()

def Summarize_volume(user_acc, user_read, int_read):
    try:
        user_acc = Clean_user_acc(user_acc)

        reads_both = pd.concat([int_read, user_read])
        reads_both['TIMESTAMP'] = reads_both['TIMESTAMP'].str.strip()
        
        fdate, ldate = Get_date_range(reads_both)
        if fdate is None or ldate is None:
            print("Error: Unable to determine date range.")
            return
        day_amnt = ((ldate - fdate).days) - 2
        
        reads_both = reads_both.drop(columns=['TIMESTAMP', 'DATE'])
        
        user_id = Get_unique_values(reads_both, 'USER_ID')
        app_id = Get_unique_values(reads_both, 'APP_ID')
        pl_id = Get_unique_values(reads_both, 'PIPELINE_ID')
        user_agent = Get_unique_values(reads_both, 'USER_AGENT')
        
        freq = Frequency(reads_both, user_id, app_id, pl_id)
        annualized = Annualized_api(freq, day_amnt)
        user_id_full = User_id_full(annualized, user_acc)
        
        Save_to_csv(user_id_full)
    except Exception as e:
        print(f"An unexpected error occurred while summarizing volume: {e}")

# Define file paths.
user_accounts = 'QuickBase-Account*.csv'
user_reads = 'user_reads*.csv'
integration_reads = 'integration_reads*.csv'

# Define columns to drop.
user_accounts_drop = [
    'FIRST NAME','LAST NAME', 'USERNAME',
    'LAST ACCESS >180 D AGO', 'IN ANY GROUP',
    'GROUP MANAGER', 'CAN CREATE APPS', 'APP MANAGER',
    'IN REALM DIRECTORY', 'REALM APPROVED', 'IS SERVICE ACCOUNT']
user_reads_drop = ['ACTION']
integration_reads_drop = ['TYPE', 'ACTION', 'ACCOUNT_ID', 'CHANNEL'] 

# Define columns to reorder.
user_accounts_reorder = ['USER ID', 'LAST ACCESS', 'ACCESS STATUS','EMAIL']
user_reads_reorder = ['USER_ID', 'APP_ID', 'TIMESTAMP', 'USER_AGENT'] #Would like to add user agent for user and integration reads eventually. JLP 12-23-24.
integration_reads_reorder = [
    'USER_ID', 'APP_ID', 'PIPELINE_ID', 'TIMESTAMP', 'USER_AGENT']

# Extract and clean data.
df_user_acc = Read_csv(user_accounts, user_accounts_drop, user_accounts_reorder)
df_user_read = Read_csv(user_reads, user_reads_drop, user_reads_reorder)
df_int_read = Read_csv(integration_reads, integration_reads_drop, integration_reads_reorder)

# Fill NaN values in APP_ID with a placeholder
df_int_read['APP_ID'].fillna('Unknown', inplace=True)

# Summarize volume
Summarize_volume(df_user_acc, df_user_read, df_int_read)

print("Finished!") # For testing 
