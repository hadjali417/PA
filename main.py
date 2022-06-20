from UserAwsAuth import *
from Train import *
from train_helper import run_ec2_command
import time, sys
from tqdm import tqdm

def progress_bar(i):
    sys.stdout.write("\r|%s>" % ('='*i))
    sys.stdout.flush()

if __name__ == "__main__":
    local_rep = "ressources"
    bucket = "pa-2022"
    template_stack_local_path = f"{local_rep}/clf_train_stack.json"
    train_script_local_path = f"{local_rep}/train_script.py"
    requirements_local_path = f"{local_rep}/requirements.txt"
    train_lbd_local_path = f"{local_rep}/lambda_train.zip"
    instance_type = "t2.micro"
    ami = "ami-021d41cbdefc0c994"
    device_size = "2"
    region = "eu-west-3"

    credential_file_path = "C:/Users/lounhadja/PycharmProjects/PA_TDV/new_user_credentials.csv"
    auth_object = UserAwsAuth(credential_file_path)
    auth_object.describe()

    train_object = Train(bucket, auth_object, template_stack_local_path, train_script_local_path,
                         requirements_local_path, train_lbd_local_path, instance_type, ami,
                         device_size, region=region)


    prep_env_response = train_object.prepare_env()

    print("creation stack...")
    create_stack_status = train_object.create_clf_stack(prep_env_response)

    print("\nlancement ec2...")
    train_ec2_status = train_object.lunch_train_ec2()

    print("\ninstallation requerements...")
    install_req_status = train_object.install_requerments()


    install_req_status["status"] = "Success"
    if install_req_status["status"]=="Success":
        print("\nentrainement model...")
        train_status = train_object.lunch_train_script()
        if train_status["status"] == "Success":
            print("\n========>train finished!")







    #train_instance_id = get_ec2_instance_id(job_id, access_key_id, secret_access_key, region)



