import re
import boto3
import json
import logging
import time
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the CloudWatch Logs client
logs_client = boto3.client('logs')

# Initialize the S3 client
s3_client = boto3.client('s3')

log_group_name = 'S3_cloudwatch_loggroup'

ITEM_REGEX = r'^.*\/init_scripts\/.*\.log$'

MAX_BATCH_SIZE = 262144 # 256 KB (in bytes)

def lambda_handler(event, context):
    logger.info(event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    s3_object = event['Records'][0]['s3']['object']['key']
    logger.info(s3_object)
    regex = re.compile(ITEM_REGEX)
    is_new_file_matching_regex= re.match(regex, s3_object)
    # logger.info("Is " + s3_object + " is matching ::" + is_new_file_matching_regex)
    if(is_new_file_matching_regex):
        logStreamName='log-stream'
        try:
            # Create the CloudWatch Logs stream
            logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=logStreamName)
        except ClientError as e:
        # Define the CloudWatch Logs group and log stream name
            logger.info(e)
           
        s3_object = s3_client.get_object(Bucket=bucket, Key=s3_object)
        file_content = s3_object['Body'].read().decode('utf-8')
        log_events = []

        # Get the log message and split it into chunks
        for i in range(0, len(file_content), MAX_BATCH_SIZE):
            log_events.append({
                'timestamp': int(round(time.time() * 1000)),
                'message': file_content[i:i+MAX_BATCH_SIZE]
            })

        #to be removed
        logger.info(file_content)
        response = logs_client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=logStreamName,
            logEvents=log_events)

        # Print the response from the put_log_events API call
        logger.info(response)
       
    else:
        logger.info('No matching file found.')