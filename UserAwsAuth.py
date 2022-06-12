import logging
import pandas

class UserAwsAuth:
    def __init__(self, user_credential_file_path, sep_ = None, secret_key_id_col_name = None, secret_access_key_col_name = None):
        self.user_credential_file_path = user_credential_file_path
        credetial = self.get_credential(user_credential_file_path, secret_key_id_col_name, secret_access_key_col_name, sep_)
        if credetial is not None:
            self.secret_key_id = credetial[0]
            self.secret_access_key = credetial[1]
        else:
            self.secret_key_id = None
            self.secret_access_key = None



    def describe(self):
        print(self.secret_key_id, self.secret_access_key)


    def get_credential(self, user_credential_file_path, secret_key_id_col_name, secret_access_key_col_name, sep_):
        if secret_key_id_col_name is None:
            secret_key_id_col_name = "Access key ID"
        if secret_access_key_col_name is None:
            secret_access_key_col_name = "Secret access key"
        if sep_ is None:
            sep_ = ','
        try:
            df_credential = pandas.read_csv(user_credential_file_path, sep=sep_)
            if df_credential.shape[0]==0:
                logging.error("le ficier creatial spécifié est vide!")
                return None
            secret_key_id = df_credential[secret_key_id_col_name][0]
            secret_access_key = df_credential[secret_access_key_col_name][0]
            return secret_key_id, secret_access_key
        except Exception as exp:
            logging.error(f"get credential failed! {exp}")
            return None

