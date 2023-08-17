#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import mlflow
import mlflow.pyfunc
from data_preprocessing import read_from_db
from data_preprocessing import extract_features, encode_categorical
import hydra
from hydra import utils
import pickle
from prefect import flow

@hydra.main(config_path='conf', config_name='config.yaml')
@flow(name='train_flow')
def predict(config):
    def prepare_for_inference(df: pd.DataFrame, artifacts) -> pd.DataFrame:
        ohe, schema, most_recent_vals = artifacts
        df = extract_features(df, inference=True)
        df = df.rename(columns={'value': 'lag'})
        df, _ = encode_categorical(df, ohe=ohe, fit=False)
        df[['rolling_mean', 'rolling_std']] = most_recent_vals
        X_recent = df[schema]
        return X_recent

    TRACKING_URI = 'sqlite:///' + utils.get_original_cwd() + '/mlflow.db'
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(config.mlflow.experiment_name)
    
    model_name = config.mlflow.model_name + '-reg'
    
    stage = 'Production'
    model_uri=f'models:/{model_name}/{stage}'

    model = mlflow.pyfunc.load_model(
        model_uri=model_uri
    )

    best_run_id = model.metadata.run_id
    best_run_uri = 'runs://' + best_run_id + '/afts.bin'
    
    local_path = mlflow.artifacts.download_artifacts(run_id=best_run_id)
    
    with open(local_path + '/afts.bin', 'rb') as f_in:
        artifacts = pickle.load(f_in)
    
    input_schema = ['period', 'timezone', 'value']
    data_inference = read_from_db(**config.data.conn_params, schema=input_schema)
    df_inference = data_inference.tail(1)
    
    X_recent = prepare_for_inference(df_inference, artifacts)

    y_pred = model.predict(X_recent)
    print('Holy Shit Preds:', y_pred)
    return y_pred

if __name__ == "__main__":
    predict()