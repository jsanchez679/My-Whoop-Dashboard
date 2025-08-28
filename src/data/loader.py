import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import base64
import io
import warnings
warnings.filterwarnings('ignore')

from src.components import ids

# class DataSchema:
#     AMOUNT = "amount"
#     CATEGORY = "category"
#     DATE = "date"
#     MONTH = "month"
#     YEAR = "year"

# Helper functions
def parse_date(date_str: str) -> datetime:
    """Parse date string in DD/MM/YY HH:MM format"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except:
        try: 
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
        except: 
            return None


def parse_contents(contents:str , filename: str) -> pd.DataFrame:
    """Parse uploaded CSV contents"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=',')
            return df
        else:
            return None
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

def calculate_cycle_phases_custom(df: pd.DataFrame, date_col: str, menstruating_col: str, 
                                    menstrual_days: int =5, luteal_days: int=14, 
                                    ovulatory_days: int =3 ) -> pd.DataFrame:
    """
    Calculate menstrual cycle phases with customizable phase durations.
    
    Parameters:
    df: pandas DataFrame
    date_col: name of the date column
    menstruating_col: name of the menstruation column
    menstrual_days: duration of menstrual phase (default: 5)
    luteal_days: duration of luteal phase (default: 14)
    ovulatory_days: duration of ovulatory phase (default: 3)
    """
    
    df_copy = df.copy()
    
    # Initialize columns
    df_copy[ids.CYCLE_START] = False
    df_copy[ids.CYCLE_DAY_NUMBER] = 0
    df_copy[ids.CYCLE_LENGTH] = np.nan
    df_copy[ids.PHASE] = ids.UNKNOWN
    
    # Find cycle starts
    menstruation_starts = []
    prev_menstruating = 0
    
    for i, row in df_copy.iterrows():
        current_menstruating = row[menstruating_col]
        if current_menstruating == 1 and prev_menstruating == 0:
            df_copy.loc[i, ids.CYCLE_START] = True
            menstruation_starts.append(i)
        prev_menstruating = current_menstruating
    
    # Calculate cycle lengths and days
    for i in range(len(menstruation_starts)):
        start_idx = menstruation_starts[i]
        #Finds the cycle_date for the first day of the menstrual cycle
        start_date = df_copy.loc[start_idx, date_col]
        
        if i < len(menstruation_starts) - 1:
            end_idx = menstruation_starts[i + 1] - 1
            end_date = df_copy.loc[menstruation_starts[i + 1], date_col]
            cycle_length = (end_date - start_date).days
        else:
            end_idx = len(df_copy) - 1
            cycle_length = np.nan
        
        for idx in range(start_idx, end_idx + 1):
            if idx < len(df_copy):
                current_date = df_copy.loc[idx, date_col]
                cycle_day_no = (current_date - start_date).days + 1
                df_copy.loc[idx, ids.CYCLE_DAY_NUMBER] = cycle_day_no
                
                if not np.isnan(cycle_length):
                    df_copy.loc[idx, ids.CYCLE_LENGTH] = cycle_length
    
    # Custom phase determination
    def determine_phase_custom(row):
        cycle_day_number = row[ids.CYCLE_DAY_NUMBER]
        cycle_length = row[ids.CYCLE_LENGTH]
        menstruating = row[menstruating_col]
        
        if cycle_day_number == 0 or np.isnan(cycle_length):
            return ids.UNKNOWN
        
        if menstruating == 1:
            return ids.MENSTRUAL
        
        follicular_start = menstrual_days + 1
        ovulatory_start = cycle_length - luteal_days - ovulatory_days + 1
        ovulatory_end = cycle_length - luteal_days
        luteal_start = ovulatory_end + 1
        
        if cycle_day_number <= menstrual_days:
            return ids.MENSTRUAL
        elif cycle_day_number >= follicular_start and cycle_day_number < ovulatory_start:
            return ids.FOLLICULAR
        elif cycle_day_number >= ovulatory_start and cycle_day_number <= ovulatory_end:
            return ids.OVULATORY
        elif cycle_day_number >= luteal_start:
            return ids.LUTEAL
        else:
            return ids.UNKNOWN
    
    df_copy[ids.PHASE] = df_copy.apply(determine_phase_custom, axis=1)
    
    return df_copy

def process_data(physiological_df: pd.DataFrame, journal_df: pd.DataFrame, 
                    sleep_df: pd.DataFrame =None, workouts_df: pd.DataFrame =None) -> pd.DataFrame:
    """Process and join the data"""
    #At least physiological_df and journal_df needs to be uploaded
    if physiological_df is None or journal_df is None:
        return None
    
    # Parse dates
    physiological_df[ids.CYCLE_START_DATE] = physiological_df[ids.CYCLE_START_TIME].apply(parse_date)
    physiological_df[ids.CYCLE_END_DATE] = physiological_df[ids.CYCLE_END_TIME].apply(parse_date)
    journal_df[ids.CYCLE_START_DATE] = journal_df[ids.CYCLE_START_TIME].apply(parse_date)

    #Create a column to check day length and add a column to define the cycle_date (the day to which the data corresponds)
    physiological_df[ids.CYCLE_DATE] = physiological_df[ids.CYCLE_START_DATE] + timedelta(hours=12)
    
    # Process journal entries
    #Pivot to extract a column with the menstrual data
    journal_pivot = journal_df.pivot_table(
        index=ids.CYCLE_START_DATE,
        columns='Question text',
        values='Answered yes', #?
        aggfunc='first'
    ).reset_index()
    
    # Merge with physiological data
    merged_df = physiological_df.merge(
        journal_pivot,
        on=ids.CYCLE_START_DATE,
        how='left'
    )
    #Reset the index after sorting the rows by cycle_date
    # Sort by date
    merged_df = merged_df.sort_values(ids.CYCLE_DATE).reset_index(drop=True)
    
    #Perhaps calculate the average number of menstrual days from the input data
    menstrual_days = 4
    luteal_days = 14
    ovulatory_days = 3

    # Create cycle phase column
    merged_df = calculate_cycle_phases_custom(merged_df, ids.CYCLE_DATE, ids.MENSTRUATING, 
                                                menstrual_days=menstrual_days, 
                                                luteal_days=luteal_days, 
                                                ovulatory_days=ovulatory_days)
    # Clean numeric columns
    numeric_cols = [ ids.RECOVERY_SCORE, ids.RESTING_HR, ids.HRV, ids.SLEEP_PERFORMANCE, ids.DAY_STRAIN, 
                    ids.SLEEP_EFFICIENCY, ids.REM_DURATION, ids.DEEP_SLEEP_DURATION, 
                    ids.LIGHT_SLEEP_DURATION, ids.SKIN_TEMP, ids.BLOOD_O2, ids.ENERGY_BURNED, 
                    ids.RESP_RATE, ids.CYCLE_DAY_NUMBER, ids.CYCLE_LENGTH]
    
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
    
    return merged_df

def load_data(processed_data: str) -> pd.DataFrame:
    '''Read the JSON file containing the data'''
    return pd.read_json(processed_data, orient='split')

