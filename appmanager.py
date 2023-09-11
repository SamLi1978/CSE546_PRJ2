
import boto3
import os
import time
import binascii
from multiprocessing import Process
from multiprocessing import Manager

pipe_name = "my_pipe"
sqs_url_input = "https://sqs.us-east-1.amazonaws.com/307466288757/cse546-input-sqs"
sqs_url_output = "https://sqs.us-east-1.amazonaws.com/307466288757/cse546-output-sqs"
s3_name_input = "cse546-input-bucket"
s3_name_output = "cse546-output-bucket"
ite = 0


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

    with open(f'images/{image_name}', 'rb') as imagefile:
        blob_data = binascii.hexlify(imagefile.read())
        imagefile.close()
        #print(blob_data)    
        return blob_data

def write_file_blob(file_name, file_blob):

    with open(f'{file_name}', 'wb') as imagefile:
        unhex_bytes = binascii.unhexlify(file_blob)
        imagefile.write(unhex_bytes)
        imagefile.close()

def write_image_result(image_result):
    
    with open(f'image_result.txt', 'a') as image_result_file:
        image_result_file.write(f'{image_result}\n')
        image_result_file.close()

def handle_pipe(pipe, shared_list):

    while True:

        time.sleep(0.01)
        
        try:
            s = os.read(pipe,20)
            rx_str = str(s, encoding='utf-8')
            image_name = rx_str.strip()
            print(f"handle_pipe {image_name}")
            shared_list.append(image_name)

        except BlockingIOError:
            pass

def handle_request(ite, shared_list):

    while True:

        time.sleep(0.01)

        if not shared_list:
            continue

        image_name = shared_list.pop()          
        print(f"handle_request {image_name}")

        image_blob = read_file_blob(image_name)
        #print(image_blob)

        response = sqs_send_message(sqs_url_input, image_name)
        #print(response)

        response = sqs_receive_message(sqs_url_input)
        if response == False:
            print("No message")
        else:
            message = response[0]
            receipt_handle = response[1]
            print(f'message {message}')
            
            sqs_delete_message(sqs_url_input, receipt_handle)
           
            message_in_queue = sqs_query_message_count(sqs_url_input)
            print(message_in_queue)   


        response = s3_upload_file(s3_name_input, image_name, image_blob)
        #print(response)

        response = s3_upload_image_result(s3_name_output, image_name, f'result{ite}')
        #print(response)

        response = sqs_send_message(sqs_url_output, f'{image_name},result{ite}')
        ite = ite + 1
        #print(response)

        response = sqs_receive_message(sqs_url_output)
        if response == False:
            print("No message")
        else:
            message = response[0]
            receipt_handle = response[1]
            write_image_result(message)
            print(f'message {message}')
            
            sqs_delete_message(sqs_url_output, receipt_handle)
           
            message_in_queue = sqs_query_message_count(sqs_url_output)
            print(message_in_queue)   


if __name__ == "__main__":

    if (os.path.exists(pipe_name)):
        os.remove(pipe_name)
    os.mkfifo(pipe_name)

    pipe = os.open(pipe_name, os.O_RDWR | os.O_NONBLOCK)

    with Manager() as manager:
        shared_list = manager.list()
        process1 = Process(target=handle_pipe, args=(pipe, shared_list))
        process2 = Process(target=handle_request, args=(ite, shared_list,))
        process1.start()
        process2.start()
        process1.join()
        process2.join()


