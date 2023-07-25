import os
import sys
import csv
import stat
import json
import requests
import argparse
from . import version, utils, config
from .api import OnyxClient


def config_required(func):
    def wrapped_func(args):
        conf = config.OnyxConfig()
        return func(conf, args)

    return wrapped_func


def client_required(func):
    def wrapped_func(args):
        conf = config.OnyxConfig()
        client = OnyxClient(
            config=conf,
            username=args.user,
            env_password=args.envpass,
        )
        return func(client, args)

    return wrapped_func


def create_config(args):
    """
    Generate the config directory and config file.
    """
    domain = args.domain
    config_dir = args.config_dir

    if domain is None:
        domain = utils.get_input("domain")

    if config_dir is None:
        config_dir = utils.get_input("config directory")

    config_dir = config_dir.replace("~", os.path.expanduser("~"))

    if os.path.isfile(config_dir):
        raise FileExistsError("Provided path to a file, not a directory.")

    if not os.path.isdir(config_dir):
        os.mkdir(config_dir)

    config_file_path = os.path.join(config_dir, config.CONFIG_FILE_NAME)

    if os.path.isfile(config_file_path):
        print(f"Config file already exists: {os.path.abspath(config_file_path)}")
        print("If you wish to overwrite this config, please delete this file.")
        exit()

    with open(config_file_path, "w") as config_file:
        json.dump(
            {"domain": domain, "users": {}, "default_user": None},
            config_file,
            indent=4,
        )

    # Read-write for OS user only
    os.chmod(config_file_path, stat.S_IRUSR | stat.S_IWUSR)

    print("Config created successfully.")
    print(
        "Please create the following environment variable to store the path to your config:"
    )
    print("")
    print(f"export ONYX_CLIENT_CONFIG={os.path.abspath(config_dir)}")
    print("")
    print("IMPORTANT: DO NOT CHANGE PERMISSIONS OF CONFIG FILE(S)".center(100, "!"))
    warning_message = [
        "The file(s) within your config directory store sensitive information such as tokens.",
        "They have been created with the permissions needed to keep your information safe.",
        "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your tokens!",
    ]
    for line in warning_message:
        print(line)
    print("".center(100, "!"))


@config_required
def set_default_user(conf: config.OnyxConfig, args):
    """
    Set the default user in the config.
    """
    username = args.username

    if username is None:
        username = utils.get_input("username")

    conf.set_default_user(username)
    print(f"User '{username}' has been set as the default user.")


@config_required
def get_default_user(conf: config.OnyxConfig, args):
    """
    Get the default user in the config.
    """
    default_user = conf.get_default_user()
    print(default_user)


@config_required
def add_user(conf: config.OnyxConfig, args):
    """
    Add user to the config.
    """
    username = args.username

    if username is None:
        username = utils.get_input("username")

    conf.add_user(username)
    print(f"User '{username}' has been added to the config.")


@config_required
def list_users(conf: config.OnyxConfig, args):
    """
    List all users in the config.
    """
    users = conf.list_users()
    for user in users:
        print(user)


@config_required
def register(conf: config.OnyxConfig, args):
    """
    Create a new user.
    """
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

    registration = OnyxClient.register(
        conf,
        first_name=first_name,
        last_name=last_name,
        email=email,
        site=site,
        password=password,
    )

    utils.print_response(registration)

    if registration.ok:
        print("Account created successfully.")
        check = ""
        while check not in ["Y", "N"]:
            check = input(
                "Would you like to add this account to the config? [y/n]: "
            ).upper()

        username = registration.json()["data"]["username"]

        if check == "Y":
            conf.add_user(username)
            print(f"User '{username}' has been added to the config.")
        else:
            print(f"User '{username}' has not been added to the config.")


@client_required
def login(client: OnyxClient, args):
    """
    Log in as a user.
    """
    response = client.login()
    utils.print_response(response, status_only=True)


@client_required
def logout(client: OnyxClient, args):
    """
    Log out the current user.
    """
    response = client.logout()
    utils.print_response(response, status_only=True)


@client_required
def logoutall(client: OnyxClient, args):
    """
    Log out the current user everywhere.
    """
    response = client.logoutall()
    utils.print_response(response, status_only=True)


@client_required
def site_approve(client: OnyxClient, args):
    """
    Site-approve another user.
    """
    approval = client.site_approve(args.username)
    utils.print_response(approval)


@client_required
def site_list_waiting(client: OnyxClient, args):
    """
    List users waiting for site approval.
    """
    users = client.site_list_waiting()
    utils.print_response(users)


@client_required
def site_list_users(client: OnyxClient, args):
    """
    List site users.
    """
    users = client.site_list_users()
    utils.print_response(users)


@client_required
def admin_approve(client: OnyxClient, args):
    """
    Admin-approve another user.
    """
    approval = client.admin_approve(args.username)
    utils.print_response(approval)


@client_required
def admin_list_waiting(client: OnyxClient, args):
    """
    List users waiting for admin approval.
    """
    users = client.admin_list_waiting()
    utils.print_response(users)


@client_required
def admin_list_users(client: OnyxClient, args):
    """
    List all users.
    """
    users = client.admin_list_users()
    utils.print_response(users)


@client_required
def create(client: OnyxClient, args):
    """
    Post new records to the database.
    """
    if args.field:
        fields = utils.construct_unique_fields_dict(args.field)
        creation = client._create(args.project, fields, test=args.test)
        utils.print_response(creation)

    elif args.csv:
        creations = client._csv_create(
            args.project,
            csv_path=args.csv,
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(creations)

    elif args.tsv:
        creations = client._csv_create(
            args.project,
            csv_path=args.tsv,
            delimiter="\t",
            multithreaded=args.multithreaded,
            test=args.test,
        )
        utils.execute_uploads(creations)


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

    results = client.filter(
        args.project, fields, include=include, exclude=exclude, scope=scope
    )

    try:
        result = next(results, None)
        if result:
            writer = csv.DictWriter(
                sys.stdout, delimiter="\t", fieldnames=result.keys()
            )
            writer.writeheader()
            writer.writerow(result)

            for result in results:
                writer.writerow(result)
    except requests.HTTPError:
        pass


@client_required
def update(client: OnyxClient, args):
    """
    Update records in the database.
    """
    if args.cid and args.field:
        fields = utils.construct_unique_fields_dict(args.field)
        update = client._update(args.project, args.cid, fields, test=args.test)
        utils.print_response(update)

    elif args.csv:
        updates = client._csv_update(
            args.project,
            csv_path=args.csv,
            test=args.test,
        )
        utils.execute_uploads(updates)

    elif args.tsv:
        updates = client._csv_update(
            args.project,
            csv_path=args.tsv,
            delimiter="\t",
            test=args.test,
        )
        utils.execute_uploads(updates)


@client_required
def suppress(client: OnyxClient, args):
    """
    Suppress records in the database.
    """
    if args.cid:
        suppression = client._suppress(args.project, args.cid, test=args.test)
        utils.print_response(suppression)

    elif args.csv:
        suppressions = client._csv_suppress(
            args.project,
            csv_path=args.csv,
            test=args.test,
        )
        utils.execute_uploads(suppressions)

    elif args.tsv:
        suppressions = client._csv_suppress(
            args.project,
            csv_path=args.tsv,
            delimiter="\t",
            test=args.test,
        )
        utils.execute_uploads(suppressions)


@client_required
def delete(client: OnyxClient, args):
    """
    Delete records in the database.
    """
    if args.cid:
        deletion = client._delete(args.project, args.cid, test=args.test)
        utils.print_response(deletion)

    elif args.csv:
        deletions = client._csv_delete(
            args.project,
            csv_path=args.csv,
            test=args.test,
        )
        utils.execute_uploads(deletions)

    elif args.tsv:
        deletions = client._csv_delete(
            args.project,
            csv_path=args.tsv,
            delimiter="\t",
            test=args.test,
        )
        utils.execute_uploads(deletions)


@client_required
def choices(client: OnyxClient, args):
    """
    View choices for a field.
    """
    choices = client._choices(args.project, args.field)
    utils.print_response(choices)


def main():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument(
        "-u",
        "--user",
        help="Which user to execute the command as.",
    )
    user_parser.add_argument(
        "--envpass",
        action="store_true",
        help="When a password is required, the client will use the env variable with format 'ONYX_<USER>_PASSWORD'.",
    )
    parser = argparse.ArgumentParser(parents=[user_parser])
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version.__version__,
        help="Client version number.",
    )
    command = parser.add_subparsers(dest="command", metavar="{command}", required=True)

    # CONFIG COMMANDS
    config_parser = command.add_parser("config", help="Config-specific commands.")
    config_commands_parser = config_parser.add_subparsers(
        dest="config_command", metavar="{config-command}", required=True
    )
    create_config_parser = config_commands_parser.add_parser(
        "create", help="Create a config."
    )
    create_config_parser.add_argument("--domain", help="Onyx domain name.")
    create_config_parser.add_argument(
        "--config-dir",
        help="Path to the config directory.",
    )
    create_config_parser.set_defaults(func=create_config)
    set_default_user_parser = config_commands_parser.add_parser(
        "setdefault", help="Set the default user."
    )
    set_default_user_parser.add_argument(
        "username", nargs="?", help="User to be set as the default."
    )
    set_default_user_parser.set_defaults(func=set_default_user)
    get_default_user_parser = config_commands_parser.add_parser(
        "getdefault", help="Get the default user."
    )
    get_default_user_parser.set_defaults(func=get_default_user)
    add_user_parser = config_commands_parser.add_parser(
        "adduser",
        help="Add a pre-existing user to the config.",
    )
    add_user_parser.add_argument(
        "username", nargs="?", help="User to be added to the config."
    )
    add_user_parser.set_defaults(func=add_user)
    list_users_parser = config_commands_parser.add_parser(
        "users", help="List all users in the config."
    )
    list_users_parser.set_defaults(func=list_users)

    # REGISTER COMMANDS
    register_parser = command.add_parser("register", help="Register a new user.")
    register_parser.set_defaults(func=register)

    # LOGIN COMMANDS
    login_parser = command.add_parser("login", help="Log in to onyx.")
    login_parser.set_defaults(func=login)
    logout_parser = command.add_parser("logout", help="Log out of onyx.")
    logout_parser.set_defaults(func=logout)
    logoutall_parser = command.add_parser(
        "logoutall", help="Log out of onyx everywhere."
    )
    logoutall_parser.set_defaults(func=logoutall)

    # SITE COMMANDS
    site_parser = command.add_parser("site", help="Site-specific commands.")
    site_commands_parser = site_parser.add_subparsers(
        dest="site_command", metavar="{site-command}", required=True
    )
    site_approve_parser = site_commands_parser.add_parser(
        "approve", help="Site-approve another user."
    )
    site_approve_parser.add_argument("username", help="User to be site-approved.")
    site_approve_parser.set_defaults(func=site_approve)
    site_list_waiting_parser = site_commands_parser.add_parser(
        "waiting",
        help="List users waiting for site approval.",
    )
    site_list_waiting_parser.set_defaults(func=site_list_waiting)
    site_list_users_parser = site_commands_parser.add_parser(
        "users",
        help="List site users.",
    )
    site_list_users_parser.set_defaults(func=site_list_users)

    # ADMIN COMMANDS
    admin_parser = command.add_parser("admin", help="Admin-specific commands.")
    admin_commands_parser = admin_parser.add_subparsers(
        dest="admin_command", metavar="{admin-command}", required=True
    )
    admin_approve_parser = admin_commands_parser.add_parser(
        "approve",
        help="Admin-approve another user.",
    )
    admin_approve_parser.add_argument("username", help="User to be admin-approved.")
    admin_approve_parser.set_defaults(func=admin_approve)
    admin_list_waiting_parser = admin_commands_parser.add_parser(
        "waiting",
        help="List users waiting for admin approval.",
    )
    admin_list_waiting_parser.set_defaults(func=admin_list_waiting)
    admin_list_users_parser = admin_commands_parser.add_parser(
        "allusers", help="List all users."
    )
    admin_list_users_parser.set_defaults(func=admin_list_users)

    # CREATE COMMANDS
    create_parser = command.add_parser("create", help="Upload metadata records.")
    create_parser.add_argument("project")
    create_exclusive_parser = create_parser.add_mutually_exclusive_group(required=True)
    create_exclusive_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    create_exclusive_parser.add_argument(
        "--csv", help="Upload metadata via a .csv file."
    )
    create_exclusive_parser.add_argument(
        "--tsv", help="Upload metadata via a .tsv file."
    )
    create_parser.add_argument(
        "--test", action="store_true", help="Run the command as a test."
    )
    create_parser.add_argument("--multithreaded", action="store_true")
    create_parser.set_defaults(func=create)

    # GET COMMANDS
    get_parser = command.add_parser("get", help="Get a metadata record.")
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
    filter_parser = command.add_parser("filter", help="Filter metadata records.")
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
    filter_parser.set_defaults(func=filter)

    # UPDATE COMMANDS
    update_parser = command.add_parser("update", help="Update metadata records.")
    update_parser.add_argument("project")
    update_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    update_exclusive_parser = update_parser.add_mutually_exclusive_group(required=True)
    update_exclusive_parser.add_argument("cid", nargs="?", help="optional")
    update_exclusive_parser.add_argument(
        "--csv", help="Update metadata via a .csv file."
    )
    update_exclusive_parser.add_argument(
        "--tsv", help="Update metadata via a .tsv file."
    )
    update_parser.add_argument(
        "--test", action="store_true", help="Run the command as a test."
    )
    update_parser.set_defaults(func=update)

    # SUPPRESS COMMANDS
    suppress_parser = command.add_parser("suppress", help="Suppress metadata records.")
    suppress_parser.add_argument("project")
    suppress_exclusive_parser = suppress_parser.add_mutually_exclusive_group(
        required=True
    )
    suppress_exclusive_parser.add_argument("cid", nargs="?", help="optional")
    suppress_exclusive_parser.add_argument(
        "--csv", help="Suppress metadata via a .csv file."
    )
    suppress_exclusive_parser.add_argument(
        "--tsv", help="Suppress metadata via a .tsv file."
    )
    suppress_parser.add_argument(
        "--test", action="store_true", help="Run the command as a test."
    )
    suppress_parser.set_defaults(func=suppress)

    # DELETE COMMANDS
    delete_parser = command.add_parser("delete", help="Delete metadata records.")
    delete_parser.add_argument("project")
    delete_exclusive_parser = delete_parser.add_mutually_exclusive_group(required=True)
    delete_exclusive_parser.add_argument("cid", nargs="?", help="optional")
    delete_exclusive_parser.add_argument(
        "--csv", help="Delete metadata via a .csv file."
    )
    delete_exclusive_parser.add_argument(
        "--tsv", help="Delete metadata via a .tsv file."
    )
    delete_parser.add_argument(
        "--test", action="store_true", help="Run the command as a test."
    )
    delete_parser.set_defaults(func=delete)

    # PROJECT COMMANDS
    choices_parser = command.add_parser("choices", help="View choices for a field.")
    choices_parser.add_argument("project")
    choices_parser.add_argument("field")
    choices_parser.set_defaults(func=choices)

    args = parser.parse_args()

    if args.command == "create" and args.multithreaded and not (args.csv or args.tsv):
        parser.error("one of the arguments --csv --tsv is required")

    if args.command == "update" and (args.cid and not args.field):
        parser.error("the following arguments are required: -f/--field")

    args.func(args)
