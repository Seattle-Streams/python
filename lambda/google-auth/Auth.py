import json
import os
import boto3
from oauth2client import client
from urllib.parse import parse_qs

QUEUE_URL = os.environ['SQS_URL']

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

s3 = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']


CLIENT_SECRET_FILE_PATH = "/tmp/google_client_secret.json"
CLIENT_SECRET_S3_KEY = "google_client_secret.json"


def getCredentials(authCode):
    return client.credentials_from_clientsecrets_and_code(
        CLIENT_SECRET_FILE_PATH,
        SCOPES,
        authCode)

def authorizeUserRecord(credentials, googleAccount):
    # make update call to dynamoDB
    raise NotImplementedError

def AuthorizeGoogleUser(event, context):
    """ 
    AuthorizeGoogleUser exchanges the Google single-use authorization code for 
    user credentials and saves those credentials in the user record corresponding
    to the google email received

    invariant: event field body contains variables:
        googleAccount - the google account email
        authCode
    """
     # parse event into fields

    body = event["body"]
    authCode = body["auth_code"]
    googleAccount = body["google_account"]

    # AUTH_CODE = ""
    # Remember to verify authenticity of auth code!
    # https://developers.google.com/identity/sign-in/web/backend-auth
    # use verify_oauth2_token

    # Exchange auth code for access token, refresh token, and ID token

    # TODO: figure out if we can get the account name from the credentials directly
    
    try:
        credentials = getCredentials(authCode)
    except FileNotFoundError:
        # handle error where file does not exist
        s3.download_file(BUCKET_NAME, CLIENT_SECRET_S3_KEY, CLIENT_SECRET_FILE_PATH)

        credentials = getCredentials(authCode)
    # store credentials in database

    authorizeUserRecord(credentials, googleAccount)