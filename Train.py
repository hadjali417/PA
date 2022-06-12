import boto3, logging
from Nomenclature import *
from train_helper import generate_job_id, upload_file_to_s3, create_train_clf_stack

#version git
class Train:
    def __init__(self,
                 bucket,
                 auth_object,
                 template_stack_local_path,
                 train_script_local_path,
                 requirements_local_path,
                 train_lbd_local_path,
                 instance_type,
                 ami,
                 device_size,
                 region=None
                 ):
        self.bucket = bucket
        self.template_stack_local_path = template_stack_local_path
        self.train_script_local_path = train_script_local_path
        self.requirements_local_path = requirements_local_path
        self.train_lbd_local_path = train_lbd_local_path
        self.instance_type = instance_type
        self.ami = ami
        self.device_size = device_size
        self.region = region
        self.access_key_id = auth_object.secret_key_id
        self.secret_access_key = auth_object.secret_access_key
        self.job_id = generate_job_id()
        self.nomenclature_object = Nomenclature(self.job_id, self.bucket, self.region)

    def prepare_env(self):
        s3_client = boto3.client('s3', aws_access_key_id = self.access_key_id, aws_secret_access_key = self.secret_access_key, region_name = self.region)
        s3_lbd_location = self.nomenclature_object.get_s3_lbd_location()
        s3_train_script_location = self.nomenclature_object.get_s3_train_script_location()
        s3_requirements_location = self.nomenclature_object.get_s3_requirements_location()
        s3_stack_template_location = self.nomenclature_object.get_s3_stack_template_location()
        upload_file_to_s3(s3_client, self.train_lbd_local_path, self.bucket, s3_lbd_location)
        upload_file_to_s3(s3_client, self.train_script_local_path, self.bucket, s3_train_script_location)
        upload_file_to_s3(s3_client, self.requirements_local_path, self.bucket, s3_requirements_location)
        upload_file_to_s3(s3_client, self.template_stack_local_path, self.bucket, s3_stack_template_location["s3_key"])
        return {
            "s3_lbd_key": s3_lbd_location,
            "s3_train_script_key": s3_train_script_location,
            "s3_requirements_key": s3_requirements_location,
            "url_s3_stack_template": s3_stack_template_location["s3_url"]
        }

    def create_ressources(self, prepare_env_response):
        s3_lbd_key = prepare_env_response["s3_lbd_key"]
        s3_train_script_key = prepare_env_response["s3_train_script_key"]
        s3_requirements_key = prepare_env_response["s3_requirements_key"]
        url_s3_stack_template = prepare_env_response["url_s3_stack_template"]

        stack_name = self.nomenclature_object.get_train_stack_name()
        lbd_train_name = self.nomenclature_object.get_lbd_train_name()
        role_train_name = self.nomenclature_object.get_role_train_name()
        profil_iam_name = self.nomenclature_object.get_profil_iam_name()

        list_parameters = [
            {
                'ParameterKey': 'LbdTrainNameParameter',
                'ParameterValue': lbd_train_name
            },
            {
                'ParameterKey': 'InstanceProfilNameParameter',
                'ParameterValue': profil_iam_name
            },
            {
                'ParameterKey': 'RoleTrainNameParameter',
                'ParameterValue': role_train_name
            },
            {
                'ParameterKey': 'S3BucketParameter',
                'ParameterValue': self.bucket
            },
            {
                'ParameterKey': 'S3KeyParameter',
                'ParameterValue': s3_lbd_key
            },
            {
                'ParameterKey': 'InstanceTypeParameter',
                'ParameterValue': self.instance_type
            },
            {
                'ParameterKey': 'AmiParameter',
                'ParameterValue': self.ami
            },
            {
                'ParameterKey': 'regionParameter',
                'ParameterValue': self.region
            },
            {
                'ParameterKey': 'TrainScriptKeyParameter',
                'ParameterValue': s3_train_script_key
            },
            {
                'ParameterKey': 'RequirementScriptKeyParameter',
                'ParameterValue': s3_requirements_key
            },
            {
                'ParameterKey': 'DeviceSizeParameter',
                'ParameterValue': self.device_size
            }
        ]
        try:
            clf_client = boto3.client('cloudformation', aws_access_key_id = self.access_key_id, aws_secret_access_key = self.secret_access_key, region_name = self.region)
            create_ressources_response = {}
            stack_id = create_train_clf_stack(clf_client, stack_name, url_s3_stack_template, list_parameters)
            create_ressources_response['StackId'] = stack_id
            create_ressources_response['StackName'] = stack_name
            return create_ressources_response
        except Exception as exp:
            logging.error(f"creation ressources echouée! {exp}")
            return None


    def lunch_train(self):
        lbd_client = boto3.client('lambda', aws_access_key_id=self.access_key_id,
                                  aws_secret_access_key=self.secret_access_key, region_name = self.region)
        lbd_train_name = self.nomenclature_object.get_lbd_train_name()
        invoke_lbd_response = lbd_client.invoke(
                                        FunctionName=lbd_train_name,
                                        InvocationType='RequestResponse'
                              )
        return invoke_lbd_response

    def get_advencement(self):
        pass

