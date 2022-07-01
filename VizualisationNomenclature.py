class VizualisationNomenclature:
    def __init__(self, job_id, bucket, region):
        self.job_id = job_id
        self.bucket = bucket
        self.region = region

    def get_viz_stack_name(self):
        return f"vizualisation-stack-{self.job_id}"

    def get_s3_stack_template_location(self):
        s3_key = f"domaine=repository/table=template_stack/jobid={self.job_id}/template_vizualisation_stack.json"
        s3_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
        return {
            "s3_key": s3_key,
            "s3_url": s3_url
        }

    def get_dashboard_name(self):
        return f"dashboard-{self.job_id}"
