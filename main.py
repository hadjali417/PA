from easyTDV import UserAwsAuth as Ath
from easyTDV import Train as T
from easyTDV import Deploy as D


if __name__ == "__main__":
    bucket = "pa-2022"
    device_size = "2"
    instance_type = "t2.micro"
    input_model_type = "int"
    model_s3_key = "...."
    #############################################

    local_rep = "C:/Users/lounhadja/PycharmProjects/PA_TDV/test_pip_easyTDV2/mes_scripts"
    train_script_local_path = f"{local_rep}/train_script.py"
    requirements_local_path = f"{local_rep}/requirements.txt"

    credential_file_path = "C:/Users/lounhadja/PycharmProjects/PA_TDV/new_user_credentials.csv"
    auth_object = Ath.UserAwsAuth(credential_file_path)
    auth_object.describe()

    ##################################################################################################
    ################################### Partie entrainement############################################
    ##################################################################################################
    train_object = T.Train(bucket, auth_object, train_script_local_path,
                         requirements_local_path, instance_type, device_size)


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

    DeployObject = D.Deploy(bucket, model_s3_key, input_model_type, auth_object)

    print("[Deployment] prepare_env...")
    deployment_prepare_env = DeployObject.prepare_deployment()

    print("[Deployment] deploy...")
    api_url = DeployObject.deploy(deployment_prepare_env)

    print(api_url)



