
'''

Mode    Description	                        File Pointer Position	Creates File if Not Exists	Truncates Existing File
r	    Read-only	                        Beginning of the file	No	                        No
r+	    Read and write (updating)	        Beginning of the file	No	                        No
w	    Write-only (overwrite or create)	Beginning of the file	Yes	                        Yes
w+	Write and read (overwrite or create)	Beginning of the file	Yes	                        Yes
a	Append-only (append or create)	        End of the file	        Yes	                        No
a+	Append and read (append or create)	    End of the file	        Yes	                        No

'''


import configparser
import os
import boto3
import time
import sys

ami = 'ami-0ce4e4a1afefc6fb7'
name_tag = 'cse546-app-instance'

def app_instance_scheduling():

    print("Create ec2 instances...")

    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(ImageId=ami, MinCount=20, MaxCount=20, InstanceType='t2.micro', 
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

    input("Any key to terminate all the ec2 instances...")


    ec2_client = boto3.client('ec2')
    instance_list = [instance.instance_id for instance in instances]
    ec2_client.terminate_instances(InstanceIds=instance_list)


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
    
def list_ec2_instances(ec2):
    
    instances = ec2.instances.all()
    print(f"instance count : {len(list(instances))}")
    for instance in instances:
        #instance = ec2.Instance('i-009986e8937d17bd4')
        print(instance.instance_id)
        print(instance.image_id)
        print(instance.tags)
        print(instance.state)

def terminate_ec2_instances(ec2):

if __name__ == "__main__":

    #ec2 = boto3.resource('ec2')
    #list_ec2_instances(ec2)
	app_instance_scheduling()
