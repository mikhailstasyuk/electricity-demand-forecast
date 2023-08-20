FROM public.ecr.aws/lambda/python:3.9

# Copy function code
COPY src /src
COPY src/app.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt /

RUN pip install -r requirements.txt

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.handler" ]