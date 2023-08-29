# !/usr/bin/env python
# coding: utf-8
import os
import mlflow
import mlflow.pyfunc
from mlflow.exceptions import MlflowException
from hydra import initialize, compose
import pickle

# @flow(name='make_prediction')
def predict(config, model_name):
    stage = "Production"
    print("Stage:", stage)
    model_uri = f"models:/{model_name}/{stage}"
    print("Model URI:", model_uri)
    model_uri = "s3://electricity-demand-bucket/mlruns/2e2bcde262ad4520b8da93ba22265361/artifacts/xgb_best"
    model = mlflow.pyfunc.load_model(model_uri=model_uri)

    best_run_id = model.metadata.run_id

    local_path = mlflow.artifacts.download_artifacts(run_id=best_run_id)
    print(local_path)
    with open(local_path + '/afts.bin', 'rb') as f_in:
        artifacts = pickle.load(f_in)
    
    last_day_vals = artifacts[2]
    y_pred = model.predict(last_day_vals)
    return y_pred[0]
    
def lambda_handler(event, context):
    # Initialize Hydra
    initialize(version_base=None, config_path="conf/", job_name="lambda_job")
    config = compose(config_name="config.yaml")
    
    dbname = config.data.conn_params.dbname
    user = config.data.conn_params.user
    password = config.data.conn_params.password
    host = config.data.conn_params.host
    port = config.data.conn_params.port
    print("Using:\n", dbname)
    TRACKING_URI = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    print("Setting URI...", TRACKING_URI)
    mlflow.set_tracking_uri(TRACKING_URI)
    
    # # mlflow.set_experiment(config.mlflow.experiment_name)
    model_name = config.mlflow.model_name + '-reg'
    
    try: # Call the prediction function
        print("Current directory before:", os.getcwd())
        os.chdir("/tmp")
        print("Current directory after:", os.getcwd())
        pred = predict(config=config, model_name=model_name)
        # Return the result as JSON
        result = {'prediction': float(pred)}
        print(result)
        return result
    
    except Exception as e:
        return {"Exception": str(e)}

if __name__ == "__main__":
    lambda_handler()