import boto3, uuid
from botocore.exceptions import ClientError
import logging


def generate_job_id():
    return uuid.uuid4()

def get_train_status(job_id):
    pass

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
        logging.error(f"creation stack echouée... {cle}")







