
class DeploymentNomenclature:
    def __init__(self, job_id, bucket, region):
        self.job_id = job_id
        self.bucket = bucket
        self.region = region

    def get_s3_lbd_location(self):
        return f"domaine=repository/table=lambda-deployment/jobid={self.job_id}/lambda_deployment.zip"

    def get_s3_model_location(self):
        pass

    def get_lbd_deployment_name(self):
        return f"lbd-request-processor-{self.job_id}"

    def get_api_name(self):
        return f"api-predection-{self.job_id}"

    def get_deployment_stack_name(self):
        return f"deployment-stack-{self.job_id}"

    def get_role_deployment_name(self):
        return f"Deployment-Role-{self.job_id}"

    def get_s3_stack_template_location(self):
        s3_key = f"domaine=repository/table=template_stack/jobid={self.job_id}/template_deployment_stack.json"
        s3_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
        return {
            "s3_key": s3_key,
            "s3_url": s3_url
        }

    def get_s3_prepro_fn_location(self):
        return f"domaine=repository/table=preprocessing_fn/jobid={self.job_id}/Dillfn"

    def get_S3_dill_zip_location(self):
        return f"domaine=repository/table=layers/jobid={self.job_id}/layer.zip"


