import boto3
import os


INSTANCE_TYPE = os.environ["INSTANCE_TYPE"]  # instance type to launch.
REGION = os.environ["REGION"]  # region to launch instance.
AMI = os.environ["AMI"]
INSTANCE_PROFIL_NAME = os.environ["INSTANCE_PROFIL_NAME"]

device_size = os.environ['DEVICE_SIZE']
script_score_key = os.environ["REQUIREMENT_SCRIPT_KEY"]
script_requirements_key = os.environ["TRAIN_SCRIPT_KEY"]

JOB_ID = os.environ["JOB_ID"]

EC2 = boto3.client('ec2', region_name=REGION)

cmd_config = """#!/bin/bash
sudo yum update -y
sudo yum install -y amazon-linux-extras
sudo amazon-linux-extras enable python3.8
sudo yum install python3.8 -y
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo systemctl start amazon-ssm-agent
sudo yum -y install python-pip
pip3.8 install awscli
mkdir appli
chmod 777 appli
aws s3 cp """ + script_score_key + """ appli/
aws s3 cp """ + script_requirements_key + """ appli/
"""


def lambda_handler(event, context):
    instance = EC2.run_instances(
        ImageId=AMI,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        BlockDeviceMappings=[
            {
                'DeviceName': 'xvdc',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeType': "gp2",
                    'VolumeSize': int(device_size)
                }
            }
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'OS',
                        'Value': 'Centos'
                    },
                    {
                        'Key': 'Instance_Market',
                        'Value': 'reserved_instance'
                    },
                    {
                        'Key': 'Application',
                        'Value': 'PA_TDV'
                    },
                    {
                        'Key': 'job_id',
                        'Value': JOB_ID
                    }
                ]
            }
        ],
        IamInstanceProfile={
            'Name': INSTANCE_PROFIL_NAME
        },
        Monitoring={
            'Enabled': True
        },
        #KeyName='credential_test_pa',
        UserData=cmd_config
    )

    instance_id = instance['Instances'][0]['InstanceId']
    ip_address = instance['Instances'][0]['PrivateIpAddress']
    print(instance_id)
    print(ip_address)
    return 0