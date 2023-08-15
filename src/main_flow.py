#!/usr/bin/env python
# coding: utf-8

import os
import json
from xgboost import XGBRegressor
import data_preprocessing, train
from prefect import flow

@flow(name='main_flow', retries=3, retry_delay_seconds=3, log_prints=True)
def train_flow():
    df, ohe = data_preprocessing.preprocess()

    # Separate features and target.
    X = df.drop(columns=['value'])
    y = df.value
    
    schema = X.columns.tolist()
    most_recent_vals = df.iloc[-1][['rolling_mean', 'rolling_std']]
    
    N_SPLITS = 9
    best_hp_path = 'artifacts/best_hp.json'

    if os.path.exists(best_hp_path):
        with open(best_hp_path, 'r') as f_in:
            best_params = json.load(f_in)

    model = XGBRegressor(**best_params)
    train.train(model, X, y, n_splits=N_SPLITS, track=True)
    print(model)
    
    # features_to_drop = []
    # artifacts = [ohe, features_to_drop, schema, most_recent_vals]
    # return (model, artifacts)

if __name__ == "__main__":
    train_flow()