import boto3, uuid, sys, time
from botocore.exceptions import ClientError
import logging


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


def create_train_clf_stack(clf_client,
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


def run_ec2_command(instance_id, commands, aws_access_key_id, aws_secret_access_key, region):
    """
    :param instance_id: ID unique de l'instance d'entrainement
    :param commands: liste de commandes shell sous format str
    :param aws_access_key_id: ID de la clé d'authentification AWS
    :param aws_secret_access_key:  clé secrete d'authentification AWS
    :param region: region AWS (exemple: us-west-1)
    :return: dict
                * reponse renvoyée par le client SSM lors du lancement des cmd ssh
    génère une exception si le ancement des cmd ssh est KO
    """
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
    """
    :param instance_id: ID unique de l'instance d'entrainement
    :param command_id: ID unique de la commande shell executée sur l'instance d'entrainement
    :param aws_access_key_id: ID de la clé d'authentification AWS
    :param aws_secret_access_key: clé secrete d'authentification AWS
    :param region: region AWS (exemple: us-west-1)
    :return: dict
                * status: statut de la commande
                * status_details: details sur le statut de la commade
    """
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


def get_train_ec2_instance_status(instance_id, access_key_id, secret_access_key, region):
    """
    :param instance_id: ID unique de l'instance d'entrainement
    :param access_key_id: ID de la clé d'authentification AWS
    :param secret_access_key: clé secrete d'authentification AWS
    :param region: region AWS (exemple: us-west-1)
    :return: str
                * le statut de l'instance d'entrainement
    """
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


def terminate_instance(instance_id, access_key_id, secret_access_key, region):
    """
    :param instance_id: ID unique de l'instance d'entrainement
    :param access_key_id: ID de la clé d'authentification AWS
    :param secret_access_key: clé secrete d'authentification AWS
    :param region: region AWS (exemple: us-west-1)
    :return: dict
                * resultat renvoyé par la fonction boto3 <terminate_instances()>
    """
    try:
        ec2_client = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                      region_name=region)
        client_response = ec2_client.terminate_instances(
            InstanceIds=[
                instance_id
            ]
        )
        return client_response
    except ClientError as cle:
        logging.error(f"impossible d'arreter l'instance d'entrainement! : {instance_id}")
        raise Exception(cle)


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
        logging.error(f"impossible de supprimer la pile CloudFormation d'entrainement! : {stack_id}")
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






