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

@click.command()
@click.option('--format', '-f', default="text", type=click.Choice(['text', 'json'], case_sensitive=False), help='output format: text/json')
@click.argument('organization_id')
def organization(format, organization_id):
    """list all your organizations"""
    org = AutoRetouchAPIClient().get_organization(organization_id)
    if format == 'text':
        click.echo(f"{org.name}: {org.id}")
    if format == 'json':
        click.echo(json.dumps(org, indent=4))


autoretouch_cli.add_command(login)
autoretouch_cli.add_command(organizations)
autoretouch_cli.add_command(organization)
