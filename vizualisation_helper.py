import logging, sys, uuid, boto3
from botocore.exceptions import ClientError

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


def create_viz_clf_stack(clf_client,
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
        logging.error(f"impossible de supprimer la pile CloudFormation de visualisation! : {stack_id}")
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

def get_dashboard_name(nomenclature_object):
    """
    :param nomenclature_object: object de la classe TrainNomenclature
    :return: str
                * un nom unique pour la ressource dashboard dans CloudWatch
    """
    return nomenclature_object.get_dashboard_name()