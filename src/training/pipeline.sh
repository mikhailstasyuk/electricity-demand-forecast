#!/bin/bash

# Update repo
git pull https://github.com/mikhailstasyuk/electricity-demand-forecast

# Add db endpoint to env variables list
bash get_db_host.sh

# Run training pipeline
python db_store.py
python main_flow.py