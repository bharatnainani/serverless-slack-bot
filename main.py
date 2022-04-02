import boto3
import json
import gzip
import os
import base64
from botocore.vendored import requests
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import logging
import slack_sdk
import re
from slack_sdk.webhook import WebhookClient

logger=logging.getLogger()
logger.setLevel(logging.INFO)
def lambda_handler(event,context):

    ssm = boto3.client('ssm')
#define the function
    encoded_zipped_data = event['awslogs']['data']
    zipped_data = base64.b64decode(encoded_zipped_data)
    log = gzip.decompress(zipped_data).decode("utf-8")
    data = json.loads(log)
    loggroup = data['logGroup']
    account_id = data['owner']
    string_pattern = os.environ["FILTER_PATTERN"]
    logstream = data['logStream']
    message = data['logEvents']
    #Create format for slack message and make request to the API

    webhook_name = os.environ["SLACK_WEBHOOK_URL"]
    webhook_url = ssm.get_parameter(Name=webhook_name, WithDecryption=True)
    webhook = WebhookClient(webhook_url['Parameter']['Value'])
    try:
        for logmessage in message:
            log = logmessage['message']
            string = re.sub('[^A-Za-z0-9]+', ' ', log)
            response = webhook.send(
                text="fallback",
                blocks=[
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": "botServerless",
                            "emoji": True
                        },
                        "image_url": "https://slack-bot-images.s3.eu-west-2.amazonaws.com/SlackBot.jpeg",
                        "alt_text": "marg"
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "CloudWatch Log Errors :cloudwatchlogo:",
                            "emoji": True
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f'*stringPattern:*\n{string_pattern}'
                            },
                            {
                                "type": "mrkdwn",
                                "text": f':aws:*accountId:*\n{account_id}'
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f'*:cloudwatch:logGroup:*\n{loggroup}'
                            },
                            {
                                "type": "mrkdwn",
                                "text": f'*logStream:*\n{logstream}'
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": 'Error Message'
                                },
                                "style": "danger"
                            }
                        ]
                    },
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_preformatted",
                                "elements": [{
                                    "type": "text",
                                    "text": json.dumps(string)
                                }]
                            },
                    
                        ]
                    }
                ]
            )
    except Exception as error:
        logger.error("An error occurred while sending a cloudwatch logs to slack")
    