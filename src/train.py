#!/usr/bin/env python
# coding: utf-8

# In[6]:


import pandas as pd
import mlflow

from xgboost import XGBRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error



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

    if track == True:
        TRACKING_URI = 'sqlite:///mlflow.db'
        mlflow.set_tracking_uri(TRACKING_URI)
        mlflow.set_experiment('xgboost-train')

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