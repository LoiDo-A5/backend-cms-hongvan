import os
import sys
import json

data = sys.argv

data = data[1:]
data = ' '.join(data)
data = json.loads(data)

failed_job = []
for key, value in data.items():
    if value['result'] == 'failure':
        failed_job.append(key)

failed_job_string = ', '.join(failed_job)

os.system(f'echo "result={failed_job_string}" >> {os.getenv("GITHUB_OUTPUT")}')
