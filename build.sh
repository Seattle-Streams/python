# Installs necessary dependencies and zips them with integration code
function package () {
    cd lambda/$1
    rm -rf dependencies
    rm -f Integration.zip
    mkdir -p dependencies

    pip3 install -r requirements.txt -t ./dependencies

    cd dependencies
    zip -r9 "./../Integration.zip" .
    cd -
    zip -g Integration.zip Integration.py
}
    
# Uploads lambda zip to S3 and updates lambda function code
function deploy () {
    echo "--------------------------------------------------"
    echo "   Uploading latest lambda function build to S3"
    echo "--------------------------------------------------"

    aws s3 cp Integration.zip s3://process-messages-builds/$2/
    
    echo "-------------------------------------------"
    echo "   Pointing lambda function to new build"
    echo "-------------------------------------------"

    aws lambda update-function-code --function-name $1 \
    --s3-bucket process-messages-builds \
    --s3-key $2/Integration.zip \
    --region us-west-2

    cd ../..
}

# If there are changes to Integrations or dependencies, we need to build
if ! git diff --name-only $GIT_PREVIOUS_COMMIT $GIT_COMMIT | grep -i 'Integration\|requirements' > lambdaChanges
then
  echo "No changes... skipping build"    
else

    build_twilio=0
    build_youtube=0
    while read -r line;
    do
        if [ "${line#*/}" == 'twilio/Integration.py' ] || [ "${line#*/}" == 'twilio/requirements.txt' ];
        then
            build_twilio=1
        fi
        if [ "${line#*/}" == 'youtube/Integration.py' ] || [ "${line#*/}" == 'youtube/requirements.txt' ];
        then
            build_youtube=1
        fi
    done < lambdaChanges

    if [ $build_twilio -eq 1 ];
    then
        package twilio
        deploy twilio_lambda twilio
    fi

    if [ $build_youtube -eq 1 ];
    then
        package youtube
        deploy youtube_lambda youtube
    fi
fi
