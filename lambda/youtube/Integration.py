# v1.11
# TODO: Determine whether we should be using oauth2client (deprecated) or a different library

import os
import httplib2
import boto3

from boto3.dynamodb.conditions import Attr

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import googleapiclient.errors

SCOPES = [
    "email",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
# CLIENT_SECRET_FILE = "client_secret.json"
# CREDENTIAL_FILE = "credentials.json"
# AUTH_CODE = ""
# Remember to verify authenticity of auth code!
# https://developers.google.com/identity/sign-in/web/backend-auth
# use verify_oauth2_token

# MESSAGE = "Hello World!!"

# s3 = boto3.client('s3')
# BUCKET_NAME = os.environ['BUCKET_NAME']


dynamoDB = None
table = None

# getLiveChatID gets the liveChatID of the currently streaming broadcast
def getLiveChatID(youtubeObject) -> str:
    request = youtubeObject.liveBroadcasts().list(
        part=
        "snippet",  # available: snippet, status broadcastContent (spelling?)
        broadcastType="all",
        mine=True  # only the broadcasts corresponding to authenticated user
    )
    response = request.execute()
    # TODO: sort this list
    items = response['items']
    if len(items) is 0:
        raise ValueError('youtubeObject is not authenticated to a user with any broadcasts')
    currentSnippet = items[0]['snippet']

    try:
        liveChatID = currentSnippet['liveChatId']
    except KeyError:
        raise ValueError('youtubeObject is not authenticated to a user with currently streaming broadcast')
    return liveChatID


# postMessage inserts the specified message into the livechat corresponding with the given liveChatID
def postMessage(youtubeObject, liveChatID, message) -> str:
    request = youtubeObject.liveChatMessages().insert(
        part="snippet",
        body={
            "snippet": {
                "liveChatId": liveChatID,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": message
                }
            }
        })
    response = request.execute()

    return response

def scanDynamoDBTable(tableName, filterKey=None, filterValue=None):
    """
    Perform a scan operation on table.
    Can specify filter_key (col name) and its value to be filtered.
    This gets all pages of results. Returns list of items.
    """
    
    global dynamoDB
    global table
    
    if dynamoDB is None:
        # TODO: turn paramaters into environment variables and call from OS
        # removed "endpoint_url param"
        dynamoDB = boto3.resource('dynamodb', region_name='us-west-2')
    if table is None:
        table = dynamoDB.Table(tableName)

    if filterKey and filterValue:
        print('filterKey: ' + filterKey)
        print('filterValue: ' + filterValue)
        filteringExp = Attr(filterKey).eq(filterValue)
        response = table.scan(FilterExpression=filteringExp)
    else:
        response = table.scan()
    # DEBUG
    print('response: ' + str(response))
    items = response['Items']
    while True:
        if response.get('LastEvaluatedKey'):
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items += response['Items']
        else:
            break

    return items


# for now, gets credentials if they exist, or breaks
def getStoredCredentials(number):

    # pull credentials from S3
    # local_file_name = "/tmp/" + CREDENTIAL_FILE
    # s3.download_file(BUCKET_NAME, CREDENTIAL_FILE, local_file_name)

    #store = Storage(local_file_name)

    #credentials = store.locked_get()
    # if not credentials or credentials.invalid:

    # Storage object  class:
    # https://oauth2client.readthedocs.io/en/latest/_modules/oauth2client/file.html#Storage
    # Set store with credentials.set_store(store):
    # https://oauth2client.readthedocs.io/en/latest/_modules/oauth2client/client.html#OAuth2Credentials.set_store

    # note: authcode is currently set
    # Exchange auth code for access token, refresh token, and ID token
    # credentials = client.credentials_from_clientsecrets_and_code(
    #     CLIENT_SECRET_FILE,
    #     SCOPES,
    #     AUTH_CODE)
    # store.locked_put(credentials)

    # unclear what the value of this line is
    # credentials.set_store(store)

    # scan table for ReceivingNumber == number

    # should be a single row
    scannedRows = scanDynamoDBTable('user', 'ReceivingNumber', number)
    
    try:
        firstRow = scannedRows[0]
    except IndexError:
        raise ValueError('scannedRows: ' + str(scannedRows) + 'There are no rows')
    try:
        stringCredentials = firstRow['Credentials']['S']
    except KeyError:
        raise ValueError('Credentials do not exist for this record')

    # TODO: error handling here
    credentials = client.Credentials.new_from_json(stringCredentials) 

    return credentials


# auth authenticates with the provided client secrets file, scope, and authorization code
# returns youtube client object
def auth(number):

    # TODO: implement in api gateway
    # (Receive auth_code by HTTPS POST)

    # TODO: implement in api gateway
    # If this request does not have `X-Requested-With` header, this could be a CSRF
    # if not request.headers.get('X-Requested-With'):
    #     abort(403)

    # TODO: Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    credentials = getStoredCredentials(number)

    # changes methods of http object to add appropriate auth headers
    httpAuth = credentials.authorize(httplib2.Http())

    # TODO: store refreshed credentials in dynamodb
    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
        httpAuth = credentials.authorize(httplib2.Http())

    youtubeService = discovery.build(
        API_SERVICE_NAME, API_VERSION, http=httpAuth, cache_discovery=False)

    return youtubeService

# ProcessMessage receives an event from SQS and 
# Note: SQS message batch size is currently 1
# TODO: Enable this to work with a larger batch size for multiple youtube accounts
def ProcessMessage(event, context):
    messages = event['Records']
    # TODO: handle attributes better. i.e. post messages in order and sort by livechatID 
    for rawMessage in messages:
        message = rawMessage['body']
        
        try:
            if rawMessage['messageAttributes'] is not None:
                try:
                    number = rawMessage.get('messageAttributes').get('receiving-number').get('stringValue')
                    print('number: ' + number)
                    
                except KeyError:
                    raise ValueError("Error: messageAttributes missing or have incorrect receiving-number field")
        except KeyError:
            raise ValueError('Error: missing messageAttributes field in message')
       
        if number is None:
            print('could not find receiving-number on message')
            continue
        try:
            youtubeObject = auth(number)
        except ValueError as e:
            print('ValueError: ' + str(e) + 'could not match given number to an account')
            continue
        try:
            liveChatID = getLiveChatID(youtubeObject)
        except ValueError:
            # TODO: decide what to do with messages sent to accounts without currently running livestreams.
            print('could not find liveChatId')
            continue
        response = postMessage(youtubeObject, liveChatID, message)
        print('Logging YouTube response', response)
    return {'statusCode': 200}