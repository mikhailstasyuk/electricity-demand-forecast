#!/bin/bash

# Update repo
git pull https://github.com/mikhailstasyuk/electricity-demand-forecast

# Load env variables
source .env

aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_DEFAULT_REGION

# Add db endpoint to env variables list
DB_HOST=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`RDSInstanceEndpoint`].OutputValue' --output text)
export DB_HOST

# Update dependencies
source ~/miniconda/bin/activate
conda init bash
source ~/.bashrc 
#conda activate venv

pipenv install
pipenv run prefect cloud login --key $PREFECT_API_KEY --workspace $PREFECT_WORKSPACE

# Run training pipeline
pipenv run python db_store.py
pipenv run python main_flow.py

pipenv run prefect cloud logout