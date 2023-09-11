
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import json
import sys
import numpy as np

import boto3
import os
import time
import binascii

sqs_url_input = "https://sqs.us-east-1.amazonaws.com/307466288757/cse546-input-sqs"
sqs_url_output = "https://sqs.us-east-1.amazonaws.com/307466288757/cse546-output-sqs"
s3_name_input = "cse546-input-bucket"
s3_name_output = "cse546-output-bucket"

image_label_json = 'imagenet-labels.json'


def sqs_send_message(sqs_url, message_body):
    sqs = boto3.client('sqs')
    response = sqs.send_message(QueueUrl=sqs_url,
            MessageBody=f'{message_body}')
    return response   

def sqs_receive_message(sqs_url):
    sqs = boto3.client('sqs')
    response = sqs.receive_message(QueueUrl=sqs_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0)
            #WaitTimeSeconds=0)    
    print(response)
    messages = response.get('Messages')
    if (messages == None):
        return False
    message = messages[0]
    message_body = message['Body']
    receipt_handle = message['ReceiptHandle']    
    return message_body,receipt_handle

def sqs_delete_message(sqs_url, receipt_handle):
    sqs = boto3.client('sqs')
    sqs.delete_message(QueueUrl=sqs_url, ReceiptHandle=receipt_handle)

def sqs_query_message_count(sqs_url):
    sqs = boto3.client('sqs')
    response = sqs.get_queue_attributes(QueueUrl=sqs_url,AttributeNames=['ApproximateNumberOfMessages'])
    #print(response)
    count = response.get('Attributes')['ApproximateNumberOfMessages']
    return int(count)

def s3_download_file(s3_name, file_name):
    s3 = boto3.client('s3')

    try:
        response = s3.get_object(Bucket=s3_name, Key=file_name)
        hex_bytes = response.get('Body')
    finally:
        return False
    return hex_bytes


def s3_upload_image_result(s3_name, file_name, result):
    s3 = boto3.client('s3')
    response = s3.put_object(Bucket=s3_name, Key=file_name, Body=file_name,
        Metadata={f'{file_name}':f'({file_name},{result})'})
    return response

def image_classify(file_name):

    model = models.resnet18(pretrained=True)
    model.eval()

    img = Image.open(file_name)
    img_tensor = transforms.ToTensor()(img).unsqueeze_(0)
    outputs = model(img_tensor)
    _, predicted = torch.max(outputs.data, 1)

    with open(image_label_json) as f:
        labels = json.load(f)

    result = labels[np.array(predicted)[0]]
    #print(f"{result}")
    return result

        

if __name__ == "__main__":
    
    
    while True:
        time.sleep(0.1)
        
        msg_count = sqs_query_message_count(sqs_url_input)
        if msg_count==0:
            continue

     
        response = sqs_receive_message(sqs_url_input)
        if response == False:
            print("msg is gone")
            continue
        message = response[0]
        receipt_handle = response[1]
        print(f'message {message}')
            
        #sqs_delete_message(sqs_url_input, receipt_handle)

    
