#!/bin/bash

# Install Miniconda
sudo apt-get update && sudo apt-get install -y wget && rm -rf /var/lib/apt/lists/*
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
source ~/miniconda/bin/activate
conda init bash

# Install AWS CLI
sudo apt-get update && sudo apt-get install -y unzip
sudo apt-get install -y curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Clean
rm -r aws
rm awscliv2.zip

conda create -n venv && conda activate venv
source ~/.bashrc 

# Install dependencies
pip install pipenv
pipenv install