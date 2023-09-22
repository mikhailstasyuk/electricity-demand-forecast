#!/bin/bash

# Load env variables
source .env

# Install Miniconda
apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda

# Install AWS CLI
apt-get update && apt-get install -y unzip
apt-get install -y curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Clean
rm -r aws
rm awscliv2.zip

# Create conda venv
conda create -n venv
conda init && . ~/.bashrc && conda activate venv