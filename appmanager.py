
import boto3
import os
import time
import binascii
import configparser

from multiprocessing import Process
from multiprocessing import Manager

pipe_name = "my_pipe"

sqs_url_input = "cse546-input-sqs"
sqs_url_output = "cse546-output-sqs"

s3_name_input = "cse546-input-s3"
s3_name_output = "cse546-output-s3"

image_uploaded_dir = './images_uploaded'

image_result_ini = 'image_result.ini'
image_result_section = 'image_result'

ami = 'ami-0ce4e4a1afefc6fb7'
name_tag = 'cse546-app-instance'

instances_limit = 15


def ec2_create_instances(ec2, count):

    instances = ec2.create_instances(ImageId=ami, MinCount=count, MaxCount=count, InstanceType='t2.micro', 
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': name_tag
                },
            ]
        },
    ],)    

def ec2_list_app_instances(ec2):

    '''    
    instances = ec2.instances.all()
    print(f"instance count : {len(list(instances))}")
    for instance in instances:
        #instance = ec2.Instance('i-009986e8937d17bd4')
        print(instance.instance_id)
        print(instance.image_id)
        print(instance.tags)
        print(instance.state)
    '''

    '''
    instances_running = ec2.instances.filter(
    Filters=[
                {
                    'Name':'tag-key', 
                    'Values':[name_tag]
                },

                {
                    'Name':'instance-state-name', 
                    'Values':['running']
                },
            ]
    )
    instances_pending = ec2.instances.filter(
    Filters=[
                {
                    'Name':'tag:Name', 
                    'Values':[name_tag]
                },

                {
                    'Name':'instance-state-name', 
                    'Values':['pending']
                },
            ]
    )
    '''

    instances_running = ec2.instances.filter(
    Filters=[
                {
                    'Name':'image-id', 
                    'Values':[ami]
                },

                {
                    'Name':'instance-state-name', 
                    'Values':['running']
                },
            ]
    )
    instances_pending = ec2.instances.filter(
    Filters=[
                {
                    'Name':'image-id', 
                    'Values':[ami]
                },

                {
                    'Name':'instance-state-name', 
                    'Values':['pending']
                },
            ]
    )

    return instances_running, instances_pending


def sqs_send_message(sqs_client, sqs_url, message_body):
    response = sqs_client.send_message(QueueUrl=sqs_url,
            MessageBody=f'{message_body}')
    return response   

def sqs_receive_message(sqs_client, sqs_url):
    response = sqs_client.receive_message(QueueUrl=sqs_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=15)
            #WaitTimeSeconds=0)    
    #print(response)
    messages = response.get('Messages')
    if (messages == None):
        return False
    message = messages[0]
    message_body = message['Body']
    receipt_handle = message['ReceiptHandle']    
    return message_body,receipt_handle

def sqs_delete_message(sqs_client, sqs_url, receipt_handle):
    sqs_client.delete_message(QueueUrl=sqs_url, ReceiptHandle=receipt_handle)


def sqs_query_message_count(sqs_client, sqs_url):
    response =  sqs_client.get_queue_attributes(QueueUrl=sqs_url,AttributeNames=['ApproximateNumberOfMessages','ApproximateNumberOfMessagesNotVisible'])
    #print(response)
    visible_count = int(response.get('Attributes')['ApproximateNumberOfMessages'])
    invisible_count = int(response.get('Attributes')['ApproximateNumberOfMessagesNotVisible'])
    
    return visible_count, invisible_count

def s3_upload_file(s3_client, s3_name, file_name, file_blob):
    response = s3_client.put_object(Bucket=s3_name, Key=file_name, Body=file_blob)
    return response

def s3_download_file(s3_client, s3_name, file_name):

    try:
        response = s3_client.get_object(Bucket=s3_name, Key=file_name)
        hex_bytes = response.get('Body')
    finally:
        return False
    return hex_bytes


def s3_upload_image_result(s3_client, s3_name, file_name, result):
    response = s3_client.put_object(Bucket=s3_name, Key=file_name, Body=file_name,
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

    Mode    Description	                        File Pointer Position	Creates File if Not Exists	Truncates Existing File
    r	    Read-only	                        Beginning of the file	No	                        No
    r+	    Read and write (updating)	        Beginning of the file	No	                        No
    w	    Write-only (overwrite or create)	Beginning of the file	Yes	                        Yes
    w+	Write and read (overwrite or create)	Beginning of the file	Yes	                        Yes
    a	Append-only (append or create)	        End of the file	        Yes	                        No
    a+	Append and read (append or create)	    End of the file	        Yes	                        No

    '''

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

    sqs_client = boto3.client('sqs')
    s3_client = boto3.client('s3')

    while True:

        time.sleep(1)

        if not shared_list:
            continue

        image_name = shared_list.pop()          
        print(f"handle_request {image_name}")

        image_blob = read_file_blob(image_name)
        #print(image_blob)

        response = sqs_send_message(sqs_client, sqs_url_input, image_name)
        #print(response)

        response = s3_upload_file(s3_client, s3_name_input, image_name, image_blob)
        #print(response)


def handle_sqs_output_message():

    sqs_client = boto3.client('sqs')

    while True:

        time.sleep(1)

        msg_count_visible, msg_count_invisible = sqs_query_message_count(sqs_client, sqs_url_output)
        if msg_count_visible == 0:
            #print("no message")
            continue

        response = sqs_receive_message(sqs_client, sqs_url_output)
        if response == False:
            #print("msg is gone")
            continue

        message = response[0]
        receipt_handle = response[1]
        formatted = message.split(',')
        image_result_set_data(formatted[0], formatted[1])
        print(f'message {message}')
                
        sqs_delete_message(sqs_client, sqs_url_output, receipt_handle)
           

def handle_app_instances_scheduling():

    ec2 = boto3.resource('ec2')
    sqs_client = boto3.client('sqs')        

    try_to_shut_down_all_app_instances = 0
    try_to_shut_down_all_app_instances_limit = 4

    while True:

        time.sleep(5)

        sqs_input_v, sqs_input_inv = sqs_query_message_count(sqs_client, sqs_url_input)
        print("sqs_input : ", sqs_input_v, sqs_input_inv)

        sqs_output_v, sqs_output_inv = sqs_query_message_count(sqs_client, sqs_url_output)
        print("sqs_output : ", sqs_output_v, sqs_output_inv)

        instances_running, instances_pending = ec2_list_app_instances(ec2)
        instances_running_count = len(list(instances_running))
        instances_pending_count = len(list(instances_pending))
        instances_total = instances_running_count + instances_pending_count
        print("instances : ", instances_running_count, instances_pending_count, instances_total)

        print(f"try_to_shut_down_all_app_instances = {try_to_shut_down_all_app_instances}")

        if ((sqs_input_v==0) and (sqs_input_inv==0) and (sqs_output_v==0) and (sqs_output_inv==0)):
            if instances_running_count > 0:
                if try_to_shut_down_all_app_instances > try_to_shut_down_all_app_instances_limit:
                    try_to_shut_down_all_app_instances = 0
                    print('terminate the running instances...')
                    instances_running.terminate()
                else:
                    try_to_shut_down_all_app_instances = try_to_shut_down_all_app_instances + 1
                    print(f"try to shut down all app instances for the {try_to_shut_down_all_app_instances} time...")
            else:
                try_to_shut_down_all_app_instances = 0                                
            '''
            if instances_pending_count > 0:
                print('terminate the pending instances...')
                instances_pending.terminate()
            '''
        else:
            try_to_shut_down_all_app_instances = 0

        if (sqs_input_v > 0):
            if instances_total >= instances_limit:
                # do nothing
                print(f"total number is {instances_total} and do nothing...")
                pass
            if instances_total == 0:
                print("total number is 0, create 10 instances...")
                # start 10 instances
                ec2_create_instances(ec2, 10)
            if instances_total > 0 and instances_total < instances_limit:
                # start some instances
                count_need_to_start = sqs_input_v // 10
                if (count_need_to_start + instances_total > instances_limit):
                    print(f"{count_need_to_start} + {instances_total} = {count_need_to_start+instances_total} will be rearching the limit, so choose to do nothing...")
                else:
                    if (count_need_to_start > 0):
                        print(f"total number is {instances_total}, create {count_need_to_start} instances...")
                        ec2_create_instances(ec2, count_need_to_start)


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
        process_app = Process(target=handle_app_instances_scheduling, args=())

        process_pipe.start()
        process_request.start()
        process_sqs.start()
        process_app.start()

        process_pipe.join()
        process_request.join()
        process_sqs.join()
        process_app.join()


