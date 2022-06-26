import boto3, logging, time
from botocore.exceptions import ClientError
from TrainNomenclature import *
from train_helper import generate_job_id, upload_file_to_s3, create_train_clf_stack, progress_bar, get_ec2_instance_id, get_train_ec2_instance_status, run_ec2_command, get_command_status


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
        self.nomenclature_object = TrainNomenclature(self.job_id, self.bucket, self.region)


    def prepare_env(self):
        """
        charger les fichiers: train.py, requirements.txt, stack_template.json et lbd_train.py vers S3
        :return: les keys S3 des fichiers chargés vers S3
        """
        s3_client = boto3.client('s3', aws_access_key_id=self.access_key_id,
                                 aws_secret_access_key=self.secret_access_key, region_name=self.region)
        s3_lbd_location = self.nomenclature_object.get_s3_lbd_location()
        s3_train_script_location = self.nomenclature_object.get_s3_train_script_location()
        s3_requirements_location = self.nomenclature_object.get_s3_requirements_location()
        s3_stack_template_location = self.nomenclature_object.get_s3_stack_template_location()
        try:
            upload_file_to_s3(s3_client, self.train_lbd_local_path, self.bucket, s3_lbd_location)
            upload_file_to_s3(s3_client, self.train_script_local_path, self.bucket, s3_train_script_location)
            upload_file_to_s3(s3_client, self.requirements_local_path, self.bucket, s3_requirements_location)
            upload_file_to_s3(s3_client, self.template_stack_local_path, self.bucket, s3_stack_template_location["s3_key"])
        except ClientError as cle:
            logging.error("[TRAIN]:preparation d'enveronement echouée...")
            raise Exception(cle)
        return {
            "s3_lbd_key": s3_lbd_location,
            "s3_train_script_key": s3_train_script_location,
            "s3_requirements_key": s3_requirements_location,
            "url_s3_stack_template": s3_stack_template_location["s3_url"]
        }


    def create_clf_stack(self, prepare_env_response, invoke_mode=0):
        """
        :param prepare_env_response: l'objet retourné par prepare_env()
        :return:
        """
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")
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
                'ParameterKey': 'JobID',
                'ParameterValue': self.job_id
            },
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
            clf_client = boto3.client('cloudformation', aws_access_key_id=self.access_key_id,
                                      aws_secret_access_key=self.secret_access_key, region_name=self.region)
            stack_id = create_train_clf_stack(clf_client, stack_name, url_s3_stack_template, list_parameters)
            if invoke_mode==0:
                quit = True
                iter = 1
                while(quit):
                    time.sleep(2)
                    clf_stack_status = self.get_clf_stack_status(stack_name)
                    if clf_stack_status == 'CREATE_COMPLETE':
                        logging.info(f"[TRAIN]:statut creation CloudFormation: {clf_stack_status}")
                        return clf_stack_status
                    elif clf_stack_status == 'CREATE_IN_PROGRESS':
                        progress_bar(iter)
                        iter+=1
                    else:
                        logging.error(f"[TRAIN]:statut creation CloudFormation: {clf_stack_status}")
                        raise Exception("[TRAIN]:Creation stack CloudFormation echoué")
            if invoke_mode==1:
                create_ressources_response = {}
                create_ressources_response['StackId'] = stack_id
                create_ressources_response['StackName'] = stack_name
                return create_ressources_response
        except ClientError as cle:
            logging.error(f"[TRAIN]:creation ressources echouée!")
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
            logging.error(f"[TRAIN]:impossible d'obtenir le statut pour la stack: {stack_name}")
            raise Exception(cle)


    def lunch_train_ec2(self, invoke_mode=0):
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")

        lbd_client = boto3.client('lambda', aws_access_key_id=self.access_key_id,
                                  aws_secret_access_key=self.secret_access_key, region_name=self.region)
        lbd_train_name = self.nomenclature_object.get_lbd_train_name()
        try:
            invoke_lbd_response = lbd_client.invoke(
                FunctionName=lbd_train_name,
                InvocationType='RequestResponse'
            )
            instance_id = get_ec2_instance_id(self.job_id, self.access_key_id, self.secret_access_key, self.region)
            if invoke_mode==1:
                return instance_id
            if invoke_mode==0:
                iter=1
                while(True):
                    time.sleep(2)
                    instance_status = get_train_ec2_instance_status(instance_id, self.access_key_id, self.secret_access_key, self.region)
                    if instance_status == 'running':
                        return instance_status
                    elif instance_status == 'pending':
                        progress_bar(iter)
                        iter+=1
                    else:
                        raise Exception(f"status de l'instance d'entrainement en erreur : {instance_status}")
        except ClientError as cle:
            logging.error("impossible de lancer l'instance d'entrainement!")
            raise Exception(cle)


    def install_requerments(self, invoke_mode=0):
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")
        requirements_file_name = "requirements.txt"
        instance_id = get_ec2_instance_id(self.job_id, self.access_key_id, self.secret_access_key, self.region)
        commands = [f"pip3.8 install -r /appli/{requirements_file_name}"]
        cmd_exec_response = run_ec2_command(instance_id, commands, self.access_key_id, self.secret_access_key,
                                            self.region)
        if invoke_mode == 1:
            return cmd_exec_response
        command_id = cmd_exec_response['Command']['CommandId']
        iter = 0
        while(True):
            time.sleep(2)
            cmd_status = get_command_status(instance_id, command_id, self.access_key_id, self.secret_access_key, self.region)
            if cmd_status["status"] == "Success":
                return cmd_status
            if cmd_status["status"] in ['Pending', 'InProgress', 'Delayed']:
                progress_bar(iter)
                iter+=1
                continue
            return {
                "status" : "failed",
                "status_details" : cmd_status["status_details"]
            }

    def lunch_train_script(self, invoke_mode=0):
        if invoke_mode not in [0, 1]:
            raise Exception("valeurs acceptées pour invoke_mode: [0:synchrone, 1: asynchrone]")

        train_script_name = "train_script.py"
        instance_id = get_ec2_instance_id(self.job_id, self.access_key_id, self.secret_access_key, self.region)
        commands = [f"sudo python3.8 /appli/{train_script_name}"]
        cmd_exec_response = run_ec2_command(instance_id, commands, self.access_key_id, self.secret_access_key,
                                            self.region)

        if invoke_mode == 1:
            return cmd_exec_response
        command_id = cmd_exec_response['Command']['CommandId']
        iter = 0
        while (True):
            time.sleep(2)
            cmd_status = get_command_status(instance_id, command_id, self.access_key_id, self.secret_access_key,
                                            self.region)
            if cmd_status["status"] == "Success":
                return cmd_status
            if cmd_status["status"] in ['Pending', 'InProgress', 'Delayed']:
                progress_bar(iter)
                iter += 1
                continue
            return {
                "status": "failed",
                "status_details": cmd_status["status_details"]
            }





