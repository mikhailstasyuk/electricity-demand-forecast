# !/usr/bin/env python
# coding: utf-8
import os
import mlflow
import mlflow.pyfunc
from mlflow.exceptions import MlflowException
from hydra import initialize, compose
import pickle

def predict(model_name):
    stage = "Production"
    model_uri = f"models:/{model_name}/{stage}"
    print("Model URI:", model_uri)
    model = mlflow.pyfunc.load_model(model_uri=model_uri)

    best_run_id = model.metadata.run_id

    local_path = mlflow.artifacts.download_artifacts(run_id=best_run_id)
    print(local_path)
    with open(local_path + '/afts.bin', 'rb') as f_in:
        artifacts = pickle.load(f_in)
    
    last_day_vals = artifacts[2]
    y_pred = model.predict(last_day_vals)
    return y_pred[0]

def make_prediction():    
    config_path = 'conf/'
    initialize(version_base=None, config_path=config_path, job_name="lambda_job")
    config = compose(config_name="config.yaml")
    
    dbname = config.data.conn_params.dbname
    user = config.data.conn_params.user
    password = config.data.conn_params.password
    host = config.data.conn_params.host
    port = config.data.conn_params.port
    
    TRACKING_URI = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    mlflow.set_tracking_uri(TRACKING_URI)
    
    model_name = config.mlflow.model_name + '-reg'
    
    try: 
        os.chdir("/tmp")
        pred = predict(model_name=model_name)

        # Return the result as JSON
        result = {'prediction': float(pred)}
        print(result)
        return result
    
    except Exception as e:
        return {"Exception": str(e)}

def lambda_handler(event, context):
    make_prediction()

if __name__ == "__main__":
    lambda_handler()