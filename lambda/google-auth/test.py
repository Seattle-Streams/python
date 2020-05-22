from urllib.parse import parse_qs
import json

event = """{
    "resource": "/auth",
    "path": "/auth",
    "httpMethod": "POST",
    "headers": {
        "Content-Type": " application/json"
    },
    "multiValueHeaders": {
        "Content-Type": [
            " application/json"
        ]
    },
    "queryStringParameters": null,
    "multiValueQueryStringParameters": null,
    "pathParameters": null,
    "stageVariables": null,
    "requestContext": {
        "resourceId": "ixje8y",
        "resourcePath": "/auth",
        "httpMethod": "POST",
        "extendedRequestId": "M7WXhEaNPHcFiQw=",
        "requestTime": "22/May/2020:09:39:21 +0000",
        "path": "/auth",
        "accountId": "950143623787",
        "protocol": "HTTP/1.1",
        "stage": "test-invoke-stage",
        "domainPrefix": "testPrefix",
        "requestTimeEpoch": 1590140361649,
        "requestId": "6b719036-b7d5-4d9a-9261-d589069213a3",
        "identity": {
            "cognitoIdentityPoolId": null,
            "cognitoIdentityId": null,
            "apiKey": "test-invoke-api-key",
            "principalOrgId": null,
            "cognitoAuthenticationType": null,
            "userArn": "arn:aws:iam::950143623787:root",
            "apiKeyId": "test-invoke-api-key-id",
            "userAgent": "aws-internal/3 aws-sdk-java/1.11.772 Linux/4.9.184-0.1.ac.235.83.329.metal1.x86_64 OpenJDK_64-Bit_Server_VM/25.252-b09 java/1.8.0_252 vendor/Oracle_Corporation",
            "accountId": "950143623787",
            "caller": "950143623787",
            "sourceIp": "test-invoke-source-ip",
            "accessKey": "ASIA52OHZEJVVTMGJAHW",
            "cognitoAuthenticationProvider": null,
            "user": "950143623787"
        },
        "domainName": "testPrefix.testDomainName",
        "apiId": "dqawrk0ofc"
    },
    "body": "{\n\t\"email\": \"aiones@uw.edu\",\n\t\"authCode\": \"test code\"\n}",
    "isBase64Encoded": false
}"""

def main():
    #print(json.dumps(parse_qs(parse_qs(event['body'])['authCode'])))
    
    cleanEvent = event.replace('\\n', '').replace('\\t', '').replace('\\', '').replace('null', '"null"').replace('false', '"false"').replace('true', '"true"').replace('"{', '{').replace('}"', '}')
    print(cleanEvent)
    eventObj = json.loads(cleanEvent)
    print(eventObj)
    body = eventObj['body']
    #bodyObj = parse_qs(body)
    authCode = body['authCode']

    print(authCode)



main()