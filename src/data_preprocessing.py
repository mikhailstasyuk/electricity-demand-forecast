#!/usr/bin/env python
# coding: utf-8
import pandas as pd

from sklearn.preprocessing import OneHotEncoder
# from prefect import task, flow
import hydra

from db_store import DatabaseHandler

# @task(retries=3, retry_delay_seconds=5)
# def read_from_db(
#     tabname: str,
#     dbname: str,
#     schema: list,
#     user: str,
#     password: str,
#     host: int,
#     port: int,
#     connect_timeout: int
# ) -> pd.DataFrame:
    
#     DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
#     try:
#         engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': connect_timeout})
#     except:
#         print("Failed to establish connection to the database.")

#     schema_str = ",".join(schema)
#     query = text(f'SELECT {schema_str} FROM {tabname};')

#     with engine.connect() as conn:
#         df = pd.read_sql_query(query, conn).reset_index(drop=True)
#     return df

# @task(retries=3, retry_delay_seconds=5)
def filter_by_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame using the Interquartile Range (IQR) method.

    Args:
        df (pd.DataFrame): DataFrame containing the "value" column.

    Returns:
        pd.DataFrame: Filtered DataFrame with outliers removed.
    """
    # Compute the IQR for the "value" column
    Q1 = df['value'].quantile(0.25)
    Q3 = df['value'].quantile(0.75)
    IQR = Q3 - Q1

    # Define bounds for the acceptable range
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Remove rows where the "value" column is outside the bounds.
    filt = (df['value'] >= lower_bound) & (df['value'] <= upper_bound)
    df_filtered = df[filt]

    return df_filtered

# @task(retries=3, retry_delay_seconds=5)
def extract_features(
        df: pd.DataFrame,
        window_size=7,
        inference=False
) -> pd.DataFrame:
    """
    Extract date-related and rolling statistics features from DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with 'period' and 'value' columns.

    Returns:
        pd.DataFrame: DataFrame with added date features and rolling stats.
    """
    df = df.copy()
    df['period'] = df['period'].astype('datetime64[ns]')
    df['timezone'] = df['timezone'].astype('category')
    df['value'] = df['value'].astype('int64')

    # Separate date features
    df['year'] = df['period'].dt.year.astype('int16')
    df['month'] = df['period'].dt.month.astype('int16')
    df['day'] = df['period'].dt.day.astype('int16')

    # Extract the day of the week
    df['day_of_week'] = df['period'].dt.day_name().astype('category')

    # Extract quarterly and weekly information to capture seasonality
    df['quarter'] = df['period'].dt.quarter.astype('int8')
    df['week_of_year'] = df['period'].dt.isocalendar().week.astype('int16')

    # Mark the weekends
    df['is_weekend'] = (df['period'].dt.weekday >= 5).astype('int8')
    
    if not inference:
        # Create rolling mean feature
        df['rolling_mean'] = df['value'].rolling(window=window_size).mean()
    
        # Create rolling standard deviation feature
        df['rolling_std'] = df['value'].rolling(window=window_size).std()
    
    # Remove NaNs introduced by the rolling mean and std
    df = df.dropna().copy().reset_index(drop=True)

    return df

# @task(retries=3, retry_delay_seconds=5)
def transform_to_supervised(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform DataFrame into a supervised learning format.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with 'lag' column and 'period' dropped.
    """
    
    # Create 'lag' column by shifting 'value' column
    df.loc[:, 'lag'] = df['value'].shift()

    # Remove rows with missing values (NaN) due to the shift
    df.dropna(inplace=True)

    # Convert 'lag' column to unsigned 64-bit integer type
    df.lag = df.lag.astype('int64')

    # Drop the 'period' column from the DataFrame
    df = df.drop(columns=['period'])
    return df

# @task(retries=3, retry_delay_seconds=5)
def encode_categorical(df: pd.DataFrame, ohe=None, fit=True) -> pd.DataFrame:
    """
    Encode categorical columns as dummy variables.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with categorical columns encoded as dummy variables.
    """ 
    df = df.reset_index(drop=True)
    
    if ohe == None:
        ohe = OneHotEncoder(sparse_output=False)

    # List of columns to encode as dummy variables
    feat_to_enc = df.select_dtypes('category')

    # Get dummy variables for the specified columns
    if fit == True:
        dummies = pd.DataFrame(ohe.fit_transform(feat_to_enc))
    else:
        dummies = pd.DataFrame(ohe.transform(feat_to_enc))
    dummies.columns = ohe.get_feature_names_out()
    
    # Concatenate the dummy variables with the original DataFrame
    df = pd.concat((df.drop(columns=feat_to_enc.columns), dummies), axis=1)
    return df, ohe

def prepare_for_inference(df: pd.DataFrame,
        last_day_rolling_vals: pd.DataFrame,
        ohe: OneHotEncoder, 
        schema: list
) -> pd.DataFrame:
        df = extract_features(df, inference=True)
        df = df.rename(columns={'value': 'lag'})
        df, _ = encode_categorical(df, ohe=ohe, fit=False)
        df[['rolling_mean', 'rolling_std']] = last_day_rolling_vals
        X_recent = df[schema]
        return X_recent

# @hydra.main(config_path='conf/', config_name='config.yaml')
# @flow(name="data_preprocessing flow", retries=3, retry_delay_seconds=5)
def preprocess(df):
    # Clean it up, extract date features and running statistics.
    df_no_outliers = filter_by_iqr(df)
    df_newfeat= extract_features(df_no_outliers)
    
    # Preprocess the dataset for model input.
    df_transformed = transform_to_supervised(df_newfeat)
    df_encoded, ohe = encode_categorical(df_transformed)
    return df_encoded, ohe

if __name__ == "__main__":
    preprocess()