import uuid, sys, logging, boto3, json
from botocore.exceptions import ClientError


def generate_job_id():
    return uuid.uuid4().__str__()

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


def get_restapi_id(job_id, access_key_id, secret_access_key, region):
    apigetway_client = boto3.client('apigateway', aws_access_key_id=access_key_id,
                                    aws_secret_access_key=secret_access_key,
                                    region_name=region)
    try:
        rest_apis = apigetway_client.get_rest_apis(
            limit=499
        )

        list_rest_apis = list(
            filter(lambda item: ("JOBID" in item['tags']) and (item['tags']["JOBID"] == job_id), rest_apis['items']))
        if len(list_rest_apis) == 0:
            raise Exception(f"Aucune API Gateway avec le tag JOBID:<{job_id}>")
        api = list_rest_apis[0]
        return api['id']
    except ClientError as cle:
        logging.error("[DEPLOYMENT]: erreur recuperation id API GATEWAY")
        raise Exception(cle)


def get_api_endpoint(job_id, access_key_id, secret_access_key, region):
    try:
        api_id = get_restapi_id(job_id, access_key_id, secret_access_key, region)
        apigetway_client = boto3.client('apigateway', aws_access_key_id=access_key_id,
                                        aws_secret_access_key=secret_access_key,
                                        region_name=region)
        apigetway_response = apigetway_client.get_export(
                                restApiId = api_id,
                                stageName = "apiprediction",
                                exportType = 'oas30'
                            )

        url_component = json.loads(apigetway_response['body'].read())['servers']
        url = url_component[0]['url'].split('/')[:-1]
        resource_methode = "apiprediction/prediction"
        url.append(resource_methode)
        return '/'.join(url)
    except ClientError as cle:
        logging.error("[DEPLOYMENT]: get_api_endpoint()")
        raise Exception(cle)
    except Exception as exp:
        logging.error("[DEPLOYMENT]: get_api_endpoint()")
        raise Exception(exp)



def progress_bar(i):
    sys.stdout.write("\r|%s>" % ('='*i))
    sys.stdout.flush()
