import boto3, logging, dill
from botocore.exceptions import ClientError
import numpy as np
import sklearn

def get_file_from_s3(bucket, s3_key):
    pkl_local_path = '/tmp/pickle_object'
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket, s3_key, pkl_local_path)
    except ClientError as cle:
        logging.error(f"impossible de recuperer le pickel depuis s3: {bucket}/{s3_key}")
        logging.error(cle)
        return {
            "pkl_local_path" : None,
            "log" : cle
        }
    return {
            "pkl_local_path" : pkl_local_path,
            "log" : "recuperation pickle terminé avec succès!"
        }


def pickle_to_object(pickle_file_path):
    try:
        return {
            "object" : dill.load(open(pickle_file_path, 'rb')),
            "log" : "deserialisation terminée avec succès!"
        }
    except Exception as exp:
        return {
            "object": None,
            "log": exp
        }


def apply_prepro_fn_to_input(fn, input_model):
    try:
        return {
            "input_model_processed": fn(input_model),
            "log": "traitement input_model terminé avec succès!"
        }
    except Exception as exp:
        return {
            "input_model_processed" : None,
            "log" : exp
        }


def get_prediction(model, input_model):
    try:
        return {
            "prediction": model.predict(input_model),
            "log": "prediction terminée avec succès"
        }
    except Exception as exp:
        return {
            "prediction" : None,
            "log" : exp
        }


