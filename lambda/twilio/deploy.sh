#!/bin/env bash

echo "Entered the post_build phase..."

# Options and their defaults
APP=${APP:-twilio}
BUCKET=${BUCKET:-process-messages}
FUNCTION_NAME=${FUNCTION_NAME:-twilio_lambda}
REGION=${REGION:-uw-west-2}

# Parsing through input variables
while [ $# -gt 0 ]; do

   if [ $1 == *"--"* ]; then
        param="${1/--/}"
        declare $param="$2"
   fi

  shift
done

echo "Pushing build to S3"
aws s3 cp ${commitID}.zip s3://$BUCKET/$APP/

echo "Pushing to build to lambda"
aws lambda update-function-code --function-name $FUNCTION_NAME --s3-bucket $BUCKET --s3-key $APP/${commitID}.zip --region $REGION

branch_name=$(git symbolic-ref HEAD 2>/dev/null)
branch_name=${branch_name##refs/heads/}

if [ $branch_name == $branch ]; then
    echo "Publing new lambda function version"
    lambdaVersion=$(aws lambda publish-version --function-name $FUNCTION_NAME --region $REGION | jq -r '.Version')
    aws lambda update-alias --function-name $FUNCTION_NAME --name production --region $REGION --function-version ${lambdaVersion}      
fi
