class Nomenclature:
    def __init__(self, job_id, bucket, region):
        self.job_id = job_id
        self.bucket = bucket
        self.region = region

    def get_s3_lbd_location(self):
        return f"domaine=repository/table=lambda-train/jobid={self.job_id}/lambda_train.zip"

    def get_s3_train_script_location(self):
        return f"domaine=repository/table=train-script/jobid={self.job_id}/train_script.py"

    def get_s3_requirements_location(self):
        return f"domaine=repository/table=requirements/jobid={self.job_id}/requirements.txt"

    def get_s3_stack_template_location(self):
        s3_key = f"domaine=repository/table=template_stack/jobid={self.job_id}/template_train_stack.json"
        s3_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
        return {
            "s3_key": s3_key,
            "s3_url": s3_url
        }

    def get_train_stack_name(self):
        return f"train-stack-{self.job_id}"

    def get_lbd_train_name(self):
        return f"lbd-train-model-{self.job_id}"

    def get_role_train_name(self):
        return f"Train-Role-{self.job_id}"

    def get_profil_iam_name(self):
        return f"Train-profil-iam-{self.job_id}"

