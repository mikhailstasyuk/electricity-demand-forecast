#!/bin/bash

source .env

echo "[
    {
        \"ParameterKey\": \"myBucketName\",
        \"ParameterValue\": \"$S3_BUCKET_NAME\"
    },
    {
        \"ParameterKey\": \"KeyPairName\",
        \"ParameterValue\": \"$KEY_PAIR_NAME\"
    },
    {
        \"ParameterKey\": \"myInstanceType\",
        \"ParameterValue\": \"$EC2_INSTANCE_TYPE\"
    },
    {
        \"ParameterKey\": \"myImageId\",
        \"ParameterValue\": \"$EC2_IMAGE_ID\"
    },
    {
        \"ParameterKey\": \"dbMasterUsername\",
        \"ParameterValue\": \"$DB_USER\"
    },
    {
        \"ParameterKey\": \"dbMasterUserPassword\",
        \"ParameterValue\": \"$DB_PASSWORD\"
    },
    {
        \"ParameterKey\": \"myImageUri\",
        \"ParameterValue\": \"$LAMBDA_IMAGE_URI\"
    },
    {
        \"ParameterKey\": \"dbMasterName\",
        \"ParameterValue\": \"$DB_NAME\"
    },         
    {
        \"ParameterKey\": \"dbMasterUsername\",
        \"ParameterValue\": \"$DB_USER\"
    },
    {
        \"ParameterKey\": \"dbMasterUserPassword\",
        \"ParameterValue\": \"$DB_PASSWORD\"
    },    
    {
        \"ParameterKey\": \"dbMasterPort\",
        \"ParameterValue\": \"$DB_PORT\"
    }     
]" > parameters.json
