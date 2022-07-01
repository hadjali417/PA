import boto3, dill
import pandas as pd
import random
from sklearn.model_selection import train_test_split
from sklearn import linear_model


def model_to_pickle(workdir, fun):
    file_path = f"{workdir}/modelPKL"
    dill.dump(fun, open(file_path, 'wb'))
    return file_path

def get_dataset():
  df = pd.DataFrame(columns=["age", "sex", "salaire"])
  df["age"] = [random.randint(18, 90) for i in range(1000)]
  df["sex"] = [random.randint(0, 1) for i in range(1000)]
  df["salaire"] = [random.randint(0, i*1000) for i in range(1000)]
  return df


if __name__=="__main__":
    workdir = "/appli"

    df_salaries = get_dataset()

    df_x = pd.DataFrame(df_salaries, columns=['age', 'sex'])
    df_y = pd.DataFrame(df_salaries, columns=["salaire"])

    reg_model = linear_model.LinearRegression()
    x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.2, random_state=42)

    reg_model.fit(x_train, y_train)

    model_local_path = model_to_pickle(workdir, reg_model)

    s3_client = boto3.client('s3')

    s3_client.upload_file(
        model_local_path,
        "pa-2022",
        "domaine=model/modelPKL"
    )


