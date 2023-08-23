#!/usr/bin/env python
# coding: utf-8
import os
import pickle
from hydra import initialize, compose
from xgboost import XGBRegressor
import train, hp_optimization, register_model
from data_preprocessing import preprocess, prepare_for_inference
import db_store
# from prefect import flow

# @flow(name='train_flow', retries=3, retry_delay_seconds=5)
def train_flow():
    with initialize(
        version_base=None, 
        config_path='conf/', 
        job_name='demand-forecast'
    ):
        config = compose(config_name='config.yaml')   

    db_handler = db_store.DatabaseHandler(config)

    db_handler.connect()

    input_schema = ['period', 'timezone', 'value']
    tab_name = config.data.tab_params.tabname
    schema_str = ",".join(input_schema)

    query = f'SELECT {schema_str} FROM {tab_name};'
    
    df = db_handler.query(query)
    
    db_handler.close()

    df_processed, ohe = preprocess(df)
    
    # Separate features and target.
    X = df_processed.drop(columns=['value'])
    y = df_processed.value
    
    schema = X.columns.tolist()
    
    last_day_demand = df.iloc[-1].to_frame().T
    last_day_rolling_vals = df_processed.iloc[-1][['rolling_mean', 'rolling_std']]
    recent_prepared = prepare_for_inference(
        df = last_day_demand,
        last_day_rolling_vals=last_day_rolling_vals,
        ohe=ohe,
        schema=schema
    )

    print('Saving artifacts...')
    artifacts = [ohe, schema, recent_prepared]
    artifacts_path = os.getcwd() + '/artifacts'
    if not os.path.exists(artifacts_path):
        os.mkdir(artifacts_path)
    with open(artifacts_path + '/afts.bin', 'wb') as f_out:
        pickle.dump(artifacts, f_out)

    print('Tuning hyperparameters...')
    best_params = hp_optimization.tune_hyperparameters(
        config=config,
        train_func=train.train,
        X=X, y=y,
        n_trials=config.hyperparameters.N_TRIALS,
        n_splits=config.training.N_SPLITS,

    )
    
    print('Training using best hyperparameters...')
    model = XGBRegressor(
        **best_params,
        early_stopping_rounds=
        config.hyperparameters.sample_space.EARLY_STOPPING_ROUNDS,
        random_state=config.hyperparameters.SEED
    )
    
    train.train(
        config=config,
        model=model, 
        X=X, y=y, 
        n_splits=config.training.N_SPLITS, 
        track=True
    )

    print('Registering the model...')
    register_model.choose_and_register(config)

if __name__ == "__main__":
    train_flow()