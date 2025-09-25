import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import base64
import io
from scipy import stats
from scipy.stats import kruskal, f_oneway, mannwhitneyu, ttest_ind
import itertools
import warnings
warnings.filterwarnings('ignore')

# Local Imports 
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

def get_stats(df: pd.DataFrame) -> list:
    """Get the statistics to render in the statistical analysis tab
    TO-DO: Add a combobox to select variable to analyse
    Visualise only the results for that varible?
    Use the same style of the table in overview (centre text)
    Separate the title from the tabs 
    Add graph of strain vs recovery in that tab - similar to the one in the whoop
    add underheath the heatmap of the cycle phase

    """
    # Statistical tests and detailed analysis
    
    metrics = [ids.RECOVERY_SCORE, ids.RESTING_HR, ids.HRV,
               ids.DAY_STRAIN, ids.SLEEP_EFFICIENCY]
    
    stats_results = []
    
    for metric in metrics:
        if metric in df.columns:
            follicular_data = df[df[ids.PHASE] == ids.FOLLICULAR][metric].dropna()
            ovulatory_data = df[df[ids.PHASE] == ids.OVULATORY][metric].dropna()
            luteal_data = df[df[ids.PHASE] == ids.LUTEAL][metric].dropna()
            menstrual_data = df[df[ids.PHASE] == ids.MENSTRUAL][metric].dropna()
            
            if (len(follicular_data) > 0 and len(ovulatory_data) > 0
                    and len(luteal_data) > 0 and len(menstrual_data) > 0):
                
                # Run analysis
                results = analyze_statistics(
                    follicular_data, 
                    ovulatory_data, 
                    luteal_data, 
                    menstrual_data, 
                    metric_name=metric
                )

                stats_results.append(results)

    # Create tables
    descriptive_table_data = create_descriptive_stats_table(stats_results)
    overall_test_data = create_overall_test_table(stats_results)
    pairwise_table_data = create_pairwise_comparison_table(stats_results, use_corrected=True)
    
    return descriptive_table_data, overall_test_data, pairwise_table_data

def analyze_statistics(follicular_data: pd.Series, 
                        ovulatory_data: pd.Series,
                        luteal_data: pd.Series, 
                        menstrual_data: pd.Series,
                        metric_name: str = "metric") -> dict[str]:
    """
    Complete statistical analysis of menstrual cycle phases
    
    Parameters:
    -----------
    follicular_data, ovulatory_data, luteal_data, menstrual_data : pd.Series
        Data for each menstrual cycle phase
    metric_name : str
        Name of the metric being analyzed
    
    Returns:
    --------
    Dict containing all statistical analysis results
    """
    
    # Organize data
    data_groups = {
        'Follicular': follicular_data,
        'Ovulatory': ovulatory_data,
        'Luteal': luteal_data,
        'Menstrual': menstrual_data
    }
    
    # Perform analysis
    descriptive_stats = calculate_descriptive_stats(data_groups)
    overall_test = perform_overall_test(data_groups)
    
    # Only perform pairwise tests if overall test is significant
    pairwise_results = {}
    corrected_pairwise = {}
    
    if overall_test.get('significant', False):
        # Determine if parametric tests should be used
        parametric = overall_test['test_used'] == 'One-way ANOVA'
        pairwise_results = perform_pairwise_tests(data_groups, parametric)
        corrected_pairwise = bonferroni_correction(pairwise_results)
    
    return {
        'metric': metric_name,
        'descriptive_statistics': descriptive_stats,
        'overall_test': overall_test,
        'pairwise_comparisons': pairwise_results,
        'pairwise_corrected': corrected_pairwise
    }

def calculate_descriptive_stats(data_groups: dict[pd.Series]) -> dict[str, dict[str, float]]:

    """
    Calculate descriptive statistics for each phase
    """
    descriptive_stats = {}
    
    for phase, data in data_groups.items():
        if len(data) > 0:
            descriptive_stats[phase] = {
                'n': len(data),
                'mean': data.mean(),
                'median': data.median(),
                'std': data.std(),
                'min': data.min(),
                'max': data.max(),
                'q25': data.quantile(0.25),
                'q75': data.quantile(0.75)
            }
        else:
            descriptive_stats[phase] = {
                'n': 0,
                'mean': np.nan,
                'median': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'q25': np.nan,
                'q75': np.nan
            }
    
    return descriptive_stats

def perform_overall_test(data_groups: dict[pd.Series]) -> dict[str]:
    """
    Perform overall test to check if there are any differences between groups
    Uses ANOVA if assumptions are met, otherwise Kruskal-Wallis
    """
    # Filter out empty groups
    valid_groups = {phase: data for phase, data in data_groups.items() if len(data) > 0}
    
    if len(valid_groups) < 2:
        return {'test_used': 'None', 'reason': 'Insufficient groups with data'}
    
    # Check assumptions
    normality_results = check_normality(valid_groups)
    variance_results = check_equal_variances(valid_groups)
    
    # Determine if parametric test is appropriate
    all_normal = all(result['is_normal'] for result in normality_results.values() 
                    if result['is_normal'] is not None)
    equal_variances = variance_results['equal_variances']
    
    data_lists = [data.values for data in valid_groups.values()]
    
    if all_normal and equal_variances:
        # Use one-way ANOVA
        stat, p_value = f_oneway(*data_lists)
        test_used = 'One-way ANOVA'
    else:
        # Use Kruskal-Wallis (non-parametric alternative)
        stat, p_value = kruskal(*data_lists)
        test_used = 'Kruskal-Wallis'
    
    return {
        'test_used': test_used,
        'statistic': stat,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'assumptions': {
            'normality': normality_results,
            'equal_variances': variance_results
        }
    }

def check_normality(data_groups: dict[pd.Series]) -> dict[str, dict[str]]:
    """
    Check normality of each phase using Shapiro-Wilk test
    Returns results for each phase
    """
    normality_results = {}
    
    for phase, data in data_groups.items():
        if len(data) >= 3:  # Shapiro-Wilk requires at least 3 samples
            stat, p_value = stats.shapiro(data)
            normality_results[phase] = {
                'statistic': stat,
                'p_value': p_value,
                'is_normal': p_value > 0.05,
                'n_samples': len(data)
            }
        else:
            normality_results[phase] = {
                'statistic': None,
                'p_value': None,
                'is_normal': False,
                'n_samples': len(data)
            }
    
    return normality_results

def check_equal_variances(data_groups: dict[str, pd.Series]) -> dict[str]:
    """
    Check for equal variances using Levene's test
    """
    data_lists = [data.values for data in data_groups.values() if len(data) > 0]
    
    if len(data_lists) >= 2:
        stat, p_value = stats.levene(*data_lists)
        return {
            'statistic': stat,
            'p_value': p_value,
            'equal_variances': p_value > 0.05
        }
    else:
        return {'statistic': None, 'p_value': None, 'equal_variances': None}

def perform_pairwise_tests(data_groups: dict[str, pd.Series], 
                          parametric: bool = None) -> dict[str, dict[str]]:
    """
    Perform pairwise comparisons between all phase combinations
    """
    # Filter out empty groups
    valid_groups = {phase: data for phase, data in data_groups.items() if len(data) > 0}
    
    if len(valid_groups) < 2:
        return {}
    
    # If parametric is not specified, determine based on data
    if parametric is None:
        normality_results = check_normality(valid_groups)
        variance_results = check_equal_variances(valid_groups)
        
        all_normal = all(result['is_normal'] for result in normality_results.values() 
                        if result['is_normal'] is not None)
        equal_variances = variance_results['equal_variances']
        parametric = all_normal and equal_variances
    
    pairwise_results = {}
    phase_combinations = list(itertools.combinations(valid_groups.keys(), 2))
    
    for phase1, phase2 in phase_combinations:
        data1 = valid_groups[phase1]
        data2 = valid_groups[phase2]
        
        comparison_key = f"{phase1} vs {phase2}"
        
        if parametric:
            # Use independent t-test
            stat, p_value = ttest_ind(data1, data2, equal_var=True)
            test_used = "Independent t-test"
        else:
            # Use Mann-Whitney U test
            stat, p_value = mannwhitneyu(data1, data2, alternative='two-sided')
            test_used = "Mann-Whitney U"
        
        pairwise_results[comparison_key] = {
            'test_used': test_used,
            'statistic': stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'mean_diff': data1.mean() - data2.mean() if parametric else None,
            'median_diff': data1.median() - data2.median() if not parametric else None
        }
    
    return pairwise_results

def bonferroni_correction(pairwise_results: dict[str, dict[str]]) -> dict[str, dict[str]]:
    """
    Apply Bonferroni correction to pairwise comparisons
    """
    corrected_results = pairwise_results.copy()
    n_comparisons = len(pairwise_results)
    
    for comparison, results in corrected_results.items():
        results['p_value_corrected'] = min(results['p_value'] * n_comparisons, 1.0)
        results['significant_corrected'] = results['p_value_corrected'] < 0.05
    
    return corrected_results

def create_descriptive_stats_table(all_results: list[dict[str]]) -> list[dict[str]]:

    """
    Create a table with descriptive statistics for all metrics and phases
    """
    table_data = []
    
    for result in all_results:
        metric = result['metric']
        desc_stats = result['descriptive_statistics']
        
        for phase, stats in desc_stats.items():
            if stats['n'] > 0:  # Only include phases with data
                table_data.append({
                    'Metric': metric,
                    'Phase': phase,
                    'N': stats['n'],
                    'Mean': round(stats['mean'], 2),
                    'Median': round(stats['median'], 2),
                    'Std Dev': round(stats['std'], 2),
                    'Min': round(stats['min'], 2),
                    'Max': round(stats['max'], 2)
                })
    
    return table_data

def create_overall_test_table(all_results: list[dict[str]]) -> list[dict[str]]:
    """
    Create a table showing overall test results for each metric
    """
    table_data = []
    
    for result in all_results:
        metric = result['metric']
        overall = result['overall_test']
        
        if 'statistic' in overall and overall['statistic'] is not None:
            table_data.append({
                'Metric': metric,
                'Test Used': overall['test_used'],
                'Test Statistic': round(overall['statistic'], 4),
                'P-value': f"{overall['p_value']:.6f}",
                'Significant': 'Yes' if overall['significant'] else 'No',
                'Interpretation': 'Phases differ significantly' if overall['significant'] else 'No significant differences'
            })
        else:
            table_data.append({
                'Metric': metric,
                'Test Used': overall.get('test_used', 'None'),
                'Test Statistic': 'N/A',
                'P-value': 'N/A',
                'Significant': 'N/A',
                'Interpretation': overall.get('reason', 'Insufficient data')
            })
    
    return table_data

def create_pairwise_comparison_table(all_results: list[dict[str]], 
                                        use_corrected: bool = True) -> list[dict[str]]:
    """
    Create a table showing pairwise comparisons for each metric
    """
    table_data = []
    
    for result in all_results:
        metric = result['metric']
        
        # Choose corrected or uncorrected results
        pairwise_results = result['pairwise_corrected'] if use_corrected else result['pairwise_comparisons']
        
        if pairwise_results:
            for comparison, comp_result in pairwise_results.items():
                # Determine effect size column based on test type
                effect_size_col = 'Mean Difference' if 'mean_diff' in comp_result else 'Median Difference'
                effect_size_val = comp_result.get('mean_diff') or comp_result.get('median_diff')
                
                p_value_col = 'P-value (Corrected)' if use_corrected else 'P-value'
                p_value_key = 'p_value_corrected' if use_corrected else 'p_value'
                significance_key = 'significant_corrected' if use_corrected else 'significant'
                
                table_data.append({
                    'Metric': metric,
                    'Comparison': comparison,
                    'Test Used': comp_result['test_used'],
                    effect_size_col: round(effect_size_val, 3) if effect_size_val is not None else 'N/A',
                    p_value_col: f"{comp_result[p_value_key]:.6f}",
                    'Significant': 'Yes' if comp_result[significance_key] else 'No'
                })
        else:
            # Add row indicating no pairwise tests performed
            table_data.append({
                'Metric': metric,
                'Comparison': 'None performed',
                'Test Used': 'N/A',
                'Effect Size': 'N/A',
                'P-value (Corrected)' if use_corrected else 'P-value': 'N/A',
                'Significant': 'N/A'
            })
    
    return table_data








