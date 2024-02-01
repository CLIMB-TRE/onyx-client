import os
import csv
import sys
import enum
import json
import dataclasses
from typing import Optional, List, Dict, Any
import click
import typer
from typer.core import TyperGroup
from rich.console import Console
from rich.table import Table
from .version import __version__
from .config import OnyxConfig, OnyxEnv
from .api import OnyxClient, onyx_errors
from . import exceptions


color_system = "auto"
if os.getenv("ONYX_COLOURS", "").upper().strip() == "NONE":
    from typer import rich_utils

    rich_utils.COLOR_SYSTEM = None
    color_system = None

console = Console(color_system=color_system)


class DefinedOrderGroup(TyperGroup):
    def list_commands(self, ctx):
        return self.commands.keys()


app = typer.Typer(
    cls=DefinedOrderGroup,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

auth_app = typer.Typer(
    name="auth",
    help="Authentication commands.",
    cls=DefinedOrderGroup,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

admin_app = typer.Typer(
    name="admin",
    help="Admin commands.",
    cls=DefinedOrderGroup,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.add_typer(auth_app)
app.add_typer(admin_app)


@dataclasses.dataclass
class OnyxConfigOptions:
    domain: Optional[str]
    token: Optional[str]
    username: Optional[str]
    password: Optional[str]


@dataclasses.dataclass
class OnyxAPI:
    config: OnyxConfig
    client: OnyxClient


def setup_onyx_api(options: OnyxConfigOptions) -> OnyxAPI:
    config = OnyxConfig(
        domain=options.domain if options.domain else "",
        username=options.username,
        password=options.password,
        token=options.token,
    )
    client = OnyxClient(config)
    return OnyxAPI(config, client)


def json_dump_pretty(obj: Any):
    return json.dumps(obj, indent=4)


def handle_error(e: Exception):
    if isinstance(e, exceptions.OnyxHTTPError):
        try:
            messages = e.response.json()["messages"]
            detail = messages.get("detail")

            if detail:
                formatted_response = detail
            else:
                formatted_response = json_dump_pretty(messages)

        except json.decoder.JSONDecodeError:
            formatted_response = e.response.text
        raise click.exceptions.ClickException(formatted_response)

    elif isinstance(e, exceptions.OnyxError):
        raise click.exceptions.ClickException(str(e))

    else:
        raise e


def create_table(
    data: List[Dict[str, Any]],
    map: Dict[str, str],
    styles: Optional[Dict[str, Dict[str, str]]] = None,
) -> Table:
    table = Table(
        show_lines=True,
    )

    for column in map.keys():
        table.add_column(column)

    for row in data:
        table.add_row(
            *(
                row[key]
                if (not styles) or (key not in styles) or (row[key] not in styles[key])
                else f"[{styles[key][row[key]]}]{row[key]}[/]"
                for key in map.values()
            )
        )

    return table


def parse_fields_option(fields_option: List[str]) -> Dict[str, str]:
    fields = {}
    for name_value in fields_option:
        try:
            name, value = name_value.split("=")
        except ValueError:
            raise click.BadParameter(
                "'name=value' syntax was not used.",
                param_hint="'-f' / '--field'",
            )
        name = name.replace(".", "__")
        fields.setdefault(name, []).append(value)
    return fields


def parse_extra_option(extra_option: List[str]) -> List[str]:
    return [
        field.replace(".", "__")
        for fields in extra_option
        for field in fields.split(",")
    ]


class HelpText(enum.Enum):
    FIELD = "Filter the data by providing conditions that the fields must match. Uses a `name=value` syntax."
    INCLUDE = "Specify which fields to include in the output."
    EXCLUDE = "Specify which fields to exclude from the output."
    SCOPE = "Access additional fields beyond the 'base' group of fields."
    SUMMARISE = "For a given field (or group of fields), return the frequency of each unique value (or unique group of values)."
    FORMAT = "Set the file format of the returned data."


class DataFormats(enum.Enum):
    JSON = "json"
    CSV = "csv"
    TSV = "tsv"


class InfoFormats(enum.Enum):
    TABLE = "table"
    JSON = "json"


class FieldFormats(enum.Enum):
    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    TSV = "tsv"


class Messages(enum.Enum):
    SUCCESS = "[bold green][SUCCESS][/]"
    NOTE = "[bold cyan][NOTE][/]"


@app.command()
def projects(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View available projects.
    """

    try:
        api = setup_onyx_api(context.obj)
        projects = api.client.projects()
        if format == InfoFormats.TABLE:
            table = create_table(
                data=projects,
                map={
                    "Project": "project",
                    "Action": "action",
                    "Scope": "scope",
                },
                styles={
                    "action": {
                        "view": "bold cyan",
                        "add": "bold green",
                        "change": "bold yellow",
                        "delete": "bold red",
                    }
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(projects))
    except Exception as e:
        handle_error(e)


def add_fields_table(
    table: Table, data: Dict[str, Any], prefix: Optional[str] = None
) -> None:
    for field, field_info in data.items():
        table.add_row(
            f"[dim]{prefix}.{field}[/dim]" if prefix else field,
            "[bold red]required[/]"
            if field_info["required"]
            else "[bold cyan]optional[/]",
            field_info["type"],
            field_info.get("description", ""),
            ", ".join(field_info.get("values")) if field_info.get("values") else "",
        )

        if field_info["type"] == "relation":
            add_fields_table(
                table,
                field_info["fields"],
                prefix=f"{prefix}.{field}" if prefix else field,
            )


def add_fields_writer(
    writer: csv.DictWriter,
    columns: List[str],
    data: Dict[str, Any],
    prefix: Optional[str] = None,
) -> None:
    for field, field_info in data.items():
        writer.writerow(
            dict(
                zip(
                    columns,
                    [
                        f"{prefix}.{field}" if prefix else field,
                        "required" if field_info["required"] else "optional",
                        field_info["type"],
                        field_info.get("description", ""),
                        ", ".join(field_info.get("values"))
                        if field_info.get("values")
                        else "",
                    ],
                )
            )
        )

        if field_info["type"] == "relation":
            add_fields_writer(
                writer,
                columns,
                field_info["fields"],
                prefix=f"{prefix}.{field}" if prefix else field,
            )


@app.command()
def fields(
    context: typer.Context,
    project: str = typer.Argument(...),
    scope: Optional[List[str]] = typer.Option(
        None,
        "-s",
        "--scope",
        help=HelpText.SCOPE.value,
    ),
    format: Optional[FieldFormats] = typer.Option(
        FieldFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View the field specification for a project.
    """

    try:
        api = setup_onyx_api(context.obj)

        if scope:
            scope = parse_extra_option(scope)

        fields = api.client.fields(
            project,
            scope=scope,
        )
        if format == FieldFormats.JSON:
            typer.echo(json_dump_pretty(fields))
        else:
            columns = ["Field", "Status", "Type", "Description", "Values"]
            caption = f"Fields specification for the {fields['name']} project. Version: {fields['version']}"

            if fields.get("description"):
                caption += "\n" + fields["description"]

            if format == FieldFormats.TABLE:
                table = Table(
                    caption=caption,
                    show_lines=True,
                )
                for column in columns:
                    table.add_column(column, overflow="fold")
                add_fields_table(table, fields["fields"])
                console.print(table)

            else:
                if format == FieldFormats.TSV:
                    delimiter = "\t"
                else:
                    delimiter = ","

                writer = csv.DictWriter(
                    sys.stdout,
                    delimiter=delimiter,
                    fieldnames=columns,
                )
                writer.writeheader()
                add_fields_writer(writer, columns, fields["fields"])
    except Exception as e:
        handle_error(e)


@app.command()
def choices(
    context: typer.Context,
    project: str = typer.Argument(...),
    field: str = typer.Argument(...),
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View options for a choice field.
    """

    try:
        api = setup_onyx_api(context.obj)
        choices = api.client.choices(project, field)
        if format == InfoFormats.TABLE:
            table = Table(
                show_lines=True,
            )
            table.add_column("Field")
            table.add_column("Values")
            table.add_row(field, ", ".join(choices))
            console.print(table)
        else:
            typer.echo(json_dump_pretty(choices))
    except Exception as e:
        handle_error(e)


@app.command()
def get(
    context: typer.Context,
    project: str = typer.Argument(...),
    climb_id: Optional[str] = typer.Argument(
        None,
    ),
    field: Optional[List[str]] = typer.Option(
        None,
        "-f",
        "--field",
        help=HelpText.FIELD.value,
    ),
    include: Optional[List[str]] = typer.Option(
        None,
        "-i",
        "--include",
        help=HelpText.INCLUDE.value,
    ),
    exclude: Optional[List[str]] = typer.Option(
        None,
        "-e",
        "--exclude",
        help=HelpText.EXCLUDE.value,
    ),
    scope: Optional[List[str]] = typer.Option(
        None,
        "-s",
        "--scope",
        help=HelpText.SCOPE.value,
    ),
):
    """
    Get a record from a project.
    """

    try:
        api = setup_onyx_api(context.obj)

        if field:
            fields = parse_fields_option(field)
        else:
            fields = {}

        if include:
            include = parse_extra_option(include)

        if exclude:
            exclude = parse_extra_option(exclude)

        if scope:
            scope = parse_extra_option(scope)

        record = api.client.get(
            project,
            climb_id,
            fields=fields,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        typer.echo(json_dump_pretty(record))
    except Exception as e:
        handle_error(e)


@app.command()
def filter(
    context: typer.Context,
    project: str = typer.Argument(...),
    field: Optional[List[str]] = typer.Option(
        None,
        "-f",
        "--field",
        help=HelpText.FIELD.value,
    ),
    include: Optional[List[str]] = typer.Option(
        None,
        "-i",
        "--include",
        help=HelpText.INCLUDE.value,
    ),
    exclude: Optional[List[str]] = typer.Option(
        None,
        "-e",
        "--exclude",
        help=HelpText.EXCLUDE.value,
    ),
    scope: Optional[List[str]] = typer.Option(
        None,
        "-s",
        "--scope",
        help=HelpText.SCOPE.value,
    ),
    summarise: Optional[List[str]] = typer.Option(
        None,
        "-S",
        "--summarise",
        help=HelpText.SUMMARISE.value,
    ),
    format: Optional[DataFormats] = typer.Option(
        DataFormats.JSON.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    Filter multiple records from a project.
    """

    try:
        api = setup_onyx_api(context.obj)

        if field:
            fields = parse_fields_option(field)
        else:
            fields = {}

        if include:
            include = parse_extra_option(include)

        if exclude:
            exclude = parse_extra_option(exclude)

        if scope:
            scope = parse_extra_option(scope)

        if summarise:
            summarise = parse_extra_option(summarise)

        if format == DataFormats.JSON:
            # ...nobody needs to know
            results = onyx_errors(super(OnyxClient, api.client).filter)(
                project,
                fields,
                include=include,
                exclude=exclude,
                scope=scope,
                summarise=summarise,
            )

            for result in results:
                if result.ok:
                    try:
                        result_json = result.json()
                    except json.decoder.JSONDecodeError:
                        raise click.exceptions.ClickException(result.text)

                    rendered_response = json_dump_pretty(result_json["data"])

                    if result_json.get("previous"):
                        if not rendered_response.startswith("[\n"):
                            raise Exception(
                                "Response JSON has invalid start character(s)."
                            )
                        rendered_response = rendered_response.removeprefix("[\n")

                    if result_json.get("next"):
                        if not rendered_response.endswith("}\n]"):
                            raise Exception(
                                "Response JSON has invalid end character(s)."
                            )
                        rendered_response = (
                            rendered_response.removesuffix("}\n]") + "},"
                        )

                    typer.echo(rendered_response)
                else:
                    raise exceptions.OnyxHTTPError("", result)
        else:
            records = api.client.filter(
                project,
                fields,
                include=include,
                exclude=exclude,
                scope=scope,
                summarise=summarise,
            )

            record = next(records, None)
            if record:
                writer = csv.DictWriter(
                    sys.stdout,
                    delimiter="\t" if format == DataFormats.TSV else ",",
                    fieldnames=record.keys(),
                )
                writer.writeheader()
                writer.writerow(record)

                for record in records:
                    writer.writerow(record)
    except Exception as e:
        handle_error(e)


@app.command()
def identify(
    context: typer.Context,
    project: str = typer.Argument(...),
    field: str = typer.Argument(...),
    value: str = typer.Argument(...),
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    Get the anonymised identifier for a value on a field.
    """

    try:
        api = setup_onyx_api(context.obj)
        identified = api.client.identify(project, field, value)
        if format == InfoFormats.TABLE:
            table = Table(
                show_lines=True,
            )
            table.add_column("Field")
            table.add_column("Value")
            table.add_column("Identifier")
            table.add_row(
                identified["field"],
                identified["value"],
                identified["identifier"],
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(identified))
    except Exception as e:
        handle_error(e)


@app.command()
def profile(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View profile information.
    """

    try:
        api = setup_onyx_api(context.obj)
        user = api.client.profile()
        if format == InfoFormats.TABLE:
            table = create_table(
                data=[user],
                map={
                    "Username": "username",
                    "Email": "email",
                    "Site": "site",
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(user))
    except Exception as e:
        handle_error(e)


@app.command()
def siteusers(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View users from the same site.
    """

    try:
        api = setup_onyx_api(context.obj)
        users = api.client.site_users()
        if format == InfoFormats.TABLE:
            table = create_table(
                data=users,
                map={
                    "Username": "username",
                    "Email": "email",
                    "Site": "site",
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(users))
    except Exception as e:
        handle_error(e)


@auth_app.command()
def register(context: typer.Context):
    """
    Create a new user.
    """

    try:
        OnyxConfig._validate_domain(context.obj.domain)

        # Get required information to create a user
        first_name = typer.prompt("Please enter your first name")
        last_name = typer.prompt("Please enter your last name")
        email = typer.prompt("Please enter your email address")
        site = typer.prompt("Please enter your site code")
        password = typer.prompt(
            "Please enter your password", hide_input=True, confirmation_prompt=True
        )

        # Register the user
        registration = OnyxClient.register(
            context.obj.domain,
            first_name=first_name,
            last_name=last_name,
            email=email,
            site=site,
            password=password,
        )
        console.print(
            f"{Messages.SUCCESS.value} Created user: '{registration['username']}'"
        )
    except Exception as e:
        handle_error(e)


@auth_app.command()
def login(
    context: typer.Context,
):
    """
    Log in.
    """

    try:
        OnyxConfig._validate_domain(context.obj.domain)

        # Get the username and password
        if not context.obj.username:
            context.obj.username = typer.prompt("Please enter your username")

        if not context.obj.password:
            context.obj.password = typer.prompt(
                "Please enter your password", hide_input=True
            )

        api = setup_onyx_api(context.obj)

        # Log in
        auth = api.client.login()
        console.print(
            f"{Messages.SUCCESS.value} Logged in as user: '{api.config.username}'"
        )
        console.print(f"{Messages.NOTE.value} Obtained token: '{auth['token']}'")
        console.print(
            f"{Messages.NOTE.value} To authenticate, assign this token to the following environment variable: '{OnyxEnv.TOKEN}'"
        )
    except Exception as e:
        handle_error(e)


@auth_app.command()
def logout(
    context: typer.Context,
):
    """
    Log out.
    """

    try:
        api = setup_onyx_api(context.obj)
        api.client.logout()
        console.print(f"{Messages.SUCCESS.value} Logged out.")
    except Exception as e:
        handle_error(e)


@auth_app.command()
def logoutall(
    context: typer.Context,
):
    """
    Log out across all clients.
    """

    try:
        api = setup_onyx_api(context.obj)
        api.client.logoutall()
        console.print(f"{Messages.SUCCESS.value} Logged out across all clients.")
    except Exception as e:
        handle_error(e)


@admin_app.command()
def waiting(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View users waiting for approval.
    """

    try:
        api = setup_onyx_api(context.obj)
        waiting = api.client.waiting()
        if format == InfoFormats.TABLE:
            table = create_table(
                data=waiting,
                map={
                    "Username": "username",
                    "Email": "email",
                    "Site": "site",
                    "Date Joined": "date_joined",
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(waiting))
    except Exception as e:
        handle_error(e)


@admin_app.command()
def approve(
    context: typer.Context,
    username: str = typer.Argument(..., help="Name of the user being approved."),
):
    """
    Approve a user.
    """

    try:
        api = setup_onyx_api(context.obj)
        approval = api.client.approve(username)
        console.print(f"{Messages.SUCCESS.value} Approved user: {approval['username']}")
    except Exception as e:
        handle_error(e)


@admin_app.command()
def allusers(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View users across all sites.
    """

    try:
        api = setup_onyx_api(context.obj)
        users = api.client.all_users()
        if format == InfoFormats.TABLE:
            table = create_table(
                data=users,
                map={
                    "Username": "username",
                    "Email": "email",
                    "Site": "site",
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(users))
    except Exception as e:
        handle_error(e)


def version_callback(value: bool):
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback(name="onyx", help=f"API for pathogen metadata.")
def common(
    context: typer.Context,
    domain: Optional[str] = typer.Option(
        None,
        "-d",
        "--domain",
        envvar=OnyxEnv.DOMAIN,
        help="Domain name for connecting to Onyx.",
    ),
    token: Optional[str] = typer.Option(
        None,
        "-t",
        "--token",
        envvar=OnyxEnv.TOKEN,
        help="Token for authenticating with Onyx.",
    ),
    username: Optional[str] = typer.Option(
        None,
        "-u",
        "--username",
        envvar=OnyxEnv.USERNAME,
        help="Username for authenticating with Onyx.",
    ),
    password: Optional[str] = typer.Option(
        None,
        "-p",
        "--password",
        envvar=OnyxEnv.PASSWORD,
        help="Password for authenticating with Onyx.",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        help="Show the client version number and exit.",
    ),
):
    context.obj = OnyxConfigOptions(
        domain=domain,
        token=token,
        username=username,
        password=password,
    )


def main():
    app()
