import os
import sys
import csv
import json
import requests
import argparse
from . import version, utils
from .config import OnyxConfig
from .api import OnyxClient


def client_required(func):
    def wrapped_func(args):
        config = OnyxConfig(
            domain=args.domain,
            token=args.token,
        )
        client = OnyxClient(config)
        return func(client, args)

    return wrapped_func


def register(args):
    """
    Create a new user.
    """

    config = OnyxConfig(
        domain=args.domain,
        token=args.token,
    )
    first_name = utils.get_input("first name")
    last_name = utils.get_input("last name")
    email = utils.get_input("email address")
    site = utils.get_input("site code")

    password = utils.get_input("password", password=True)
    password2 = utils.get_input("password (again)", password=True)

    while password != password2:
        print("Passwords do not match. Please try again.")
        password = utils.get_input("password", password=True)
        password2 = utils.get_input("password (again)", password=True)

    registration = OnyxClient._register(
        config,
        first_name=first_name,
        last_name=last_name,
        email=email,
        site=site,
        password=password,
    )

    utils.print_response(registration)

    if registration.ok:
        print("Account created successfully.")


def login(args):
    """
    Log in as a user.
    """

    config = OnyxConfig(
        domain=args.domain,
        credentials=(args.user, args.password),
        token=args.token,
    )
    client = OnyxClient(config)
    response = client._login()
    if response.ok:
        print(f"Logged in successfully.")
    else:
        utils.print_response(response)


@client_required
def logout(client: OnyxClient, args):
    """
    Log out the current user.
    """

    response = client._logout()
    if response.ok:
        print("Logged out successfully.")
    else:
        utils.print_response(response)


@client_required
def logoutall(client: OnyxClient, args):
    """
    Log out the current user everywhere.
    """

    response = client._logoutall()
    if response.ok:
        print("Logged out everywhere successfully.")
    else:
        utils.print_response(response)


@client_required
def approve(client: OnyxClient, args):
    """
    Approve a user.
    """

    approval = client._approve(args.username)
    utils.print_response(approval)


@client_required
def waiting(client: OnyxClient, args):
    """
    List users waiting for site approval.
    """

    users = client._waiting()
    utils.print_response(users)


@client_required
def site_users(client: OnyxClient, args):
    """
    List site users.
    """

    users = client._site_users()
    utils.print_response(users)


@client_required
def all_users(client: OnyxClient, args):
    """
    List all users.
    """

    users = client._all_users()
    utils.print_response(users)


@client_required
def create(client: OnyxClient, args):
    """
    Post new records to the database.
    """

    fields = utils.construct_unique_fields_dict(args.field)

    if args.csv:
        creations = client._csv_create(
            args.project,
            csv_path=args.csv,
            fields=fields,
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(creations)

    elif args.tsv:
        creations = client._csv_create(
            args.project,
            csv_path=args.tsv,
            fields=fields,
            delimiter="\t",
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(creations)

    else:
        creation = client._create(args.project, fields=fields, test=args.test)
        utils.print_response(creation)


@client_required
def get(client: OnyxClient, args):
    """
    Get a record from the database.
    """

    include = args.include
    exclude = args.exclude
    scope = args.scope

    if include:
        include = utils.flatten_list_of_lists(include)

    if exclude:
        exclude = utils.flatten_list_of_lists(exclude)

    if scope:
        scope = utils.flatten_list_of_lists(scope)

    response = client._get(
        args.project, args.cid, include=include, exclude=exclude, scope=scope
    )
    utils.print_response(response)


@client_required
def filter(client: OnyxClient, args):
    """
    Filter records from the database.
    """

    fields = utils.construct_fields_dict(args.field)
    include = args.include
    exclude = args.exclude
    scope = args.scope

    if include:
        include = utils.flatten_list_of_lists(include)

    if exclude:
        exclude = utils.flatten_list_of_lists(exclude)

    if scope:
        scope = utils.flatten_list_of_lists(scope)

    if args.format:
        results = client.filter(
            args.project, fields, include=include, exclude=exclude, scope=scope
        )
        try:
            if args.format == "json":
                data = [result for result in results]
                print(json.dumps(data))
            else:
                result = next(results, None)
                if result:
                    writer = csv.DictWriter(
                        sys.stdout,
                        delimiter="\t" if args.format == "tsv" else ",",
                        fieldnames=result.keys(),
                    )
                    writer.writeheader()
                    writer.writerow(result)

                    for result in results:
                        writer.writerow(result)
        except requests.HTTPError as e:
            utils.print_response(e.response)
    else:
        results = client._filter(
            args.project, fields, include=include, exclude=exclude, scope=scope
        )
        for result in results:
            utils.print_response(result)


@client_required
def update(client: OnyxClient, args):
    """
    Update records in the database.
    """

    fields = utils.construct_unique_fields_dict(args.field)

    if args.csv:
        updates = client._csv_update(
            args.project,
            csv_path=args.csv,
            fields=fields,
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(updates)

    elif args.tsv:
        updates = client._csv_update(
            args.project,
            csv_path=args.tsv,
            fields=fields,
            delimiter="\t",
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(updates)

    else:
        update = client._update(args.project, args.cid, fields=fields, test=args.test)
        utils.print_response(update)


@client_required
def delete(client: OnyxClient, args):
    """
    Delete records in the database.
    """

    if args.csv:
        deletions = client._csv_delete(
            args.project,
            csv_path=args.csv,
            multithreaded=args.multithreaded,
        )
        utils.execute_uploads(deletions)

    elif args.tsv:
        deletions = client._csv_delete(
            args.project,
            csv_path=args.tsv,
            delimiter="\t",
            multithreaded=args.multithreaded,
        )
        utils.execute_uploads(deletions)

    else:
        deletion = client._delete(args.project, args.cid)
        utils.print_response(deletion)


@client_required
def projects(client: OnyxClient, args):
    """
    View available projects.
    """

    projects = client._projects()
    utils.print_response(projects)


@client_required
def fields(client: OnyxClient, args):
    """
    View fields for a project.
    """

    scope = args.scope

    if scope:
        scope = utils.flatten_list_of_lists(scope)

    fields = client._fields(args.project, scope=scope)
    utils.print_response(fields)


@client_required
def choices(client: OnyxClient, args):
    """
    View choices for a field.
    """

    choices = client._choices(args.project, args.field)
    utils.print_response(choices)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        help="The config file to use.",
        default=os.getenv("ONYX_CLIENT_CONFIG"),
    )
    parser.add_argument(
        "-d",
        "--domain",
        help="The domain name to target.",
        default=os.getenv("ONYX_CLIENT_DOMAIN"),
    )
    parser.add_argument(
        "-t",
        "--token",
        help="Token to authenticate with.",
        default=os.getenv("ONYX_CLIENT_TOKEN"),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version.__version__,
        help="Client version number.",
    )
    command = parser.add_subparsers(dest="command", metavar="{command}", required=True)

    # ACCOUNTS COMMANDS
    register_parser = command.add_parser("register", help="Register a new user.")
    register_parser.set_defaults(func=register)
    login_parser = command.add_parser("login", help="Log in to onyx.")
    login_parser.add_argument(
        "-u",
        "--user",
        help="The user to log in as.",
        default=os.getenv("ONYX_CLIENT_USERNAME"),
    )
    login_parser.add_argument(
        "-p",
        "--password",
        help="The user's password.",
        default=os.getenv("ONYX_CLIENT_PASSWORD"),
    )
    login_parser.set_defaults(func=login)
    logout_parser = command.add_parser("logout", help="Log out of onyx.")
    logout_parser.set_defaults(func=logout)
    logoutall_parser = command.add_parser(
        "logoutall", help="Log out of onyx everywhere."
    )
    logoutall_parser.set_defaults(func=logoutall)
    waiting_parser = command.add_parser(
        "waiting",
        help="List users waiting for approval.",
    )
    waiting_parser.set_defaults(func=waiting)
    approve_parser = command.add_parser(
        "approve",
        help="Approve a user.",
    )
    approve_parser.add_argument("username", help="User to be approved.")
    approve_parser.set_defaults(func=approve)
    site_users_parser = command.add_parser(
        "siteusers",
        help="List site users.",
    )
    site_users_parser.set_defaults(func=site_users)
    all_users_parser = command.add_parser(
        "allusers",
        help="List all users.",
    )
    all_users_parser.set_defaults(func=all_users)

    # PROJECT COMMANDS
    projects_parser = command.add_parser("projects", help="View available projects.")
    projects_parser.set_defaults(func=projects)

    fields_parser = command.add_parser("fields", help="View fields for a project.")
    fields_parser.add_argument("project")
    fields_parser.add_argument("-s", "--scope", nargs="+", action="append")
    fields_parser.set_defaults(func=fields)

    choices_parser = command.add_parser("choices", help="View choices for a field.")
    choices_parser.add_argument("project")
    choices_parser.add_argument("field")
    choices_parser.set_defaults(func=choices)

    # CRUD PARSER GROUPINGS
    test_parser = argparse.ArgumentParser(add_help=False)
    test_parser.add_argument(
        "--test", action="store_true", help="Run the command as a test."
    )
    multithreaded_parser = argparse.ArgumentParser(add_help=False)
    multithreaded_parser.add_argument("--multithreaded", action="store_true")
    cid_action_parser = argparse.ArgumentParser(add_help=False)
    cid_action_parser.add_argument("project")
    cid_action_group = cid_action_parser.add_mutually_exclusive_group(required=True)
    cid_action_group.add_argument("cid", nargs="?", help="optional")
    cid_action_group.add_argument(
        "--csv",
        help="Carry out action on multiple records via a .csv file. CID column required.",
    )
    cid_action_group.add_argument(
        "--tsv",
        help="Carry out action on multiple records via a .tsv file. CID column required.",
    )

    # CREATE COMMANDS
    create_parser = command.add_parser(
        "create",
        help="Create records in a project.",
        parents=[test_parser, multithreaded_parser],
    )
    create_parser.add_argument("project")
    create_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    create_action_group = create_parser.add_mutually_exclusive_group()
    create_action_group.add_argument(
        "--csv", help="Carry out action on multiple records via a .csv file."
    )
    create_action_group.add_argument(
        "--tsv", help="Carry out action on multiple records via a .tsv file."
    )
    create_parser.set_defaults(func=create)

    # GET COMMANDS
    get_parser = command.add_parser("get", help="Get a record from a project.")
    get_parser.add_argument("project")
    get_parser.add_argument("cid")
    get_parser.add_argument(
        "-i", "--include", nargs="+", action="append", metavar="FIELD"
    )
    get_parser.add_argument(
        "-e", "--exclude", nargs="+", action="append", metavar="FIELD"
    )
    get_parser.add_argument("-s", "--scope", nargs="+", action="append")
    get_parser.set_defaults(func=get)

    # FILTER COMMANDS
    filter_parser = command.add_parser("filter", help="Filter records from a project.")
    filter_parser.add_argument("project")
    filter_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    filter_parser.add_argument(
        "-i", "--include", nargs="+", action="append", metavar="FIELD"
    )
    filter_parser.add_argument(
        "-e", "--exclude", nargs="+", action="append", metavar="FIELD"
    )
    filter_parser.add_argument("-s", "--scope", nargs="+", action="append")
    filter_parser.add_argument("--format", choices=["tsv", "csv", "json"])
    filter_parser.set_defaults(func=filter)

    # UPDATE COMMANDS
    update_parser = command.add_parser(
        "update",
        help="Update records in a project.",
        parents=[test_parser, multithreaded_parser, cid_action_parser],
    )
    update_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    update_parser.set_defaults(func=update)

    # DELETE COMMANDS
    delete_parser = command.add_parser(
        "delete",
        help="Delete records in a project.",
        parents=[multithreaded_parser, cid_action_parser],
    )
    delete_parser.set_defaults(func=delete)

    args = parser.parse_args()

    if args.command in ["create", "update", "delete"]:
        if args.multithreaded and not (args.csv or args.tsv):
            parser.error("one of the arguments --csv --tsv is required")

        if args.command == "update":
            if args.cid and not args.field:
                parser.error("the following arguments are required: -f/--field")

    args.func(args)
