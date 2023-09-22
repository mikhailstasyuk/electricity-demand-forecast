#!/bin/bash

# Update repo
git pull https://github.com/mikhailstasyuk/electricity-demand-forecast

# Load env variables
source .env

# Add db endpoint to env variables list
DB_HOST=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`RDSInstanceEndpoint`].OutputValue' --output text)
export DB_HOST
echo $DB_HOST

# Update dependencies
pipenv update
pipenv run prefect cloud login --key $PREFECT_API_KEY --workspace $PREFECT_WORKSPACE

# Run training pipeline
pipenv run python db_store.py
pipenv run python main_flow.py