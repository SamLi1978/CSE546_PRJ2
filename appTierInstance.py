from image_classification import ClassifyImage
from dotenv import load_dotenv
import time
import os
import boto3
import logging

logging.basicConfig(
    filename='/home/ubuntu/classifier/logs/app.log',
    level=logging.INFO)

load_dotenv()

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

class AppTierInstance():
    def __init__(self) -> None:
        pass

    def sendMessage(self, queue_url, sqs, image_name, result):
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=f'{image_name}, {result}',
            MessageGroupId='images',
        )

        return response

    def receiveMessage(self, queue_url, sqs):
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ]
        )

        return response

    def deleteMessage(self, queue_url, sqs, receipt_handle):
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

    def putBucket(self, s3, bucket_name, image_name, result):
        object_value = f'({image_name}, {result})'
        response = s3.put_object(
            Bucket=bucket_name, Key=image_name, Body=object_value)
        return response


if __name__ == "__main__":
    run = AppTierInstance()
    sqs = boto3.client(
        'sqs',
        region_name='us-east-1',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    s3 = boto3.client(
        's3',
        region_name='us-east-1',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    logging.info('Initialized boto3 clients.')

    request_queue_url = 'https://sqs.us-east-1.amazonaws.com/947390209074/RequestQueue.fifo'
    response_queue_url = 'https://sqs.us-east-1.amazonaws.com/947390209074/ResponseQueue.fifo'
    get_bucket_name = 'input-images-cc-2022'
    put_bucket_name = 'output-bucket-cc-2022'

    # receive message from the queue
    while (True):
        logging.info('Running next iteration.')
        time.sleep(1)
        request_queue_response = {}

        try:
            request_queue_response = run.receiveMessage(request_queue_url, sqs)
            logging.info('request queue response', request_queue_response)
        except:
            logging.info('Something went wrong with request queue response receive message.')
            continue

        # do image classification
        if 'Messages' in request_queue_response and len(request_queue_response['Messages']) > 0:

            messages = request_queue_response['Messages']
            message = messages[0]
            message_body = message['Body']
            receipt_handle = message['ReceiptHandle']

            result = ClassifyImage.classifyImage(get_bucket_name, message_body)
            logging.info('result', result)

            if '.JPEG' in message_body:
                image_name = message_body.rstrip('.JPEG')
                logging.info('image_name', image_name)
            else:
                continue

            # send message to response queue
            response = run.sendMessage(
                response_queue_url, sqs, image_name, result)
            logging.info(response['MessageId'])
            logging.info('Sent message to response queue.')
            # put the object to the output bucket
            repsonse = run.putBucket(s3, put_bucket_name, image_name, result)
            logging.info('Uploaded image to output S3 bucket.')

            # delete the message from the request queue
            run.deleteMessage(request_queue_url, sqs, receipt_handle)
            logging.info('Deleted message from request queue.')
        else:
            logging.info('No message in the request queue.')

