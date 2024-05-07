import os
import csv
import sys
import ast
import enum
import json
import dataclasses
from typing import Optional, List, Dict, Any
import http.client
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
    """
    Set up the Onyx API.

    Args:
        options: The config options for the Onyx API.

    Returns:
        The Onyx API object containing a config and client.
    """

    config = OnyxConfig(
        domain=options.domain if options.domain else "",
        username=options.username,
        password=options.password,
        token=options.token,
    )
    client = OnyxClient(config)
    return OnyxAPI(config, client)


def json_dump_pretty(obj: Any) -> str:
    """
    Pretty print a JSON object.

    Args:
        obj: The JSON object to pretty print.

    Returns:
        The pretty printed JSON object.
    """

    return json.dumps(obj, indent=4)


def handle_error(e: Exception) -> None:
    """
    Handle an Onyx exception, coercing into a CLI-friendly format if possible.

    Args:
        e: The exception to handle.

    Raises:
        click.exceptions.ClickException: If the exception is an OnyxHTTPError or OnyxError.
        Exception: If the exception is not an OnyxHTTPError or OnyxError.
    """

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
) -> Table:
    """
    Create a table from a list of dictionaries.

    Args:
        data: List of dictionaries.
        map: Dictionary mapping the column names to the dictionary keys.

    Returns:
        A rich Table object.
    """

    table = Table(
        show_lines=True,
    )

    for column in map.keys():
        table.add_column(column, overflow="fold")

    for row in data:
        table.add_row(*(str(row.get(key, "")) for key in map.values()))

    return table


def parse_fields_option(fields_option: List[str]) -> Dict[str, str]:
    """
    Parse the fields option into a dictionary that maps field names to values.

    Args:
        fields_option: List of unparsed 'field=value' pairs.

    Returns:
        The parsed dictionary of field names mapped to their values.
    """

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
    """
    Parse the extra option into a list of valid field names.

    Replaces '.' with '__' to match the API's field naming convention.

    Args:
        extra_option: List of unparsed field names.

    Returns:
        The parsed list of field names.
    """

    return [
        field.replace(".", "__")
        for fields in extra_option
        for field in fields.split(",")
    ]


class HelpText(enum.Enum):
    FIELD = "Filter the data by providing conditions that the fields must match. Uses a `name=value` syntax."
    INCLUDE = "Specify which fields to include in the output."
    EXCLUDE = "Specify which fields to exclude from the output."
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


class Status(enum.Enum):
    REQUIRED = "[bold red]required[/]"
    OPTIONAL = "[bold cyan]optional[/]"


class Actions(enum.Enum):
    GET = "[bold cyan]get[/]"
    LIST = "[bold blue]list[/]"
    FILTER = "[bold magenta]filter[/]"
    HISTORY = "[bold yellow]history[/]"
    IDENTIFY = "[bold white]identify[/]"
    ADD = "[bold green]add[/]"
    CHANGE = "[bold yellow]change[/]"
    DELETE = "[bold red]delete[/]"


class ActiveStatus(enum.Enum):
    ACTIVE = "[bold green]active[/]"
    INACTIVE = "[bold red]inactive[/]"


class Method(enum.Enum):
    GET = "[bold cyan]GET[/]"
    POST = "[bold green]POST[/]"
    PUT = "[bold blue]PUT[/]"
    PATCH = "[bold yellow]PATCH[/]"
    DELETE = "[bold red]DELETE[/]"
    OPTIONS = "[bold magenta]OPTIONS[/]"
    HEAD = "[bold white]HEAD[/]"


def format_action(action: str) -> str:
    """
    Format an action and apply its colour.

    Args:
        action: The action to format.

    Returns:
        The formatted action.
    """

    match action:
        case "get":
            return Actions.GET.value
        case "list":
            return Actions.LIST.value
        case "filter":
            return Actions.FILTER.value
        case "history":
            return Actions.HISTORY.value
        case "identify":
            return Actions.IDENTIFY.value
        case "add":
            return Actions.ADD.value
        case "change":
            return Actions.CHANGE.value
        case "delete":
            return Actions.DELETE.value
        case _:
            return action


def format_status_code(status: Optional[int]) -> str:
    """
    Format a status code, apply its colour and add a description of the status.

    Args:
        status: The status to format.

    Returns:
        The formatted status.
    """

    if status is None:
        return ""

    status_str = f"{status} ({http.client.responses[status]})"

    if status_str.startswith("2"):
        return f"[bold green]{status_str}[/]"

    elif status_str.startswith("3"):
        return f"[bold cyan]{status_str}[/]"

    elif status_str.startswith("4"):
        return f"[bold yellow]{status_str}[/]"

    elif status_str.startswith("5"):
        return f"[bold red]{status_str}[/]"

    else:
        return status_str


def format_method(method: str) -> str:
    """
    Format a method and apply its colour.

    Args:
        method: The method to format.

    Returns:
        The formatted method.
    """

    match method:
        case "GET":
            return Method.GET.value
        case "POST":
            return Method.POST.value
        case "PUT":
            return Method.PUT.value
        case "PATCH":
            return Method.PATCH.value
        case "DELETE":
            return Method.DELETE.value
        case "OPTIONS":
            return Method.OPTIONS.value
        case "HEAD":
            return Method.HEAD.value
        case _:
            return method


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
            columns = ["Project", "Scope", "Actions"]
            table = Table(
                show_lines=True,
            )

            for column in columns:
                table.add_column(column, overflow="fold")

            for project in projects:
                table.add_row(
                    project.get("project", ""),
                    project.get("scope", ""),
                    " | ".join(
                        [format_action(action) for action in project.get("actions", [])]
                    ),
                )

            console.print(table)
        else:
            typer.echo(json_dump_pretty(projects))
    except Exception as e:
        handle_error(e)


@app.command()
def types(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View available field types.
    """

    try:
        api = setup_onyx_api(context.obj)
        types = api.client.types()

        if format == InfoFormats.TABLE:
            columns = ["Type", "Description", "Lookups"]
            table = Table(
                show_lines=True,
            )

            for column in columns:
                table.add_column(column, overflow="fold")

            for t in types:
                table.add_row(
                    t.get("type", ""),
                    t.get("description", ""),
                    " | ".join(t.get("lookups", [])),
                )

            console.print(table)
        else:
            typer.echo(json_dump_pretty(types))
    except Exception as e:
        handle_error(e)


@app.command()
def lookups(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View available lookups.
    """

    try:
        api = setup_onyx_api(context.obj)
        lookups = api.client.lookups()

        if format == InfoFormats.TABLE:
            columns = ["Lookup", "Description", "Types"]
            table = Table(
                show_lines=True,
            )

            for column in columns:
                table.add_column(column, overflow="fold")

            for lookup in lookups:
                table.add_row(
                    lookup.get("lookup", ""),
                    lookup.get("description", ""),
                    " | ".join(lookup.get("types", [])),
                )

            console.print(table)
        else:
            typer.echo(json_dump_pretty(projects))
    except Exception as e:
        handle_error(e)


def add_fields_table(
    table: Table, data: Dict[str, Any], prefix: Optional[str] = None
) -> None:
    """
    Add fields from the field specification data to the input table.

    Works recursively for nested fields.

    Args:
        table: The table object to add the fields to.
        data: The fields data.
        prefix: The prefix for the fields (if nested).
    """

    for field, field_spec in data.items():
        restrictions = []
        if field_spec.get("default") is not None:
            restrictions.append(f"• Default: {field_spec['default']}")
        if field_spec.get("restrictions"):
            restrictions.extend(
                f"• {restriction}" for restriction in field_spec["restrictions"]
            )
        if field_spec.get("values"):
            if len(field_spec["values"]) > 20:
                restrictions.append(
                    "• Choices: " + ", ".join(field_spec["values"][:20]) + ", ..."
                )
            else:
                restrictions.append("• Choices: " + ", ".join(field_spec["values"]))

        table.add_row(
            # Field
            ("-" * (prefix.count(".") + 1) + f" {prefix}.{field}" if prefix else field),
            # Status
            (
                Status.REQUIRED.value
                if field_spec["required"]
                else Status.OPTIONAL.value
            ),
            # Type
            field_spec["type"],
            # Description
            field_spec.get("description", ""),
            # Actions
            " | ".join(
                [format_action(action) for action in field_spec.get("actions", [])]
            ),
            # Restrictions (choices, default value, additional restrictions)
            "\n".join(restrictions),
        )

        if field_spec["type"] == "relation":
            add_fields_table(
                table,
                field_spec["fields"],
                prefix=f"{prefix}.{field}" if prefix else field,
            )


def add_fields_writer(
    writer: csv.DictWriter,
    columns: List[str],
    data: Dict[str, Any],
    prefix: Optional[str] = None,
) -> None:
    """
    Add fields from the field specification data to the input CSV writer.

    Works recursively for nested fields.

    Args:
        writer: The CSV writer object to add the fields to.
        columns: The column names for the CSV writer.
        data: The fields data.
        prefix: The prefix for the fields (if nested).
    """

    for field, field_spec in data.items():
        writer.writerow(
            dict(
                zip(
                    columns,
                    [
                        # Field
                        f"{prefix}.{field}" if prefix else field,
                        # Status
                        "required" if field_spec["required"] else "optional",
                        # Type
                        field_spec["type"],
                        # Description
                        field_spec.get("description", ""),
                        # Actions
                        ", ".join(field_spec.get("actions", "")),
                        # Choices
                        ", ".join(field_spec.get("values", "")),
                        # Default
                        field_spec.get("default", ""),
                        # Restrictions
                        ", ".join(field_spec.get("restrictions", "")),
                    ],
                )
            )
        )

        if field_spec["type"] == "relation":
            add_fields_writer(
                writer,
                columns,
                field_spec["fields"],
                prefix=f"{prefix}.{field}" if prefix else field,
            )


@app.command()
def fields(
    context: typer.Context,
    project: str = typer.Argument(...),
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
        fields = api.client.fields(project)

        if format == FieldFormats.JSON:
            typer.echo(json_dump_pretty(fields))
        elif format == FieldFormats.TABLE:
            columns = [
                "Field",
                "Status",
                "Type",
                "Description",
                "Actions",
                "Restrictions",
            ]
            caption = f"Fields specification for the {fields['name']} project. Version: {fields['version']}"

            if fields.get("description"):
                caption += "\n" + fields["description"]

            table = Table(
                caption=caption,
                show_lines=True,
            )
            for column in columns:
                table.add_column(column, overflow="fold")
            add_fields_table(table, fields["fields"])
            console.print(table)
        else:
            columns = [
                "Field",
                "Status",
                "Type",
                "Description",
                "Actions",
                "Choices",
                "Default",
                "Restrictions",
            ]
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
    View options for a choice field in a project.
    """

    try:
        api = setup_onyx_api(context.obj)
        field = parse_extra_option([field])[0]
        choices = api.client.choices(project, field)

        if format == InfoFormats.TABLE:
            table = Table(
                show_lines=True,
            )
            table.add_column("Choice", overflow="fold")
            table.add_column("Description", overflow="fold")
            table.add_column("Status", overflow="fold")
            for choice, choice_info in choices.items():
                active_status = choice_info.get("is_active")
                if active_status == True:
                    active_status = ActiveStatus.ACTIVE.value
                elif active_status == False:
                    active_status = ActiveStatus.INACTIVE.value
                else:
                    active_status = ""

                table.add_row(
                    choice,
                    choice_info.get("description", ""),
                    active_status,
                )
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

        record = api.client.get(
            project,
            climb_id,
            fields=fields,
            include=include,
            exclude=exclude,
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
    summarise: Optional[List[str]] = typer.Option(
        None,
        "-s",
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

        if summarise:
            summarise = parse_extra_option(summarise)

        if format == DataFormats.JSON:
            # ...nobody needs to know
            results = onyx_errors(super(OnyxClient, api.client).filter)(
                project,
                fields,
                include=include,
                exclude=exclude,
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
def history(
    context: typer.Context,
    project: str = typer.Argument(...),
    climb_id: str = typer.Argument(...),
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View the history of a record in a project.
    """

    try:
        api = setup_onyx_api(context.obj)
        history = api.client.history(project, climb_id)

        if format == InfoFormats.TABLE:
            columns = ["Username", "Timestamp", "Action", "Changes"]

            table = Table(show_lines=True)
            for column in columns:
                table.add_column(column, overflow="fold")

            actions = {
                "add": "added",
                "change": "changed",
                "delete": "deleted",
            }

            for h in history["history"]:
                changes = []
                for change in h.get("changes", []):
                    if change.get("type") == "relation":
                        action = actions.get(change.get("action", ""), "")
                        count = change.get("count", "")

                        if count:
                            count = f"{count} record{'s' if count != 1 else ''}"

                        changes.append(f"• {change['field']}: {action} {count}")
                    else:
                        changes.append(
                            f"• {change['field']}: {change.get('from', '')} → {change.get('to', '')}"
                        )

                table.add_row(
                    h.get("username", ""),
                    h.get("timestamp", ""),
                    format_action(h.get("action", "")),
                    "\n".join(changes),
                )

            console.print(table)
        else:
            typer.echo(json_dump_pretty(history))
    except Exception as e:
        handle_error(e)


@app.command()
def identify(
    context: typer.Context,
    project: str = typer.Argument(...),
    field: str = typer.Argument(...),
    value: str = typer.Argument(...),
    site: Optional[str] = typer.Option(
        None,
        "-s",
        "--site",
        help="Site code for the value. If not provided, defaults to the user's site.",
    ),
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
        identifier = api.client.identify(
            project,
            field,
            value,
            site=site,
        )

        if format == InfoFormats.TABLE:
            table = create_table(
                data=[identifier],
                map={
                    "Project": "project",
                    "Site": "site",
                    "Field": "field",
                    "Value": "value",
                    "Identifier": "identifier",
                },
            )
            console.print(table)
        else:
            typer.echo(json_dump_pretty(identifier))
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
def activity(
    context: typer.Context,
    format: Optional[InfoFormats] = typer.Option(
        InfoFormats.TABLE.value,
        "-F",
        "--format",
        help=HelpText.FORMAT.value,
    ),
):
    """
    View latest profile activity.
    """

    try:
        api = setup_onyx_api(context.obj)
        activity = api.client.activity()

        if format == InfoFormats.TABLE:
            columns = [
                "Address",
                "Timestamp",
                "Method",
                "Endpoint",
                "Status Code",
                "Execution Time (ms)",
                "Errors",
            ]

            table = Table(show_lines=True)
            for column in columns:
                table.add_column(column, overflow="fold")

            for a in activity:
                errors = a.get("error_messages", "")
                if errors:
                    errors = json_dump_pretty(json.loads(ast.literal_eval(errors)))

                table.add_row(
                    a.get("address", ""),
                    a.get("date", ""),
                    format_method(a.get("method", "")),
                    a.get("endpoint", ""),
                    format_status_code(a.get("status")),
                    str(a.get("exec_time", "")),
                    errors,
                )

            console.print(table)
        else:
            typer.echo(json_dump_pretty(activity))
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
