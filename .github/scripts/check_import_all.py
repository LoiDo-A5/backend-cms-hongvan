import os
import sys


def model_imported_correctly(app_string, folder, ignore_func=None):
    path = app_string.replace('.', '/')
    path = f'../{path}'
    if not os.path.isdir(path):  # not local app
        return True

    if os.path.isfile(os.path.join(path, f'{folder}.py')):  # models is a file
        return True

    if not os.path.isfile(os.path.join(path, f'{folder}/__init__.py')):  # models not found
        return True

    model_init_path = os.path.join(path, f'{folder}/__init__.py')
    with open(model_init_path) as f:
        model_init_content = f.read()

    import_files = model_init_content.split()
    import_files = [x for x in import_files if x]
    import_files = [x[1:] if x.startswith('.') else x for x in import_files]

    result = True
    model_files = os.scandir(os.path.join(path, folder))

    for model_file in model_files:
        if model_file.name == '__init__.py':
            continue

        if not model_file.name.endswith('.py'):  # not python file
            continue

        filename = model_file.name.split('.', 1)[0]

        if filename not in import_files:
            if not ignore_func or not ignore_func(model_file):
                print(f'::error::App {app_string} {folder} missing {model_file.name}.', file=sys.stderr)
                result = False

    return result


def get_installed_apps():
    settings_file = '../root/settings.py'
    with open(settings_file) as f:
        settings_content = f.read()

    installed_apps = settings_content.split('INSTALLED_APPS', 1)[1]
    installed_apps = installed_apps.split('[', 1)[1].split(']')[0]
    installed_apps = [x.strip(" '\n") for x in installed_apps.split(',') if x.strip()]
    return installed_apps


def check_missing(folder, ignore_func=None):
    is_missing = False
    for app in get_installed_apps():
        if not model_imported_correctly(app, folder, ignore_func=ignore_func):
            print(f'::error::App {app} {folder} is not imported correctly.', file=sys.stderr)
            is_missing = True

    if is_missing:
        sys.exit(1)
