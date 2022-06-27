from UserAwsAuth import *
from Train import *
from Deploy import *
from deployment_helper import get_api_endpoint

if __name__ == "__main__":
    #######A l'utilisateur de les declarer########
    bucket = "pa-2022"
    device_size = "2"
    region = "eu-west-3"
    instance_type = "t2.micro"
    input_model_type = "int"
    model_s3_key = "...."
    #############################################
    local_rep = "ressources"
    template_stack_local_path = f"{local_rep}/clf_train_stack.json"
    train_script_local_path = f"{local_rep}/train_script.py"
    requirements_local_path = f"{local_rep}/requirements.txt"
    train_lbd_local_path = f"{local_rep}/lambda_train.zip"

    ami = "ami-021d41cbdefc0c994"


    credential_file_path = "C:/Users/lounhadja/PycharmProjects/PA_TDV/new_user_credentials.csv"
    auth_object = UserAwsAuth(credential_file_path)
    auth_object.describe()


    ##################################################################################################
    ################################### Partie entrainement############################################
    ##################################################################################################
    train_object = Train(bucket, auth_object, template_stack_local_path, train_script_local_path,
                         requirements_local_path, train_lbd_local_path, instance_type, ami,
                         device_size, region=region)


    prep_env_response = train_object.prepare_env()

    print("[Train] creation stack...")
    create_stack_status = train_object.create_clf_stack(prep_env_response)

    print("\n[Train] lancement ec2...")
    instance_id = train_object.lunch_train_ec2()

    print(instance_id)
    print("\n[Train] installation requerements...")
    install_req_status = train_object.install_requerments(instance_id)


    install_req_status["status"] = "Success"
    if install_req_status["status"]=="Success":
        print("\n[Train] entrainement model...")
        train_status = train_object.lunch_train_script(instance_id)
        if train_status["status"] == "Success":
            print("\n========>train finished!")

    train_object.delete_resources(instance_id)

    ##################################################################################################
    ###################################Partie Deploiement############################################
    ##################################################################################################
    template_deployment_stack_local_path = f"{local_rep}/clf_deployment_stack.json"
    deployment_lbd_local_path = f"{local_rep}/lambda_deployment.zip"

    DeployObject = Deploy(bucket, model_s3_key, input_model_type, auth_object,
                          template_deployment_stack_local_path, deployment_lbd_local_path ,
                          region=region)
    print("[Deployment] prepare_env...")
    deployment_prepare_env = DeployObject.prepare_deployment()

    print("[Deployment] deploy...")
    api_url = DeployObject.deploy(deployment_prepare_env)

    print(api_url)