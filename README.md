## Getting Started

This project forecasts electricity demand using New York data. Follow the steps below to set up and run the project.

### Prerequisites

1. **Install Required Tools**:
   - [Docker](https://docs.docker.com/get-docker/)
   - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
   - [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

2. **Set Up AWS Credentials**:
   - Ensure your AWS credentials are configured using `aws configure`.

3. **Environment Variables**:
   - Create a `.env` file in the project root with the following variables:
     ```env
     AWS_ACCESS_KEY_ID=<your_aws_access_key>
     AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
     AWS_DEFAULT_REGION=<your_aws_region>
     S3_BUCKET_NAME=<your_s3_bucket_name>
     KEY_PAIR_NAME=<your_ec2_key_pair_name>
     EC2_INSTANCE_TYPE=t3.micro
     EC2_IMAGE_ID=<your_ec2_image_id>
     DB_NAME=forecast_db
     DB_USER=admin
     DB_PASSWORD=<your_db_password>
     DB_PORT=5432
     LAMBDA_IMAGE_URI=<your_lambda_image_uri>
     STACK_NAME=electricity-forecast-stack
     ```

### Steps to Run the Project

1. **Build and Push Docker Image**:
   - Run the following command to build and push the Lambda Docker image to AWS ECR:
     ```sh
     make push
     ```

2. **Create CloudFormation Stack**:
   - Generate the stack parameters and create the stack:
     ```sh
     make setup
     ```

3. **Run the Training Pipeline**:
   - SSH into the EC2 instance created by the CloudFormation stack.
   - Clone this repository and navigate to the `src/training` directory.
   - Run the training pipeline:
     ```sh
     ./pipeline.sh
     ```

4. **Make Predictions**:
   - The Lambda function is deployed and ready to make predictions. You can invoke it using the AWS CLI:
     ```sh
     aws lambda invoke --function-name <lambda_function_name> response.json
     ```

### Cleaning Up

To delete the CloudFormation stack and clean up resources:
```sh
make delete-stack
