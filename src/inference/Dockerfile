FROM public.ecr.aws/lambda/python:3.10
# This is an inference only container
WORKDIR ${LAMBDA_TASK_ROOT}

COPY inference/app.py ${LAMBDA_TASK_ROOT}
COPY training/mlflow.db ${LAMBDA_TASK_ROOT}
COPY conf/config.yaml ${LAMBDA_TASK_ROOT}

COPY .env ${LAMBDA_TASK_ROOT}
COPY inference/Pipfile ${LAMBDA_TASK_ROOT}
COPY inference/Pipfile.lock ${LAMBDA_TASK_ROOT}

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION

ENV AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY
ENV AWS_DEFAULT_REGION $AWS_DEFAULT_REGION

RUN pip install --upgrade pip
RUN pip install pipenv && pipenv install --system --deploy


CMD [ "app.lambda_handler" ]