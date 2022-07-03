import json, os
from lambda_deployment.utils import *


def lambda_handler(event, context):
    prepro_fn_s3_key = os.environ["PREPRO_FN"]
    model_s3_key = os.environ["MODEL_S3_KEY"]
    bucket = os.environ["BUCKET"]
    list_features = json.loads(os.environ["LIST_FEATURES"].replace("\'", "\""))

    if event["queryStringParameters"] is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Aucun parametre passé en entrée!...Veuillez inclure le(s) parametre(s) requis pour la prediction! : {list_features}")
        }

    input_model = event["queryStringParameters"]

    all_param_required = True
    list_param_abs = []
    for feature in list_features:
        if feature not in input_model.keys():
            all_param_required = False
            list_param_abs.append(feature)

    if all_param_required == False:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Les parametres suivants (obligatoires) sont manquants : {list_param_abs}")
        }


    ##################################### recupération fonction preprocessing #######################################
    get_fn_pickle_response = get_file_from_s3(bucket, prepro_fn_s3_key)

    pickle_fn_local_path = get_fn_pickle_response["pkl_local_path"]

    if pickle_fn_local_path is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"impossible de recuperer le pickle de la fonction de preprocessing! : {get_fn_pickle_response['log']}")
        }

    prepro_fn_response = pickle_to_object(pickle_fn_local_path)

    prepro_fn = prepro_fn_response["object"]
    if  prepro_fn is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"impossible de deserialiser pour la focntion de prediction! : {prepro_fn_response['log']}")
        }

    ##########################################recupération model ######################################################
    get_model_pickle_response = get_file_from_s3(bucket, model_s3_key)

    pickle_model_local_path = get_model_pickle_response["pkl_local_path"]

    if pickle_model_local_path is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"impossible de recuperer le pickle du modèle! : {get_model_pickle_response['log']}")
        }

    model_response = pickle_to_object(pickle_model_local_path)

    model = model_response["object"]
    if model is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"impossible de deserialiser le modèle de prediction! : {model_response['log']}")
        }


    input_model_processed_response = apply_prepro_fn_to_input(prepro_fn, input_model)

    input_model_processed = input_model_processed_response["input_model_processed"]
    if input_model_processed is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Veuillez verifier votre fonction de preprocessing...impossible d'appliquer la fonction à l'input du modèle! : {input_model_processed_response['log']}")
        }


    prediction_response = get_prediction(model, input_model_processed)

    prediction = prediction_response["prediction"]

    if prediction is None:
        return {
            'statusCode': 400,
            'body': json.dumps(f"prédiction impossible! : { prediction_response['log']}")
        }

    return {
        'statusCode': 200,
        'body': str(prediction)
    }