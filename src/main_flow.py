#!/usr/bin/env python
# coding: utf-8

import hydra
import os
import json
from xgboost import XGBRegressor
import data_preprocessing, train, hp_optimization
from prefect import flow

@hydra.main(config_path='conf/', config_name='config.yaml')
@flow(name='train_flow', retries=3, retry_delay_seconds=5)
def train_flow(config):
    df, ohe = data_preprocessing.preprocess()

    # Separate features and target.
    X = df.drop(columns=['value'])
    y = df.value
    
    schema = X.columns.tolist()
    most_recent_vals = df.iloc[-1][['rolling_mean', 'rolling_std']]
    
    best_params = hp_optimization.tune_hyperparameters(
        config=config,
        train_func=train.train,
        X=X, y=y,
        n_trials=config.hyperparameters.N_TRIALS,
        n_splits=config.training.N_SPLITS,

    )
    model = XGBRegressor(**best_params)
    train.train(config=config,
                model=model, 
                X=X, y=y, 
                n_splits=config.training.N_SPLITS, 
                track=True)
    print(model)
    
    # features_to_drop = []
    # artifacts = [ohe, features_to_drop, schema, most_recent_vals]
    # return (model, artifacts)

if __name__ == "__main__":
    train_flow()