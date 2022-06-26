import boto3

if __name__=="__main__":
    local_path = "/appli/test_pipeline.txt"
    s3_client = boto3.client('s3')
    for i in range(1000):
        continue
    with open(local_path, 'w') as f:
        f.write("test_pipeline")
    s3_client.upload_file(
        local_path,
        "pa-repository",
        "test_pipeline.txt"
    )

