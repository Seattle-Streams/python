import json
import os
import boto3
from urllib.parse import parse_qs

QUEUE_URL = os.environ['SQS_URL']

sqs = boto3.client('sqs')

# ProcessMessage extracts the SMS message and Twilio receiving phone number
# from the request and sends it to an SQS Queue
def ProcessMessage(event, context):
    try:
        requestJSON = parse_qs(event['body'])
    except KeyError:
        raise ValueError("Event must contain field body")

    try:
        twilioReceivingPhoneNumber = requestJSON['To'][0]
    except KeyError:
        raise ValueError("Request body must contain field To")

    # This is the end-user generated SMS message
    try:
        message = requestJSON['Body'][0]
    except KeyError:
        raise ValueError("Request body must contain field Body")

    queueResponse = sqs.send_message(
        QueueUrl=QUEUE_URL, 
        MessageBody=message, 
        MessageAttributes={
            'receiving-number': {
                'StringValue': '{twilioReceivingPhoneNumber}',
                'DataType': 'String'
            }
        }
    )

    print("Logging Twilio Receiving Number: ", twilioReceivingPhoneNumber)
    print("Logging SMS Message: ", message)
    print("Logging SQS Response: ", queueResponse)

    return {
        "statusCode": 200, 
        "body": "<Response><Message><Body>Message Received!</Body></Message></Response>",
        "headers": {
            'Content-Type': 'text/xml',
        }
    }