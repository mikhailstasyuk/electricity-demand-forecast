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