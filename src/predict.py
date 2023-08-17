#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import mlflow
from data_preprocessing import read_from_db
from data_preprocessing import extract_features, encode_categorical
import hydra
from hydra import utils

@hydra.main(config_path='conf', config_name='config.yaml')
def predict(config, X, artifacts):
    def prepare_for_inference(df: pd.DataFrame) -> pd.DataFrame:
        ohe, schema, most_recent_vals = artifacts
        df = extract_features(df, inference=True)
        df = df.rename(columns={'value': 'lag'})
        df, _ = encode_categorical(df, ohe=ohe, fit=False)
        df[['rolling_mean', 'rolling_std']] = most_recent_vals
        X_recent = df[schema]
        return X_recent

    data_inference = read_from_db(config.data.conn_params)
    df_inference = data_inference.tail(1)
    
    X_recent = prepare_for_inference(df_inference, artifacts)

    TRACKING_URI = 'sqlite:///' + utils.get_original_cwd() + '/mlflow.db'
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(config.mlflow.experiment_name)

    logged_model = 'runs:/e7cc03f29ef74315829159e332835a59/xgb_best'

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)
    
    y_pred = loaded_model.predict(X_recent)
    return y_pred

if __name__ == "__main__":
    predict()