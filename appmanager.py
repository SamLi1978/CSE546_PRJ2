
import boto3
import os
import time
import binascii
import configparser

from multiprocessing import Process
from multiprocessing import Manager

pipe_name = "my_pipe"
sqs_url_input = "https://sqs.us-east-1.amazonaws.com/231128306811/cse546-input-sqs"
sqs_url_output = "https://sqs.us-east-1.amazonaws.com/231128306811/cse546-output-sqs"
s3_name_input = "cse546-input-s3"
s3_name_output = "cse546-output-s3"

image_uploaded_dir = './images_uploaded'

image_result_ini = 'image_result.ini'
image_result_section = 'image_result'

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
    #print(response)
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
    return response.get('Attributes')['ApproximateNumberOfMessages']

def s3_upload_file(s3_name, file_name, file_blob):
    s3 = boto3.client('s3')
    response = s3.put_object(Bucket=s3_name, Key=file_name, Body=file_blob)
    return response

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


def read_file_blob(image_name):

    with open(f'{image_uploaded_dir}/{image_name}', 'rb') as imagefile:
        blob_data = binascii.hexlify(imagefile.read())
        imagefile.close()
        #print(blob_data)    
        return blob_data

def write_file_blob(file_name, file_blob):

    with open(f'{file_name}', 'wb') as imagefile:
        unhex_bytes = binascii.unhexlify(file_blob)
        imagefile.write(unhex_bytes)
        imagefile.close()

def image_result_set_data(key, value):

    if not os.path.exists(image_result_ini):
        with open(image_result_ini, 'w') as ini:
            pass

    config = configparser.ConfigParser()

    '''
    config.read('test.ini')
    or 
    with open(image_result_ini, 'r') as ini:
        config.read_file(ini)

    Both of them make the ini file appendable, or the ini file will be rewritten.
    '''
    with open(image_result_ini, 'r') as ini:
        config.read_file(ini)
 
    if config.has_section(image_result_section) == False:
        config.add_section(image_result_section)    
    
    config.set(image_result_section, key, value)

    with open(image_result_ini, 'w') as ini:
        config.write(ini)


def handle_pipe(pipe, shared_list):

    while True:

        time.sleep(0.1)
        
        try:
            s = os.read(pipe,20)
            rx_str = str(s, encoding='utf-8')
            image_name = rx_str.strip()
            print(f"handle_pipe {image_name}")
            shared_list.append(image_name)

        except BlockingIOError:
            pass

def handle_request(shared_list):

    while True:

        time.sleep(1)

        if not shared_list:
            continue

        image_name = shared_list.pop()          
        print(f"handle_request {image_name}")

        image_blob = read_file_blob(image_name)
        #print(image_blob)

        response = sqs_send_message(sqs_url_input, image_name)
        #print(response)

        response = s3_upload_file(s3_name_input, image_name, image_blob)
        #print(response)


def handle_sqs_output_message():

    while True:

        time.sleep(1)

        msg_count = sqs_query_message_count(sqs_url_output)
        if msg_count==0:
            print("no message")
            continue

        response = sqs_receive_message(sqs_url_output)
        if response == False:
            print("msg is gone")
            continue

        message = response[0]
        receipt_handle = response[1]
        formatted = message.split(',')
        image_result_set_data(formatted[0], formatted[1])
        print(f'message {message}')
                
        sqs_delete_message(sqs_url_output, receipt_handle)
           

if __name__ == "__main__":

    if (os.path.exists(pipe_name)):
        os.remove(pipe_name)
    os.mkfifo(pipe_name)

    pipe = os.open(pipe_name, os.O_RDWR | os.O_NONBLOCK)

    with Manager() as manager:
        shared_list = manager.list()
        process_pipe = Process(target=handle_pipe, args=(pipe, shared_list))
        process_request = Process(target=handle_request, args=(shared_list,))
        process_sqs = Process(target=handle_sqs_output_message, args=())
        process_pipe.start()
        process_request.start()
        process_sqs.start()
        process_pipe.join()
        process_request.join()
        process_sqs.join()


