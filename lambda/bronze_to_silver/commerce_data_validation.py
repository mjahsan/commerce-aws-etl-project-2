import json
import boto3
import logging
import urllib.parse
import os

s3 = boto3.client('s3')
glue = boto3.client("glue")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_PREFIX = 'bronze_commerce/'
TARGET_PREFIX = 'silver_commerce/'
ALLOWED_FILES = {"user.json", "events.json", "orders.json"}

def lambda_handler(event, context):
    # Creating a list of processed files to enable Glue run
    processed_files = []

    # Extracting Bucket & Key from the event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key']) #decoding
        filename = key.split('/').pop()

        # Eliminating files that are not in the bronze/ or doesn't match the filenames or not .json
        if not key.startswith(VALID_PREFIX):
            logger.info(f"Skipping non-bronze file: {key}, as it is not in {VALID_PREFIX}")
            continue
        if filename not in ALLOWED_FILES:
            logger.info(f"Skipping unallowed file: {key}, as it is not in {ALLOWED_FILES}")
            continue

        # Continuing with the allowed files 
        logger.info(f'Processing file: {filename}')
        # Raising exceptions for empty files
        head = s3.head_object(Bucket=bucket, Key=key)
        if head['ContentLength'] == 0:
            raise ValueError(f"Empty file detected in {key}")

        #Reassigning the filename to the target partition with additional sub folder for downstream visibility
        folder_name = filename.split(".")[0]
        target_key = key.replace(VALID_PREFIX, f"{TARGET_PREFIX}{folder_name}/", 1)

        #Copying the file to the target prefix - More prone to error due to access deny
        try:
            s3.copy_object(
                CopySource={'Bucket':bucket, 'Key':key},
                Bucket=bucket,
                Key=target_key
            )
            processed_files.append(filename)
            logger.info(f'Successfully copied {key} to {target_key}')
        except Exception as e:
            logger.error(f"Failed to copy {key}:{str(e)}")
            raise

        #Deleting the original file - Not recommended as it is the source of truth
        # s3.delete_object(
        #   Bucket=bucket,
        #   Key=key
        # )

    # Enabling Glue run once all filesare transferred to TARGET_PREFIX
    required_files = {"user", "events", "orders"}
    response = s3.list_objects_v2(
                    Bucket=bucket, 
                    Prefix=TARGET_PREFIX
                )
    found = set()
    for obj in response.get('Contents',[]):
        for f in required_files:
            if f"{f}" in obj['Key']:
                found.add(f)

    if found == required_files:
        try:
            glue.start_job_run(JobName="silver_commerce_transformation")
            logger.info(f"Successfully initiated Glue job for {processed_files}")
        except Exception as e:
            logger.error(f"Failed to initiate Glue job for {processed_files}:{str(e)}")
            raise 