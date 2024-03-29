from batch_client import AWSBatch
from datetime import datetime

# Instantiate client
batch = AWSBatch()

# Get existing job queues and job definitions
my_job_queues = batch.list_job_queues()
my_job_definitions = batch.list_job_definitions()

print(f"Existing Job Queues: {[j.get('jobQueueName') for j in my_job_queues]}")
print(f"Existing Job Definitions: {[j.get('jobDefinitionName') for j in my_job_definitions]}")

# Define job arguments
job_kwargs = {
    "SOURCE_AWS_S3_BUCKET": "my-bucket-source",
    "SOURCE_AWS_S3_BUCKET_FOLDER": "my-folder",
    "TARGET_AWS_S3_BUCKET": "my-bucket-target",
    "TARGET_AWS_S3_BUCKET_FOLDER": "my-folder",
    "DATA_TYPE": "spikeglx",
    # "READ_RECORDING_KWARGS": {"stream_id": "imec.ap"},
    "SORTERS": "kilosort2_5,kilosort3"
}

# Submit job
response_job = batch.submit_job(
    job_name="my-job-123", 
    job_queue=my_job_queues[0]["jobQueueName"],
    job_definition=my_job_definitions[0]["jobDefinitionName"],
    job_kwargs=job_kwargs,
    attempt_duration_seconds=7200,
)

# Check job status every 60 seconds, until succeeded
out = False
while not out:
    r = batch.describe_job(job_id=response_job["jobId"])
    status = r["status"]
    print(f"Job status: {status}")
    if status == "SUCCEEDED":
        out = True

# Get Job logs
log_events = batch.get_job_logs(job_id=response_job["jobId"])
for e in log_events:
    msg = datetime.fromtimestamp(e["timestamp"]/1000.).strftime("%d/%m/%Y, %H:%M:%S") + ' - ' + e["message"]
    print(msg)