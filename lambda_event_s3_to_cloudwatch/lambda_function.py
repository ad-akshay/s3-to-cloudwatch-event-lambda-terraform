import re
import boto3
import json
import logging
import time
import os
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the CloudWatch Logs client
logs_client = boto3.client('logs')

# Initialize the S3 client
s3_client = boto3.client('s3')

log_group_name = os.environ['CWLogGroup']

ITEM_REGEX = r'^.*\/init_scripts\/.*\.log$'

MAX_BATCH_SIZE = 260000 # less than 256 KB (in bytes)

def lambda_handler(event, context):
    logger.info(event)
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        s3_object = record['s3']['object']['key']
        logger.info(s3_object)
        regex = re.compile(ITEM_REGEX)
        is_new_file_matching_regex= re.match(regex, s3_object)
        # logger.info("Is " + s3_object + " is matching ::" + is_new_file_matching_regex)
        if(is_new_file_matching_regex):
            # Split object by '/' and getting first item as cluster name
            log_stream_name=s3_object
            s3_object = s3_client.get_object(Bucket=bucket, Key=s3_object)
            file_content = s3_object['Body'].read()
            write_to_cloudwatch_in_chunks(log_stream_name, file_content)


def write_to_cloudwatch_in_chunks(log_stream_name, log_data):
    log_data_chunks = [log_data[i:i+MAX_BATCH_SIZE] for i in range(0, len(log_data), MAX_BATCH_SIZE)]
    
    try:
        response = logs_client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=log_stream_name
        )
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass
    
    # Iterating each chunck
    sequence_token = None
    for log_data_chunk in log_data_chunks:
        kwargs = {
            'logGroupName': log_group_name,
            'logStreamName': log_stream_name,
            'logEvents': [
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': log_data_chunk.decode('utf-8')
                },
            ]
        }
        if sequence_token:
            kwargs['sequenceToken'] = sequence_token
        response = logs_client.put_log_events(**kwargs)
        sequence_token = response['nextSequenceToken']
        logger.info(response)
