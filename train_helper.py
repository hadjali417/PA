import boto3, uuid, sys, time
from botocore.exceptions import ClientError
import logging


def generate_job_id():
    return uuid.uuid4().__str__()

def delete_all_ressources(stack_name):
    clf_client = boto3.client('cloudformation')
    clf_client.delete_stack(StackName=stack_name)

def upload_file_to_s3(s3_client, local_path, bucket, s3_key):
    s3_client.upload_file(local_path, bucket, s3_key)

def create_train_clf_stack(clf_client,
                     stack_name: str,
                     template_url: str,
                     list_parameters: list
                     ):
    try:
        clf_response = clf_client.create_stack(
            StackName = stack_name,
            TemplateURL = template_url,
            Parameters = list_parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        return clf_response['StackId']
    except ClientError as cle:
        logging.error(f"creation de la stack echouée... {cle}")
        return None

def run_ec2_command(instance_id, commands, aws_access_key_id, aws_secret_access_key, region):
    ssm_client = boto3.client('ssm', aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key, region_name = region)
    try:
        response = ssm_client.send_command(
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': commands},
                InstanceIds=[
                    instance_id
                ]
            )
        return response
    except ClientError as cle:
        logging.error(f"impossible d'executer la commande : {commands}")
        raise Exception(cle)


def get_command_status(instance_id, command_id, aws_access_key_id, aws_secret_access_key, region):
    ssm_client = boto3.client('ssm', aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key, region_name = region)
    try:
        command_status = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        return {
            "status": command_status['Status'],
            "status_details": command_status['StatusDetails']
        }
    except ClientError as cle:
        logging.error(f"impossible d'obtenir le statut de la commande suivante: {command_id}")
        raise Exception(cle)


"""def get_ec2_instance_id(stack_name, access_key_id, secret_access_key, region):
    clf_client = boto3.client('cloudformation', aws_access_key_id=access_key_id,
                              aws_secret_access_key=secret_access_key, region_name=region)
    try:
        clf_response = clf_client.list_stack_resources(
            StackName=stack_name
        )
        list_ressources = clf_response['StackResourceSummaries']
        ec2_ressource = list(filter(lambda rs : rs['ResourceType'] == "AWS::EC2::Instance", list_ressources))[0]
        return ec2_ressource['']
    except ClientError as cle:
        logging.error(f"impossible d'obtenir l'id de l'instance d'entrainement!'")
        logging.error(cle)
        return None"""

"""def get_ec2_instance_id(job_id, access_key_id, secret_access_key, region):
    ec2_resource = boto3.resource('ec2', aws_access_key_id = access_key_id, aws_secret_access_key = secret_access_key, region_name = region)
    instances = ec2_resource.instances.filter(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    job_id
                ]
            }
        ]
    )
    if len(instances)==0:
        raise Exception(f"impossible d'obtenir l'id de l'instance d'entrainement pour le job: {job_id}!")
    instance_id = instances[0]['instance_id']
    return instance_id
"""

def get_ec2_instance_id(job_id, access_key_id, secret_access_key, region):
    ec2_client = boto3.client('ec2', aws_access_key_id = access_key_id, aws_secret_access_key = secret_access_key, region_name = region)
    instances = ec2_client.describe_instances(
        Filters=[
            {
                'Name': "tag:job_id",
                'Values': [
                    job_id,
                ]
            }
        ]
    )
    if len(instances['Reservations'])==0:
        raise Exception(f"impossible d'obtenir l'id de l'instance d'entrainement pour le job: {job_id}!")
    return instances['Reservations'][0]['Instances'][0]['InstanceId']


def get_train_ec2_instance_status(instance_id, access_key_id, secret_access_key, region):
    ec2_client = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                  region_name=region)
    ec2_response = ec2_client.describe_instance_status(
        InstanceIds = [
            instance_id,
        ],
        IncludeAllInstances=True
    )
    instances_status = ec2_response['InstanceStatuses']
    if len(instances_status)==0:
        raise Exception(f"Auncune instance avec l'identifiant suivant: {instance_id}")

    if instances_status[0]["InstanceState"]["Name"]=="pending":
        return instances_status[0]["InstanceState"]["Name"]
    if instances_status[0]["InstanceState"]["Name"] == "running":
        if instances_status[0]['InstanceStatus']['Details'][0]['Status']=='passed':
            return instances_status[0]["InstanceState"]["Name"]
        if instances_status[0]['InstanceStatus']['Details'][0]['Status']=='initializing':
            return "pending"
    return 'Failed'


def progress_bar(i):
    sys.stdout.write("\r|%s>" % ('='*i))
    sys.stdout.flush()









