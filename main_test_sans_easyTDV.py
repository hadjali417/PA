from Train import *
from Deploy import *
from Vizualisation import *
from UserAwsAuth import *



def prepro_fn(input_model):
    import numpy as np
    age = float(input_model["age"])
    sex = float(input_model["sex"])
    secteur_activite = float(input_model["secteur_activite"])
    return np.array([age, sex, secteur_activite]).reshape(-1, 3)


if __name__ == "__main__":
    bucket = "pa-2022-1"
    device_size = "2"
    instance_type = "t2.medium"
    model_s3_key = "domaine=model/modelPKL"
    #############################################
    template_train_stack_local_path = "C:/Users/lounhadja/PycharmProjects/projet_annuel_tdv_git/ressources/clf_train_stack.json"
    train_lbd_local_path = "C:/Users/lounhadja/PycharmProjects/projet_annuel_tdv_git/ressources/lambda_train.zip"

    local_rep = "C:/Users/lounhadja/PycharmProjects/projet_annuel_tdv_git/ressources"
    train_script_local_path = f"{local_rep}/train_script.py"
    requirements_local_path = f"{local_rep}/requirements.txt"

    credential_file_path = "C:/Users/lounhadja/PycharmProjects/PA_TDV/new_user_credentials.csv"
    auth_object = UserAwsAuth(credential_file_path)
    auth_object.describe()

    ##################################################################################################
    ################################### Partie entrainement############################################
    ##################################################################################################
    print("===============================>[Train]<===============================")
    """train_object = Train(bucket, auth_object, template_train_stack_local_path ,train_script_local_path,
                         requirements_local_path, train_lbd_local_path, instance_type, device_size)


    prep_env_response = train_object.prepare_env()

    create_stack_status = train_object.create_clf_stack(prep_env_response)

    instance_id = train_object.lunch_train_ec2()

    install_req_status = train_object.install_requerments(instance_id)

    if install_req_status["status"]=="Success":
        train_status = train_object.lunch_train_script(instance_id)
        if train_status["status"] == "Success":
            print("\n========>train finished!")

    train_object.delete_resources(instance_id)
"""
    ##################################################################################################
    ###################################Partie Deploiement############################################
    ##################################################################################################
    print("===============================>[Deployment]<===============================")
    list_features = ["age", "sex", "secteur_activite"]
    template_deployment_stack_local_path = f"{local_rep}/clf_deployment_stack.json"
    deployment_lbd_local_path = f"{local_rep}/lambda_deployment.zip"
    dep_layer_zip_local_path = "C:/Users/lounhadja/PycharmProjects/projet_annuel_tdv_git/ressources/layers/python.zip"
    workdir = "C:/Users/lounhadja/PycharmProjects/projet_annuel_tdv_git"

    DeployObject = Deploy(bucket, model_s3_key, prepro_fn, auth_object, template_deployment_stack_local_path, deployment_lbd_local_path, dep_layer_zip_local_path, list_features, workdir)

    print("[Deployment] prepare_env...")
    deployment_prepare_env = DeployObject.prepare_deployment()

    print("[Deployment] deploy...")
    api_response = DeployObject.deploy(deployment_prepare_env)

    print(api_response)

    api_name = api_response["api_name"]

    #DeployObject.delete_resources()
    print("===============================>[Vizualisation]<===============================")
    template_viz_stack_local_path = f"{local_rep}/clf_vizualisation_stack.json"
    VizObject = Vizualisation(bucket, template_viz_stack_local_path, auth_object, api_name)

    vizualisation_prepare_env = VizObject.prepare_env()

    dashboard_name = VizObject.vizualise(vizualisation_prepare_env)

    print(dashboard_name)

    VizObject.delete_resources()




