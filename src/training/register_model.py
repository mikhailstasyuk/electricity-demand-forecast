#!/usr/bin/env python
# coding: utf-8

import mlflow
from mlflow import MlflowClient
from mlflow.entities import ViewType
from pprint import pprint
from prefect import flow, task

@task(name="find best model", retries=5, retry_delay_seconds=5)
def search_best(config):
    dbname = config.data.conn_params.dbname
    user = config.data.conn_params.user
    password = config.data.conn_params.password
    host = config.data.conn_params.host

    TRACKING_URI = f'postgresql://{user}:{password}@{host}/{dbname}'
    mlflow.set_tracking_uri(TRACKING_URI)
    
    experiment = mlflow.get_experiment_by_name(config.mlflow.experiment_name)

    run = MlflowClient().search_runs(
        experiment_ids=experiment.experiment_id,
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.mae_test ASC"],
    )[0]
    return run

def check_if_registered(model_name, run_id):
    client = MlflowClient()
    for mv in client.search_model_versions(f"name='{model_name}'"):
        # pprint(dict(mv), indent=4)
        if dict(mv)['run_id'] == run_id:
            return True
    return False

def promote_to_production(model_name, model_version):
    client = MlflowClient()
    client.transition_model_version_stage(
        name=model_name, 
        version=model_version,
        stage="Production",
        archive_existing_versions=True
    )

def register_model(run, model_name):
    run_id = run.info.run_id
    model_uri = 'runs:/' + run_id + '/xgb_best'
    is_registered = check_if_registered(model_name, run_id)
    if not is_registered:
        result = mlflow.register_model(
        model_uri, model_name
        )
        return result
    return None

@flow(name="register model")
def choose_and_register(config):
    run = search_best(config)
    model_name = config.mlflow.model_name + '-reg'
    result = register_model(run, model_name)
    if result is not None:
        promote_to_production(model_name, result.version)

if __name__ == "__main__":
    choose_and_register()