#!/usr/bin/env python
# coding: utf-8
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from hydra import initialize, compose
import pickle

def get_prod_uri(model_name):
    # Initialize the MLflow client
    client = MlflowClient()

    # Get a list of all registered models
    registered_models = client.get_latest_versions(name=model_name, 
                                                   stages=["Production"])

    # Find the model with "Production" stage
    production_model_uri = None
    for reg_model in registered_models:
        # Get the latest version of the model in "Production" stage
        latest_prod_version = client.get_latest_versions(reg_model.name, stages=["Production"])
        
        if latest_prod_version:
            # Construct the full URI of the model in the S3 bucket
            production_model_uri = latest_prod_version[0].source
            break

    if production_model_uri:
        print(f"The URI of the model in 'Production' stage is: {production_model_uri}")
        return production_model_uri
    else:
        print("No model found in 'Production' stage.")

# @flow(name='make_prediction')
def predict(config, model_uri):
    try:
        model = mlflow.pyfunc.load_model(
            model_uri=model_uri
        )

    except Exception as e:
        raise Exception(str(e) + f'model URI:{model_uri}')

    best_run_id = model.metadata.run_id

    local_path = mlflow.artifacts.download_artifacts(run_id=best_run_id)
    with open(local_path + '/afts.bin', 'rb') as f_in:
        artifacts = pickle.load(f_in)
    
    last_day_vals = artifacts[2]
    y_pred = model.predict(last_day_vals)
    return y_pred[0]

def lambda_handler(event, context):
    
    # Initialize Hydra
    initialize(version_base=None, config_path="conf/", job_name="lambda_job")
    config = compose(config_name="config.yaml")
    
    TRACKING_URI = 'sqlite:///mlflow.db'
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(config.mlflow.experiment_name)
    model_name = config.mlflow.model_name + '-reg'
    
    try: # Call the prediction function
        model_uri = get_prod_uri(model_name)
        pred = predict(config=config, model_uri=model_uri)
        # Return the result as JSON
        result = {'prediction': float(pred)}
        return result
    
    except Exception as e:
        return {"Exception": str(e)}

if __name__ == "__main__":
    lambda_handler()