import json
import os
import boto3
from oauth2client import client
from oauth2client import clientsecrets
from urllib.parse import parse_qs

CLIENT_SECRET_FILE_PATH = "/tmp/google_client_secret.json"
CLIENT_SECRET_S3_KEY = "google_client_secret.json"
SCOPES = [
    "email",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]
BUCKET_NAME = os.environ['BUCKET_NAME']

# Defined as None here to take advantage of reusing instantiated variables
s3 = None
dynamoDB = None
table = None


def createCredentials(authCode):
    return client.credentials_from_clientsecrets_and_code(
            CLIENT_SECRET_FILE_PATH,
            SCOPES,
            authCode)

def getCredentials(authCode):  
    global s3

    try:
        credentials = createCredentials(authCode)
    # handle error where file does not exist
    except clientsecrets.InvalidClientSecretsError:
        try:
            s3.download_file(BUCKET_NAME, CLIENT_SECRET_S3_KEY, CLIENT_SECRET_FILE_PATH)
        except AttributeError:
            s3 = boto3.client('s3')
            s3.download_file(BUCKET_NAME, CLIENT_SECRET_S3_KEY, CLIENT_SECRET_FILE_PATH)

        credentials = createCredentials(authCode)
    except client.FlowExchangeError:
        raise ValueError('authCode: ' + authCode + ' is invalid')
    return credentials

def updateItem(signupEmail, credentialsInJSON):
    global table
    
    response = table.update_item(
            Key={
                'Email': signupEmail
            },
            UpdateExpression='SET Credentials = :c',
            ExpressionAttributeValues={
                ':c': credentialsInJSON
            }
        )
    return response

def authorizeUserRecord(credentials, signupEmail):
    global dynamoDB
    global table
    # make update call to 
    
    # Doubtful we need the google account at all
    """ try:
        idToken = credentials['id_token']
    except KeyError:
        raise ValueError("credentials object does not contain id_token")
    try:
        googleAccount = idToken['email']
    except KeyError:
        raise ValueError("id_token field in credentials does not include email")
 """
    credentialsInJSON = credentials.to_json()

    # store entire credentials string in dynamo db
    if dynamoDB is None:
        # TODO: turn paramaters into environment variables and call from OS
        dynamoDB = boto3.resource('dynamodb', region_name='us-west-2')

    if table is None:
        table = dynamoDB.Table('user')


    # TODO: Fix issue here - email is key but is not received by this lambda

    try:
        response = updateItem(signupEmail, credentialsInJSON)
    except AttributeError:
        try: 
            table = dynamoDB.Table('user')
        except AttributeError:
            dynamoDB = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamoDB.Table('user')
        response = updateItem(signupEmail, credentialsInJSON)

    return response
    

def AuthorizeGoogleUser(event, context):
    """ 
    AuthorizeGoogleUser exchanges the Google single-use authorization code for 
    user credentials and saves those credentials in the user record corresponding
    to the email received

    invariant: event field body contains variables:
        authCode - the single-use google authorization code
        email - the email account the user signed up with
    """
     # parse event into fields

    bodyString = event['body']
    cleanBody = bodyString.replace('\\n', '').replace('\\t', '').replace('\\r', '').replace('\\', '').replace('null', '"null"').replace('false', '"false"').replace('true', '"true"').replace('"{', '{').replace('}"', '}')
    body = json.loads(cleanBody)['body']

    try:
        authCode = body['authCode']
    except KeyError:
        raise ValueError("event: " + json.dumps(event) + "cleanBody: "  + cleanBody + " Event body must contain field authCode")
    
    try:
        signupEmail = body['email']
    except KeyError:
        raise ValueError("Event body must contain field email")

    # AUTH_CODE = ""
    # TODO: Remember to verify authenticity of auth code!
    # https://developers.google.com/identity/sign-in/web/backend-auth
    # use verify_oauth2_token

    # Exchange auth code for access token, refresh token, and ID token

    credentials = getCredentials(authCode)

    # get email:https://developers.google.com/identity/sign-in/web/server-side-flow#step_7_exchange_the_authorization_code_for_an_access_token
    # NOTE: manually inspecting the credentials.json file reveals the email is available as a field nested under "id_token"

    # store credentials in database
    response = authorizeUserRecord(credentials, signupEmail)
    print('Logging DynamoDB response: ', response)