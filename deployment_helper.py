import uuid, sys, logging, boto3, json, dill
from botocore.exceptions import ClientError
import pickle, inspect

def generate_job_id():
    """
        génère un ID unique à chaque appel
        :return: str
                    * un identifiant unique généré depuis la lib uuid
    """
    return uuid.uuid4().__str__()

def upload_file_to_s3(s3_client, local_path, bucket, s3_key):
    """
        :param s3_client: Client s3 (client_s3 = boto3.client('s3'))
        :param local_path: chemin local vers le fichier à charger vers S3
        :param bucket:  bucket S3 vers lequel charger le fichier
        :param s3_key: prefixe s3 vers lequel charger le fichier
        :return: None
    """
    s3_client.upload_file(local_path, bucket, s3_key)

def create_deployment_clf_stack(clf_client,
                     stack_name: str,
                     template_url: str,
                     list_parameters: list
                     ):
    """
        :param clf_client: client CloudFormation boto3
        :param stack_name: nom unique de la pile CloudFormation
        :param template_url: url S3 du template CloudFormation
        :param list_parameters: liste des parametres de la pile CloudFormation
        :return: str
                    * ID unique de la pile CloudFormation créée
        génère une exception si la création de la pile est KO
        """
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


def get_restapi_id(job_id, access_key_id, secret_access_key, region):
    """
    :param job_id: ID unique pour le deploiement (obtenu via la lib uuid)
    :param access_key_id: ID de la clé d'authentification AWS
    :param secret_access_key: clé secrete d'authentification AWS
    :param region: region AWS (exemple: us-west-1)
    :return: str:
                * ID unique de la ressource API Gateway
    """
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
    """
    :param job_id: ID unique pour le deploiement (obtenu via la lib uuid)
    :param access_key_id: ID de la clé d'authentification AWS
    :param secret_access_key: clé secrete d'authentification AWS
    :param region:  region AWS (exemple: us-west-1)
    :return: str
                * endpoint de l'API de prediction
    génère une exception si la fonction boto3 <get_export()> est KO
    """
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


def delete_clf_stack(stack_id, access_key_id, secret_access_key, region):
    """
        :param stack_id: ID unique de la pile CloudFormation
        :param access_key_id: ID de la clé d'authentification AWS
        :param secret_access_key: clé secrete d'authentification AWS
        :param region: region AWS (exemple: us-west-1)
        :return: dict
                    * resultat renvoyé par la fonction boto3 <delete_stack()>
    """
    try:
        clf_client = boto3.client('cloudformation', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                  region_name=region)
        clf_response = clf_client.delete_stack(
            StackName = stack_id
        )
        return clf_response
    except ClientError as cle:
        logging.error(f"impossible de supprimer la pile CloudFormation de deploiement! : {stack_id}")
        raise Exception(cle)



def progress_bar(i, comment):
    """
    :param i: un compteur i dans [1..N]
    :param comment: str à afficher sur la sortie standard
    :return: None
                * affiche la bare d'avancement sur la sortie standard
    """
    sys.stdout.write(f"\r|%s> {comment}" % ('='*i))
    sys.stdout.flush()


def fn_to_pickle(workdir, fun):
    """
    sauvegarde la fonction fun() dans un pickle
    :param workdir: repertoire local de travail
    :param fun: fonction de préprocessing fourni par l'utilisateur
                cette fonction sert à preparer l'entrée du modèle
    :return: str
                * chemin local vers le pickle
    """
    file_path = f"{workdir}/Dillfn"
    dill.dump(fun, open(file_path, 'wb'))
    return file_path






