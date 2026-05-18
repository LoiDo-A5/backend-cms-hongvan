import os
import sys
from uuid import uuid4

from invoke import Exit
from invoke import task

BASE_DIR = os.path.dirname(__file__)


def command_ready(c, command):
    print(f'check command "{command}"')
    try:
        c.run(f'which {command}')
        return True
    except Exception:
        return False


@task
def deploy(c):
    update_deployment(c)


@task
def green_migrate(c):
    deploy_name, output = run_single_command(
        c, 'python manage.py green_migrate > green_migrate_output.json', delete=False,
    )
    run_single_command(c, 'ls', delete=False, deploy_name=deploy_name)
    run_single_command(c, 'pwd', delete=False, deploy_name=deploy_name)
    run_single_command(c, 'python manage.py migrate', delete=False, deploy_name=deploy_name)
    with open('green_migrate_output.json', 'w') as f:
        f.write(deploy_name)


@task
def pos_green_migrate(c):
    with open('green_migrate_output.json') as f:
        deploy_name = f.read().strip()
    run_single_command(
        c, 'python manage.py pos_green_migrate green_migrate_output.json', deploy_name=deploy_name, delete=True,
    )


@task
def run_single_command(c, command, filename='migration.temp.yaml', delete=True, deploy_name=None):
    print(command)
    if not deploy_name:
        random_hash = uuid4().hex
        deploy_name = f'temp-{random_hash}'

        migration_yaml = os.path.join(BASE_DIR, 'deploy/kubernetes', filename)
        c.run(f"HOSTNAME='$HOSTNAME' DEPLOY_NAME='{deploy_name}' envsubst < {migration_yaml} > /tmp/{filename}")
        c.run(f'cat /tmp/{filename}')
        c.run(f'kubectl apply -f /tmp/{filename}')
        c.run(f'kubectl rollout status -w --timeout=120s deployment {deploy_name}')

    pod_name = c.run(f'kubectl get pod | grep {deploy_name} | head -n 1').stdout.split()[0]

    error = False
    try:
        output = c.run(f"kubectl exec -i {pod_name} -- bash -c '{command}'").stdout
    except Exception as ex:
        print(ex)
        error = True
        output = ''

    if delete:
        c.run(f'kubectl delete deploy/{deploy_name}')
    if error:
        sys.exit(1)
    return deploy_name, output


@task
def clean_temp(c):
    deployments = c.run('kubectl get deploy')
    for line in deployments.stdout.splitlines():
        deployment = line.split()[0]
        if deployment.startswith('temp-'):
            c.run(f'kubectl delete deploy {deployment}')


def should_ignore_kubernetes_file(filename: str):
    if filename.endswith('.temp.yaml'):
        return True

    if filename.count('.') == 2 and not filename.endswith(f'.{os.getenv("ENVIRONMENT_NAME")}.yaml'):
        return True

    return False


def make_yaml_file(c, config_dir_path, filename):
    file_path = os.path.join(config_dir_path, filename)
    if not os.path.isfile(file_path):
        return

    print(f'Preparing yaml file {file_path}')
    c.run(f"HOSTNAME='$HOSTNAME' envsubst < {file_path} > /tmp/{filename}")
    c.run(f'cat /tmp/{filename}')


@task
def update_deployment(c):
    config_dir = 'deploy/kubernetes'
    config_dir_path = os.path.join(BASE_DIR, config_dir)
    files = os.listdir(config_dir_path)
    files = sorted(files)
    files = [x for x in files if not should_ignore_kubernetes_file(x)]

    c.run(f'echo "Will update development {len(files)} files"')

    for filename in files:
        make_yaml_file(c, config_dir_path=config_dir_path, filename=filename)

    for index, filename in enumerate(files):
        c.run(f'echo "# {index + 1}. {filename}" >> /tmp/sum_deploy.yaml')
        c.run(f'cat /tmp/{filename} >> /tmp/sum_deploy.yaml')
        c.run('echo "" >> /tmp/sum_deploy.yaml')
        c.run('echo "---" >> /tmp/sum_deploy.yaml')
        c.run('echo "" >> /tmp/sum_deploy.yaml')

    c.run('echo "Proceed kubectl apply"')
    c.run('cat /tmp/sum_deploy.yaml')
    c.run('kubectl apply -f /tmp/sum_deploy.yaml --request-timeout 3m')
    apply_output = c.run('kubectl apply -f /tmp/sum_deploy.yaml --request-timeout 3m')
    with open('apply_output.txt', 'w') as f:
        f.write(apply_output.stdout)


@task
def wait_for_deploy(c, timeout=1200):
    with open('apply_output.txt') as f:
        apply_output = f.read()
    apply_lines = apply_output.splitlines()
    deploy_lines = [x for x in apply_lines if 'deployment.apps/' in x]
    deployments = [x.split(' ')[0].split('/')[1] for x in deploy_lines]

    for deployment in deployments:
        result = c.run(f'kubectl rollout status -w --timeout={timeout}s deployment {deployment}')

        if not result.ok:
            raise Exit(code=1)
