import logging, sys, uuid
from botocore.exceptions import ClientError

def generate_job_id():
    return uuid.uuid4().__str__()


def upload_file_to_s3(s3_client, local_path, bucket, s3_key):
    s3_client.upload_file(local_path, bucket, s3_key)


def create_viz_clf_stack(clf_client,
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
        logging.error(f"creation de la stack echouée...")
        raise Exception(cle)


def progress_bar(i, comment):
    sys.stdout.write(f"\r|%s> {comment}" % ('='*i))
    sys.stdout.flush()

def get_dashboard_name(nomenclature_object):
    return nomenclature_object.get_dashboard_name()