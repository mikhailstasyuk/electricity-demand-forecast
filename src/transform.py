#!/usr/bin/env python
# coding: utf-8

import random
import optuna
import mlflow
from prefect import flow, task
from sqlalchemy import create_engine, text
import pandas as pd

import matplotlib.pyplot as plt

from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

TRACKING_URI = 'sqlite:///mlflow.db'
mlflow.set_tracking_uri(TRACKING_URI)
mlflow.set_experiment('xgboost-train')

@task(name='read_data', retries=3, retry_delay_seconds=2, log_prints=True)
def read_from_db(
    tabname: str,
    dbname: str,
    schema: list,
    user: str,
    password: str,
    host: int,
    port: int,
    connect_timeout: int
) -> pd.DataFrame:
    
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    try:
        engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': connect_timeout})
    except:
        print("Failed to establish connection to the database.")

    schema_str = ",".join(schema)
    query = text(f'SELECT {schema_str} FROM {tabname};')

    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn).reset_index(drop=True)
    return df

schema = ['period', 'timezone', 'value']
tabname = 'demand'

conn_params = {
    'tabname': tabname,
    'dbname': 'db_demand',
    'schema': schema,
    'user': 'dbuser',
    'password': '123',
    'host': 'localhost',
    'port': '5432',
    'connect_timeout': 5
}

@task(name='filter_by_iqr', retries=3, retry_delay_seconds=2, log_prints=True)
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

@task(name='extract_features', retries=3, retry_delay_seconds=2, log_prints=True)
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
    df['year'] = df['period'].dt.year.astype('uint16')
    df['month'] = df['period'].dt.month.astype('uint16')
    df['day'] = df['period'].dt.day.astype('uint16')

    # Extract the day of the week
    df['day_of_week'] = df['period'].dt.day_name().astype('category')

    # Extract quarterly and weekly information to capture seasonality
    df['quarter'] = df['period'].dt.quarter.astype('uint8')
    df['week_of_year'] = df['period'].dt.isocalendar().week.astype('uint16')

    # Mark the weekends
    df['is_weekend'] = (df['period'].dt.weekday >= 5).astype('uint8')
    
    if not inference:
        # Create rolling mean feature
        df['rolling_mean'] = df['value'].rolling(window=window_size).mean()
    
        # Create rolling standard deviation feature
        df['rolling_std'] = df['value'].rolling(window=window_size).std()
    
    # Remove NaNs introduced by the rolling mean and std
    df = df.dropna().copy().reset_index(drop=True)

    # Create a random feature as a threshold for later feature filtering
    random_feature = [random.random() for _ in range(df.shape[0])]
    df['random_feature'] = random_feature
    
    return df

@task(name='transform_to_supervised', retries=3, retry_delay_seconds=2, log_prints=True)
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
    df.lag = df.lag.astype('uint64')

    # Drop the 'period' column from the DataFrame
    df = df.drop(columns=['period'])
    return df

@task(name='encode_categorical', retries=3, retry_delay_seconds=2, log_prints=True)
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

@task(name='train', retries=3, retry_delay_seconds=2, log_prints=True)
def train(
    model: XGBRegressor, 
    X: pd.DataFrame, 
    y: pd.Series,
    n_splits: int,
    track=False
) -> tuple:
    """
    Train a model using TimeSeriesSplit cross-validation.

    Args:
        model (XGBRegressor): XGBoost regressor using scikit-learn API.
        X (pd.DataFrame): Features DataFrame.
        y (pd.Series): Target values Series.

    Returns:
        tuple: Contains average Mean Absolute Error on the training 
              set (float) and test set (float) respectively.
    """
    # Lists to store mean absolute errors for training and test sets
    mae_train_hist = []
    mae_test_hist = []
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    if track == True:
        mlflow.start_run()
        
    # Split the data using TimeSeriesSplit for cross-validation
    for train_index, test_index in tscv.split(X):
        # Split the data into training and test sets
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        # Train the model
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        
        # Predict on training and test sets
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate mean absolute error for training and test sets
        mae_train = mean_absolute_error(y_train, y_pred_train)
        mae_test = mean_absolute_error(y_test, y_pred_test)
        
        # Append the errors to their respective histories
        mae_train_hist.append(mae_train)
        mae_test_hist.append(mae_test)
        if track == True:
            mlflow.log_metric('mae_train', mae_train)
            mlflow.log_metric('mae_test', mae_test)

    # Calculate average mean absolute error for training and test sets
    mae_train_avg = sum(mae_train_hist) / len(mae_train_hist)
    mae_test_avg = sum(mae_test_hist) / len(mae_test_hist)
    if track == True:
        mlflow.end_run()
    return (mae_train_avg, mae_test_avg)

@task(
    name='remove_redundant_features', 
      retries=3, 
      retry_delay_seconds=2, 
      log_prints=True
)
def remove_redundant_features(
        model: XGBRegressor, 
        X: pd.DataFrame
) -> pd.DataFrame:
    """
    Remove features less important than a reference 'random_feature'.
    
    Args:
        model (XGBRegressor): XGBoost regressor using scikit-learn API.
        X (pd.DataFrame): Features DataFrame.
        
    Returns:
        pd.DataFrame: DataFrame with redundant features removed.
    """
    # Get feature importances and feature names
    importances = model.feature_importances_
    features = X.columns.tolist()
    
    # Create a DataFrame for feature importances
    feat_imps = pd.DataFrame({
        'feature': features,
        'importance': importances
    })
    
    # Sort features by importance
    sorted_feat_imps = feat_imps.sort_values(by='importance', ascending=False)
    sorted_feat_imps.reset_index(drop=True, inplace=True)
    
    # Find the importance threshold of 'random_feature'
    random_feature_row = sorted_feat_imps[
            sorted_feat_imps['feature'] == 'random_feature']
    thresh = random_feature_row['importance'].iloc[0]
    
    # Identify columns to drop (less important than 'random_feature')
    redundant_features = sorted_feat_imps[
            sorted_feat_imps['importance'] < thresh]
    to_drop = redundant_features['feature'].tolist()
    to_drop.append('random_feature')
    
    # Drop redundant columns
    X_new = X.drop(columns=to_drop)
    
    return (X_new, to_drop)

@flow(name='tune_hyperparameters', retries=3, retry_delay_seconds=2, log_prints=True)
def tune_hyperparameters(X, y, n_trials=100, n_splits=5):
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2, 1000),
            'max_depth': trial.suggest_int('max_depth', 1, 15),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'alpha': trial.suggest_float("alpha", 1e-5, 10, log=True),  
            'gamma': trial.suggest_float("gamma", 1e-5, 5, log=True),
            'lambda': trial.suggest_float('lambda', 1e-5, 10.0, log=True),
            'early_stopping_rounds': 50
        }

        model = XGBRegressor(**params)
        mae_train_avg, mae_test_avg = train(model, X, y, n_splits)
        return mae_test_avg

    study = optuna.create_study(direction='minimize')

    # Optimize the study, the objective function is passed in as the first argument
    study.optimize(objective, n_trials=n_trials)

    # Results
    print('Number of finished trials: ', len(study.trials))
    print('Best trial:')
    trial = study.best_trial
    
    print('Value: ', trial.value)
    print('Params: ')
    for key, value in trial.params.items():
        print(f'    {key}: {value}')
    
    return trial.params

@flow(name='training_flow', timeout_seconds=900, log_prints=True)
def main(n_trials=100) -> XGBRegressor:
    # Load the data.
    df = read_from_db(**conn_params)

    # Clean it, extract date features and running statistics.
    df_no_outliers = filter_by_iqr(df)
    df_newfeat= extract_features(df_no_outliers)
    
    # Preprocess the dataset for model input.
    df_transformed = transform_to_supervised(df_newfeat)
    df_encoded, ohe = encode_categorical(df_transformed)
    
    # Separate features and target.
    X = df_encoded.drop(columns=['value'])
    y = df_encoded.value

    most_recent_vals = df_encoded.iloc[-1][['rolling_mean', 'rolling_std']]

    model = XGBRegressor(objective='reg:squarederror', n_estimators=100)
    n_splits = 9
    mae_train_avg, mae_test_avg = train(model, X, y, n_splits=n_splits)
    print(f'Avg MAE:\nTrain: {mae_train_avg}\nTest: {mae_test_avg}')
    
    X_new, features_to_drop = remove_redundant_features(model, X)
    schema = X_new.columns.tolist()
    best_params = tune_hyperparameters(X_new, y, n_trials=n_trials)

    model = XGBRegressor(**best_params)
    train(model, X_new, y, n_splits=n_splits, track=True)

    artifacts = [ohe, features_to_drop, schema, most_recent_vals]
    return (model, artifacts)

model, artifacts = main()
ohe, features_to_drop, schema, most_recent_vals = artifacts