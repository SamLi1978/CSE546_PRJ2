

import configparser
import os
import boto3
import time
import sys

ami = 'ami-0ce4e4a1afefc6fb7'
name_tag = 'cse546-app-instance'

sqs_url_input = "cse546-input-sqs"
sqs_url_output = "cse546-output-sqs"

instances_limit = 15


def get_ec2_state(ec2_client, instance_id):

    response = ec2_client.describe_instance_status(InstanceIds=[instance_id],)
    #print(response)
    ins_states = response['InstanceStatuses']
    print(ins_states)
    state_name = ''
    for ins_state in ins_states:
        state_name = ins_states['InstanceState']['Name']
        state_code = ins_states['InstanceState']['Code']
        print(state_code)
    return state_name
    
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

def sqs_query_message_count(sqs_client, sqs_url):
    response =  sqs_client.get_queue_attributes(QueueUrl=sqs_url,AttributeNames=['ApproximateNumberOfMessages','ApproximateNumberOfMessagesNotVisible'])
    #print(response)
    visible_count = int(response.get('Attributes')['ApproximateNumberOfMessages'])
    invisible_count = int(response.get('Attributes')['ApproximateNumberOfMessagesNotVisible'])
    
    return visible_count, invisible_count

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


if __name__ == "__main__":

    ec2 = boto3.resource('ec2')
    sqs_client = boto3.client('sqs')        

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

        if ((sqs_input_v==0) and (sqs_input_inv==0) and (sqs_output_v==0) and (sqs_output_inv==0)):
            if instances_running_count > 0:
                print('terminate the running instances...')
                instances_running.terminate()
            if instances_pending_count > 0:
                print('terminate the pending instances...')
                instances_pending.terminate()

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


