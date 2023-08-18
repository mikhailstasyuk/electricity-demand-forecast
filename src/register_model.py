#!/usr/bin/env python
# coding: utf-8

import mlflow
from mlflow import MlflowClient
from mlflow.entities import ViewType
import hydra
from hydra import utils
from pprint import pprint

def search_best(config):
    TRACKING_URI = 'sqlite:///' + utils.get_original_cwd() + '/mlflow.db'
    mlflow.set_tracking_uri(TRACKING_URI)
    
    experiment = mlflow.get_experiment_by_name(config.mlflow.experiment_name)

    run = MlflowClient().search_runs(
        experiment_ids=experiment.experiment_id,
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.mae_test ASC"],
    )[0]
    print(run.info.artifact_uri)
    return run

def check_if_registered(model_name, run_id):
    client = MlflowClient()
    for mv in client.search_model_versions(f"name='{model_name}'"):
        # pprint(dict(mv), indent=4)
        if dict(mv)['run_id'] == run_id:
            return True
    return False

def register_model(run, model_name):
    run_id = run.info.run_id
    model_uri = 'runs:/' + run_id + '/xgb_best'
    is_registered = check_if_registered(model_name, run_id)
    if not is_registered:
        result = mlflow.register_model(
        model_uri, model_name
        )
        print(model_name, result.version)
        promote_to_production(model_name, result.version)
        

def promote_to_production(model_name, model_version):
    client = MlflowClient()
    client.transition_model_version_stage(
        name=model_name, 
        version=model_version,
        stage="Production",
        archive_existing_versions=True
    )

@hydra.main(config_path='conf/', config_name='config.yaml')
def choose_and_register(config):
    run = search_best(config)
    model_name = config.mlflow.model_name + '-reg'
    register_model(run, model_name)

if __name__ == "__main__":
    choose_and_register()