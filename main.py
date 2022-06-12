from UserAwsAuth import *
from Train import *

if __name__ == "__main__":
    local_rep = "C:/Users/lounhadja/PycharmProjects/PA_TDV/repos"
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

    create_ressources_response = train_object.create_ressources(prep_env_response)

    print(create_ressources_response)

    lunch_train_response = train_object.lunch_train()



