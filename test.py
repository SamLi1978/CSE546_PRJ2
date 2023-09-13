
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

ami = 'ami-045bfe57a27b5d826'
name_tag = 'cse546-app-instance'

def app_instance_scheduling():

    print("Create ec2 instances...")

    ec2 = boto3.resource('ec2')
    instances = ec2.create_instances(ImageId=ami, MinCount=2, MaxCount=2, InstanceType='t2.micro', 
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



if __name__ == "__main__":



