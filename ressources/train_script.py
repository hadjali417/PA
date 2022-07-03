import boto3, dill, logging
import pandas as pd
import random
from botocore.exceptions import ClientError
from sklearn.model_selection import train_test_split
from sklearn import linear_model


def model_to_pickle(workdir, fun):
    file_path = f"{workdir}/modelPKL"
    dill.dump(fun, open(file_path, 'wb'))
    return file_path


def get_file_from_s3(bucket, s3_key):
    pkl_local_path = '/tmp/dataset.csv'
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket, s3_key, pkl_local_path)
    except ClientError as cle:
        logging.error(f"impossible de recuperer le dataset depuis s3: {bucket}/{s3_key}")
        logging.error(cle)
        return {
            "dataset_local_path" : None,
            "log" : cle
        }
    return {
            "dataset_local_path" : pkl_local_path,
            "log" : "recuperation dataset terminé avec succès!"
        }

def get_dataset(bucket, s3_key):
    dataset_local_path_res = get_file_from_s3(bucket, s3_key)
    dataset_local_path = dataset_local_path_res["dataset_local_path"]
    if dataset_local_path is None:
        raise Exception("dateset not found!")
    return pd.read_csv(dataset_local_path, sep='|')



if __name__=="__main__":
    workdir = "/appli"
    bucket = "pa-2022-1"
    s3_key_model = "domaine=model/modelPKL"
    s3_key_dataset = "domaine=datasets/dataset_salaries.csv"

    df_salaries = get_dataset(bucket, s3_key_dataset)

    df_x = pd.DataFrame(df_salaries, columns=['age', 'sex', 'secteur_activite'])
    df_y = pd.DataFrame(df_salaries, columns=["salaire"])

    reg_model = linear_model.LinearRegression()
    x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.2, random_state=42)

    reg_model.fit(x_train, y_train)

    model_local_path = model_to_pickle(workdir, reg_model)

    s3_client = boto3.client('s3')

    s3_client.upload_file(
        model_local_path,
        bucket,
        s3_key_model
    )


