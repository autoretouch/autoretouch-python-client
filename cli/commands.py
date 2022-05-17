import json

import click
from api_client.client import AutoRetouchAPIClient

@click.group()
def autoretouch_cli():
    pass

@click.command()
def login():
    AutoRetouchAPIClient().login()

@click.command()
@click.option('--format', '-f', default="text", type=click.Choice(['text', 'json'], case_sensitive=False), help='output format: text/json')
def organizations(format):
    """list all your organizations"""
    orgs = AutoRetouchAPIClient().get_organizations()
    if format == 'text':
        for org in orgs:
            click.echo(f"{org.name}: {org.id}")
    if format == 'json':
        click.echo(json.dumps([o.to_dict() for o in orgs], indent=4))

autoretouch_cli.add_command(login)
autoretouch_cli.add_command(organizations)
