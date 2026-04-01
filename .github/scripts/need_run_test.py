import os
import subprocess

head_commit = subprocess.check_output('git diff origin/main --name-only'.split())
files = head_commit.decode().splitlines()

need_run_test = False

for filename in files:
    if filename.startswith('.scripts/'):
        continue

    if filename == 'tasks.py':
        continue

    if filename in ['pyproject.toml', 'poetry.lock']:
        need_run_test = True
        break

    if filename.endswith('.py'):
        if filename.startswith('.github/'):
            continue
        need_run_test = True
        break

    if 'templates' in filename:
        need_run_test = True
        break

output = 'no'
if need_run_test:
    output = 'separate'
    COMMIT_SHA = os.getenv('COMMIT_SHA')
    commit_message = subprocess.check_output(f'git show -s --format=%B {COMMIT_SHA}'.split()).decode()
    if '[autoupdate]' in commit_message:
        output = 'bulk'

os.system(f'echo "has={output}" >> {os.getenv("GITHUB_OUTPUT")}')
