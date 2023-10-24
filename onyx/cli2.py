import os
import csv
import sys
import stat
import enum
import json
import click
import typer
from typer.core import TyperGroup
import requests
import dataclasses
from typing import Optional, List
from .version import __version__
from .utils import print_response
from .config import OnyxConfig
from .api import OnyxClient


class DefinedOrderGroup(TyperGroup):
    def list_commands(self, ctx):
        return self.commands.keys()


app = typer.Typer(
    cls=DefinedOrderGroup,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


def show_error(response):
    try:
        detail = response.json().get("messages", {}).get("detail")
        if detail:
            raise click.exceptions.ClickException(detail)

    except json.decoder.JSONDecodeError:
        pass
    print_response(response)


@app.command()
def init(context: typer.Context):
    """
    Create a config file.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    if not context.obj.config.domain:
        context.obj.config.domain = typer.prompt("Please enter a domain")

    with open(context.obj.config.config_path, "w") as config_file:
        json.dump(
            {
                "domain": context.obj.config.domain,
                "token": context.obj.config.token,
            },
            config_file,
            indent=4,
        )

    # Read-write for OS user only
    os.chmod(context.obj.config.config_path, stat.S_IRUSR | stat.S_IWUSR)

    typer.echo("Config created successfully.")


@app.command()
def register(context: typer.Context):
    """
    Register a new user.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    # Get required information to create an account
    first_name = typer.prompt("Please enter your first name")
    last_name = typer.prompt("Please enter your last name")
    email = typer.prompt("Please enter your email address")
    site = typer.prompt("Please enter your site code")
    password = typer.prompt(
        "Please enter your password", hide_input=True, confirmation_prompt=True
    )

    # Register the account
    try:
        registration = OnyxClient.register(
            context.obj.config,
            first_name=first_name,
            last_name=last_name,
            email=email,
            site=site,
            password=password,
        )
        typer.echo(f"Successfully created the account '{registration['username']}'.")
    except requests.HTTPError as e:
        show_error(e.response)


@app.command()
def login(
    context: typer.Context,
    username: Optional[str] = typer.Option(
        default=None,
        envvar="ONYX_CLIENT_USERNAME",
    ),
    password: Optional[str] = typer.Option(
        default=None,
        envvar="ONYX_CLIENT_PASSWORD",
    ),
):
    """
    Log in to Onyx.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    # Get the username and password
    if not username:
        username = typer.prompt("Please enter your username")
    context.obj.config.username = username

    if not password:
        password = typer.prompt("Please enter your password", hide_input=True)
    context.obj.config.password = password

    # Log in
    try:
        context.obj.client.login()
        typer.echo(f"Successfully logged in as '{context.obj.config.username}'.")
    except requests.HTTPError as e:
        show_error(e.response)


@app.command()
def logout(
    context: typer.Context,
):
    """
    Log out of Onyx.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    try:
        context.obj.client.logout()
        typer.echo("Successfully logged out.")
    except requests.HTTPError as e:
        show_error(e.response)


@app.command()
def logoutall(
    context: typer.Context,
):
    """
    Log out of Onyx everywhere.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    try:
        context.obj.client.logoutall()
        typer.echo("Successfully logged out everywhere.")
    except requests.HTTPError as e:
        show_error(e.response)


@app.command()
def profile(
    context: typer.Context,
):
    """
    View the logged-in user's information.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    user = context.obj.client._profile()
    if user.ok:
        print_response(user)
    else:
        show_error(user)


@app.command()
def waiting(
    context: typer.Context,
):
    """
    List users waiting for approval.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    users = context.obj.client._waiting()
    if users.ok:
        print_response(users)
    else:
        show_error(users)


@app.command()
def approve(
    context: typer.Context,
    username: str,
):
    """
    Approve a user.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    try:
        approval = context.obj.client.approve(username)
        typer.echo(f"Successfully approved '{approval['username']}'.")
    except requests.HTTPError as e:
        show_error(e.response)


@app.command()
def siteusers(
    context: typer.Context,
):
    """
    List site users.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    users = context.obj.client._site_users()
    if users.ok:
        print_response(users)
    else:
        show_error(users)


@app.command()
def allusers(
    context: typer.Context,
):
    """
    List all users.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    users = context.obj.client._all_users()
    if users.ok:
        print_response(users)
    else:
        show_error(users)


@app.command()
def projects(
    context: typer.Context,
):
    """
    View available projects.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    projects = context.obj.client._projects()
    if projects.ok:
        print_response(projects)
    else:
        show_error(projects)


@app.command()
def fields(
    context: typer.Context,
    project: str,
    scope: Optional[List[str]] = typer.Option(
        default=None,
    ),
):
    """
    View fields for a project.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    fields = context.obj.client._fields(
        project,
        scope=scope,
    )
    if fields.ok:
        print_response(fields)
    else:
        show_error(fields)


@app.command()
def choices(
    context: typer.Context,
    project: str,
    field: str,
):
    """
    View choices for a field.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    choices = context.obj.client._choices(project, field)
    if choices.ok:
        print_response(choices)
    else:
        show_error(choices)


@app.command()
def get(
    context: typer.Context,
    project: str,
    cid: str,
    include: Optional[List[str]] = typer.Option(
        default=None,
    ),
    exclude: Optional[List[str]] = typer.Option(
        default=None,
    ),
    scope: Optional[List[str]] = typer.Option(
        default=None,
    ),
):
    """
    Get a record from a project.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    record = context.obj.client._get(
        project,
        cid,
        include=include,
        exclude=exclude,
        scope=scope,
    )
    if record.ok:
        print_response(record)
    else:
        show_error(record)


class Formats(enum.Enum):
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"


@app.command()
def filter(
    context: typer.Context,
    project: str,
    field: Optional[List[str]] = typer.Option(
        default=None,
    ),
    include: Optional[List[str]] = typer.Option(
        default=None,
    ),
    exclude: Optional[List[str]] = typer.Option(
        default=None,
    ),
    scope: Optional[List[str]] = typer.Option(
        default=None,
    ),
    format: Optional[Formats] = typer.Option(
        default=None,
    ),
):
    """
    Filter records from a project.
    """

    assert isinstance(context.obj.config, OnyxConfig)
    assert isinstance(context.obj.client, OnyxClient)

    fields = {}
    if field:
        for f_v in field:
            try:
                f, v = f_v.split("=")
            except ValueError:
                raise click.BadParameter(
                    "'field=value' syntax was not used for --field"
                )
            f = f.replace(".", "__")
            fields.setdefault(f, []).append(v)

    if format:
        results = context.obj.client.filter(
            project,
            fields,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        try:
            if format == Formats.JSON:
                data = [result for result in results]
                typer.echo(json.dumps(data))
            else:
                result = next(results, None)
                if result:
                    writer = csv.DictWriter(
                        sys.stdout,
                        delimiter="\t" if format == Formats.TSV else ",",
                        fieldnames=result.keys(),
                    )
                    writer.writeheader()
                    writer.writerow(result)

                    for result in results:
                        writer.writerow(result)
        except requests.HTTPError as e:
            show_error(e.response)
    else:
        results = context.obj.client._filter(
            project,
            fields,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        for result in results:
            if result.ok:
                print_response(result)
            else:
                show_error(result)


@dataclasses.dataclass
class OnyxCLI:
    config: OnyxConfig
    client: OnyxClient


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback(name="onyx", help=f"Client Version: {__version__}")
def common(
    context: typer.Context,
    config: Optional[str] = typer.Option(
        default=OnyxConfig.CONFIG_FILE_PATH
        if os.path.isfile(
            OnyxConfig.CONFIG_FILE_PATH.replace("~", os.path.expanduser("~"))
        )
        else None,
        envvar="ONYX_CLIENT_CONFIG",
    ),
    domain: Optional[str] = typer.Option(
        default=None,
        envvar="ONYX_CLIENT_DOMAIN",
    ),
    token: Optional[str] = typer.Option(
        default=None,
        envvar="ONYX_CLIENT_TOKEN",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        help="Show the client version number and exit.",
    ),
):
    conf = OnyxConfig(
        config_path=config,
        domain=domain,
        token=token,
    )
    client = OnyxClient(conf)
    context.obj = OnyxCLI(conf, client)


def main():
    app()
