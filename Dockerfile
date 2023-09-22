# Lambda stage
FROM public.ecr.aws/lambda/python:3.10 AS lambda-image

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION
ARG API_KEY
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_PORT

ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
    API_KEY=$API_KEY \
    DB_NAME=$DB_NAME \
    DB_USER=$DB_USER \
    DB_PASSWORD=$DB_PASSWORD \
    DB_PORT=$DB_PORT 

WORKDIR ${LAMBDA_TASK_ROOT}

COPY ./src/prediction/app.py ${LAMBDA_TASK_ROOT}
COPY ./src/conf/ ${LAMBDA_TASK_ROOT}/conf
COPY ./src/prediction/Pipfile ${LAMBDA_TASK_ROOT}
COPY ./src/prediction/Pipfile.lock ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install pipenv && pipenv install --system --deploy

CMD [ "app.lambda_handler" ]

# # Python stage
# FROM python:3.10-slim AS ec2-image

# ARG AWS_ACCESS_KEY_ID
# ARG AWS_SECRET_ACCESS_KEY
# ARG AWS_DEFAULT_REGION
# ARG API_KEY
# ARG STACK_NAME
# ARG DB_NAME
# ARG DB_USER
# ARG DB_PASSWORD
# ARG DB_PORT
# ARG PREFECT_API_KEY
# ARG PREFECT_WORKSPACE

# ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
#     AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
#     AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
#     API_KEY=$API_KEY \
#     STACK_NAME=$STACK_NAME \
#     DB_NAME=$DB_NAME \
#     DB_USER=$DB_USER \
#     DB_PASSWORD=$DB_PASSWORD \
#     DB_PORT=$DB_PORT \
#     PREFECT_API_KEY=$PREFECT_API_KEY \
#     PREFECT_WORKSPACE=$PREFECT_WORKSPACE

# WORKDIR /app
# COPY ./src/training/data_preprocessing.py .
# COPY ./src/training/db_store.py .
# COPY ./src/training/hp_optimization.py .
# COPY ./src/training/main_flow.py .
# COPY ./src/training/register_model.py .
# COPY ./src/training/train.py .
# COPY ./src/training/Pipfile .
# COPY ./src/training/Pipfile.lock .
# COPY ./src/conf ../conf

# # Install Miniconda
# RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
# RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh -O ~/miniconda.sh
# RUN bash ~/miniconda.sh -b -p $HOME/miniconda

# ENV PATH="/root/miniconda/bin:${PATH}"

# RUN apt-get update && apt-get install -y unzip
# RUN apt-get install -y curl
# RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
# RUN unzip awscliv2.zip
# RUN ./aws/install
# RUN conda create -n venv
# RUN conda init && . ~/.bashrc && conda activate venv

# RUN pip install --upgrade pip
# RUN pip install pipenv && pipenv install

# COPY ./src/training/get_db_host.sh .
# RUN bash get_db_host.sh