import json
import click
from uuid import UUID

from api_client.client import AutoRetouchAPIClient


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
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
@click.argument('organization_id')
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


@click.command()
def balance():
    """show your current balance"""
    click.echo(AutoRetouchAPIClient().get_balance())


autoretouch_cli.add_command(login)
autoretouch_cli.add_command(logout)
autoretouch_cli.add_command(organizations)
autoretouch_cli.add_command(organization)
autoretouch_cli.add_command(upload)
autoretouch_cli.add_command(balance)
