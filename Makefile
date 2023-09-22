include .env
export

IMAGES = $(LAMBDA_IMAGE_NAME)

AWS_SERVER = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com

login:
	aws ecr get-login-password --region $(AWS_DEFAULT_REGION) --profile $(AWS_PROFILE) | \
	docker login --username AWS --password-stdin $(AWS_SERVER)

push: login
	for img in $(IMAGES); do \
		docker build \
    		--build-arg AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
    		--build-arg AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
    		--build-arg AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
    		--build-arg API_KEY=$(API_KEY) \
			--build-arg STACK_NAME=$(STACK_NAME) \
    		--build-arg DB_NAME=$(DB_NAME) \
    		--build-arg DB_USER=$(DB_USER) \
    		--build-arg DB_PASSWORD=$(DB_PASSWORD) \
    		--build-arg DB_PORT=$(DB_PORT) \
    		--build-arg PREFECT_API_KEY=$(PREFECT_API_KEY) \
    		--build-arg PREFECT_WORKSPACE=$(PREFECT_WORKSPACE) \
    		--target $$img -t $$img .; \
		docker tag $$img $(AWS_SERVER)/$(ECR_REPO_NAME):$$img-latest; \
		docker push $(AWS_SERVER)/$(ECR_REPO_NAME):$$img-latest; \
	done

make-stack-params:
	chmod +x make_stack_params.sh
	./make_stack_params.sh

create-stack:
	@bash -c  'source .env && aws cloudformation create-stack \
    --stack-name $(STACK_NAME) \
    --template-body file://template.yaml \
    --parameters file://parameters.json \
    --capabilities CAPABILITY_IAM'

delete-stack:
	@bash -c  'source .env && aws cloudformation delete-stack \
    --stack-name $(STACK_NAME)'

clean:
	rm parameters.json

setup: push make-stack-params create-stack clean
	