#!/bin/bash

DB_HOST=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`RDSInstanceEndpoint`].OutputValue' --output text)
export DB_HOST

pipenv run prefect cloud login --key $PREFECT_API_KEY --workspace $PREFECT_WORKSPACE

pipenv run python db_store.py
pipenv run python main_flow.py