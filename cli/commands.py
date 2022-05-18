import json
import os
from typing import Optional

import click
from uuid import UUID
from api_client.client import AutoRetouchAPIClient, USER_CONFIG, USER_CONFIG_PATH


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)


@click.group()
def autoretouch_cli():
    pass


@click.command()
def login():
    """
    create/fetch credentials from the environment variables
        - AUTORETOUCH_REFRESH_TOKEN
        or
        - AUTORETOUCH_CREDENTIALS_PATH (default = home/.config/autoretouch-credentials.json)
    or trigger Auth0 device flow if none of the above are set and store the obtained credentials
    in AUTORETOUCH_CREDENTIALS_PATH
    """
    AutoRetouchAPIClient().login()


@click.command()
def logout():
    """
    revoke and remove stored refresh token from disk
    """
    AutoRetouchAPIClient().revoke().logout()


@click.command()
def show_config():
    """
    print the name and id of your currently used organization
    """
    for key, value in USER_CONFIG.items():
        click.echo(key)
        for k, v in value.items():
            click.echo(f"\t{k}: {v}")


def autocomplete_user_organizations(ctx, param, incomplete):
    return [str(k.id) for k in AutoRetouchAPIClient().get_organizations() if k.name.startswith(incomplete)]


def autocomplete_user_workflows(ctx, param, incomplete):
    return [str(k.id) for k in AutoRetouchAPIClient().get_workflows() if k.name.startswith(incomplete)]


@click.command()
@click.option("--organization-id", "-o", default=None, shell_complete=autocomplete_user_organizations)
@click.option("--workflow-id", "-w", default=None, shell_complete=autocomplete_user_workflows)
def use(organization_id, workflow_id):
    client = AutoRetouchAPIClient()
    if organization_id is not None:
        org = client.get_organization(organization_id)
        new_org = {"organization": {"name": org.name, "id": org.id}}
    else:
        new_org = {"organization": USER_CONFIG["organization"]}
    if workflow_id is not None:
        wf = client.get_workflow(workflow_id)
        new_wf = {"workflow": {"name": wf.name, "id": wf.id}}
    else:
        new_wf = {"workflow": USER_CONFIG["workflow"]}
    new_config = {**new_org, **new_wf}
    with open(USER_CONFIG_PATH, "w") as f:
        f.write(json.dumps(new_config, cls=UUIDEncoder))


@click.command()
@click.option('--format', '-f', default="text", type=click.Choice(['text', 'json'], case_sensitive=False), help='output format: text/json')
def organizations(format):
    """list all your organizations"""
    orgs = AutoRetouchAPIClient().get_organizations()
    if format == 'text':
        for org in orgs:
            click.echo(f"{org.name}: {org.id}")
    if format == 'json':
        click.echo(json.dumps([o.to_dict() for o in orgs], indent=4, cls=UUIDEncoder))


@click.command()
@click.option('--format', '-f', default="text", type=click.Choice(['text', 'json'], case_sensitive=False), help='output format: text/json')
@click.argument('organization_id', shell_complete=autocomplete_user_organizations)
def organization(format, organization_id):
    """show details of given organization"""
    org = AutoRetouchAPIClient().get_organization(organization_id)
    if format == 'text':
        click.echo(f"{org.name}: {org.id}")
    if format == 'json':
        click.echo(json.dumps(org, indent=4))


@click.command()
@click.argument('files', type=click.File('rb'), nargs=-1)
def upload(files):
    """upload an image from disk"""
    client = AutoRetouchAPIClient()
    for file in files:
        click.echo(f"{file.name} is uploaded as {client.upload_image_from_stream(file)}")


@click.command("balance")
def balance():
    """show your current balance"""
    click.echo(AutoRetouchAPIClient().get_balance())


@click.command()
@click.argument('input', type=click.Path(exists=True), required=True)
@click.argument('output', type=click.Path(exists=True), required=True)
@click.option('--workflow-id', '-w', required=False, shell_complete=autocomplete_user_workflows)
@click.option('--yes', '-y', required=False, is_flag=True, help="skip confirmation")
def process(input: str, output: str, workflow_id: Optional[UUID], yes: bool = False):
    """process an image or a folder of images and wait for the result

    INPUT: path of image file or folder of image files.
    OUTPUT: destination folder for processed image(s).
    """
    client = AutoRetouchAPIClient()
    if os.path.isfile(input):
        client.process_image(input, output, workflow_id=workflow_id)
    else:
        images = client.get_processable_image_files(input)
        if not yes:
            click.confirm(f"Are you sure you want to process {len(images)} images?", abort=True)
        click.echo(f"Uploading and processing {len(images)} images ...")
        client.process_folder(input, output, workflow_id=workflow_id)
    click.echo("done")


@click.command()
def workflows():
    client = AutoRetouchAPIClient()
    workflows = client.get_workflows()
    for workflow in workflows:
        click.echo(f"{workflow.name}: {workflow.id}")


autoretouch_cli.add_command(login)
autoretouch_cli.add_command(logout)
autoretouch_cli.add_command(organizations)
autoretouch_cli.add_command(organization)
autoretouch_cli.add_command(show_config)
autoretouch_cli.add_command(use)
autoretouch_cli.add_command(upload)
autoretouch_cli.add_command(balance)
autoretouch_cli.add_command(process)
autoretouch_cli.add_command(workflows)
