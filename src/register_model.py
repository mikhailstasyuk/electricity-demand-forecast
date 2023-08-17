#!/usr/bin/env python
# coding: utf-8

import mlflow
from mlflow import MlflowClient
from mlflow.entities import ViewType
import hydra
from hydra import utils

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

def register_model(run, model_name):
    model_uri = 'runs:/' + run.info.run_id + '/xgb_best'
    print('model path is', model_uri)
    result = mlflow.register_model(
    model_uri, model_name
    )

def choose_and_register(config):
    run = search_best(config)
    model_name = config.mlflow.model_name + '-reg'
    register_model(run, model_name)

if __name__ == "__main__":
    choose_and_register()