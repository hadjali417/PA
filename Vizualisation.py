import boto3, logging, time
from VizualisationNomenclature import *
from vizualisation_helper import create_viz_clf_stack, upload_file_to_s3, progress_bar, get_dashboard_name, generate_job_id
from botocore.exceptions import ClientError


"""
Classe python pour la création de resossources necessaires pour la cr
"""
class Vizualisation:
    def __init__(self,
                 bucket : str,
                 template_stack_local_path: str,
                 auth_object,
                 api_name: str,
                 region = "us-west-1"):
        self.bucket = bucket
        self.job_id = generate_job_id()
        self.template_stack_local_path = template_stack_local_path
        self.region = region
        self.access_key_id = auth_object.secret_key_id
        self.secret_access_key = auth_object.secret_access_key
        self.nomenclature_object = VizualisationNomenclature(self.job_id, self.bucket, self.region)
        self.api_name = api_name

    def prepare_env(self):
        s3_client = boto3.client('s3', aws_access_key_id=self.access_key_id,
                                 aws_secret_access_key=self.secret_access_key, region_name=self.region)

        s3_stack_template_location = self.nomenclature_object.get_s3_stack_template_location()
        try:
            upload_file_to_s3(s3_client, self.template_stack_local_path, self.bucket, s3_stack_template_location["s3_key"])
        except ClientError as cle:
            logging.error("[VIZUALISATION]:preparation d'enveronement echouée...")
            raise Exception(cle)
        return {
            "url_s3_stack_template": s3_stack_template_location["s3_url"]
        }


    def create_stack(self, prepare_env_response, invoke_mode=0):
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")

        url_s3_stack_template = prepare_env_response["url_s3_stack_template"]
        viz_stack_name = self.nomenclature_object.get_viz_stack_name()
        dashboard_name = self.nomenclature_object.get_dashboard_name()
        list_parameters = [
            {
                'ParameterKey': 'DashboardNameParameter',
                'ParameterValue': dashboard_name
            },
            {
                'ParameterKey': 'APINameParameter',
                'ParameterValue': self.api_name
            }
        ]
        try:
            clf_client = boto3.client('cloudformation', aws_access_key_id=self.access_key_id,
                                      aws_secret_access_key=self.secret_access_key, region_name=self.region)

            stack_id = create_viz_clf_stack(clf_client, viz_stack_name, url_s3_stack_template, list_parameters)
            if invoke_mode==1:
                create_ressources_response = {}
                create_ressources_response['StackId'] = stack_id
                create_ressources_response['StackName'] = viz_stack_name
                return create_ressources_response
            if invoke_mode==0:
                quit = True
                iter = 1
                while(quit):
                    time.sleep(2)
                    clf_stack_status = self.get_clf_stack_status(viz_stack_name)
                    if clf_stack_status == 'CREATE_COMPLETE':
                        logging.info(f"[VIZUALISATION]:statut creation CloudFormation: {clf_stack_status}")
                        return clf_stack_status
                    elif clf_stack_status == 'CREATE_IN_PROGRESS':
                        progress_bar(iter, "Vizualization...")
                        iter+=1
                    else:
                        logging.error(f"[VIZUALISATION]:statut creation CloudFormation: {clf_stack_status}")
                        raise Exception("Creation stack CloudFormation echoué")

        except ClientError as cle:
            logging.error(f"[VIZUALISATION]:creation ressources echouée!")
            raise Exception(cle)


    def get_clf_stack_status(self, stack_name):
        """
        :param stack_name: le nom de la stack CloudFormation
        :return: le status en cours
        """
        clf_client = boto3.client('cloudformation', aws_access_key_id=self.access_key_id,
                                  aws_secret_access_key=self.secret_access_key, region_name=self.region)

        try:
            clf_response = clf_client.describe_stacks(
                StackName=stack_name
            )
            return clf_response['Stacks'][0]['StackStatus']
        except ClientError as cle:
            logging.error(f"[VIZUALISATION]:impossible d'obtenir le statut pour la stack: {stack_name}")
            raise Exception(cle)


    def vizualise(self, prepare_env_response, invoke_mode=0):
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")
        self.create_stack(prepare_env_response, invoke_mode)
        return get_dashboard_name(self.nomenclature_object)



