import os
import stat
import json
import argparse
import pandas as pd
from metadbclient import version, utils, settings
from metadbclient.config import Config
from metadbclient.api import Client


def register():
    """
    Create a new user.
    """
    config = Config()
    client = Client(config)

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

    registration = client.register(
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
        while not check:
            check = input(
                "Would you like to add this account to the config? [y/n]: "
            ).upper()

        if check == "Y":
            results = registration.json()["results"]
            if len(results) != 1:
                raise Exception("Expected only one result in response")

            username = results[0]["username"]
            client.config.add_user(username)
            print("The user has been added to the config.")


def login(username, env_password):
    """
    Log in as a user.
    """
    config = Config()
    client = Client(config)

    response = client.login(
        username=username,
        env_password=env_password,
    )
    utils.print_response(response, status_only=True)


def logout(username, env_password):
    """
    Log out the current user.
    """
    config = Config()
    client = Client(config)
    client.continue_session(username=username, env_password=env_password)

    response = client.logout()
    utils.print_response(response, status_only=True)


def logoutall(username, env_password):
    """
    Log out the current user everywhere.
    """
    config = Config()
    client = Client(config)
    client.continue_session(username=username, env_password=env_password)

    response = client.logoutall()
    utils.print_response(response, status_only=True)


def list_projects(username, env_password):
    """
    Get the current pathogens within the database.
    """
    config = Config()
    client = Client(config)
    client.continue_session(username=username, env_password=env_password)

    projects = client.list_projects()
    utils.print_response(projects)


class ConfigCommands:
    """
    Commands involving creation/altering of the config.
    """

    def __init__(self):
        self.config = Config()

    @classmethod
    def add_commands(cls, command):
        config_parser = command.add_parser(
            "config", help="Commands for creating/manipulating the config."
        )
        config_commands_parser = config_parser.add_subparsers(
            dest="config_command", metavar="{config-command}"
        )

        create_config_parser = config_commands_parser.add_parser(
            "create", help="Create a config for the client."
        )
        create_config_parser.add_argument("--host", help="METADB host name.")
        create_config_parser.add_argument(
            "--port", type=int, help="METADB port number."
        )
        create_config_parser.add_argument(
            "--config-dir",
            help="Path to the config directory.",
        )

        set_default_user_parser = config_commands_parser.add_parser(
            "set-default-user", help="Set the default user in the config of the client."
        )
        set_default_user_parser.add_argument(
            "username", nargs="?", help="User to be set as the default."
        )

        get_default_user_parser = config_commands_parser.add_parser(
            "get-default-user", help="Get the default user in the config of the client."
        )

        add_user_parser = config_commands_parser.add_parser(
            "add-user",
            help="Add a pre-existing metadb user to the config of the client.",
        )
        add_user_parser.add_argument(
            "username", nargs="?", help="User to be added to the config."
        )

        list_config_users_parser = config_commands_parser.add_parser(
            "list-users", help="List all users in the config of the client."
        )

    @classmethod
    def create(cls, host=None, port=None, config_dir=None):
        """
        Generate the config directory and config file.
        """
        if host is None:
            host = utils.get_input("host")

        if port is None:
            port = utils.get_input("port", type=int)

        if config_dir is None:
            config_dir = utils.get_input("config directory")

        config_dir = config_dir.replace("~", os.path.expanduser("~"))

        if os.path.isfile(config_dir):
            raise FileExistsError("Provided path to a file, not a directory")

        if not os.path.isdir(config_dir):
            os.mkdir(config_dir)

        config_file = os.path.join(config_dir, settings.CONFIG_FILE_NAME)

        if os.path.isfile(config_file):
            raise FileExistsError(f"Config file already exists: {config_file}")

        with open(config_file, "w") as config:
            json.dump(
                {"host": host, "port": port, "users": {}, "default_user": None},
                config,
                indent=4,
            )

        # Read-write for OS user only
        os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)

        print("")
        print("Config created successfully.")
        print(
            "Please create the following environment variable to store the path to your config:"
        )
        print("")
        print(f"export METADB_CONFIG_DIR={config_dir}")
        print("")
        print(
            "IMPORTANT: DO NOT CHANGE PERMISSIONS OF CONFIG FILE(S)".center(
                settings.MESSAGE_BAR_WIDTH, "!"
            )
        )
        warning_message = [
            "The file(s) within your config directory store sensitive information such as tokens.",
            "They have been created with the permissions needed to keep your information safe.",
            "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your tokens!",
        ]
        for line in warning_message:
            print(line)
        print("".center(settings.MESSAGE_BAR_WIDTH, "!"))

    def set_default_user(self, username):
        """
        Set the default user in the config.
        """
        self.config.set_default_user(username)
        print(f"The user has been set as the default user.")

    def get_default_user(self):
        """
        Get the default user in the config.
        """
        default_user = self.config.get_default_user()
        print(default_user)

    def add_user(self, username):
        """
        Add user to the config.
        """
        self.config.add_user(username)
        print("The user has been added to the config.")

    def list_users(self):
        """
        List all users in the config.
        """
        users = self.config.list_users()
        for user in users:
            print(user)


class SiteCommands:
    """
    Site specific commands.
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):
        site_parser = command.add_parser("site", help="Site-specific commands.")
        site_commands_parser = site_parser.add_subparsers(
            dest="site_command", metavar="{site-command}"
        )

        site_approve_parser = site_commands_parser.add_parser(
            "approve", parents=[user_parser], help="Approve another user in metadb."
        )
        site_approve_parser.add_argument("username", help="User to be approved.")

        site_waiting_parser = site_commands_parser.add_parser(
            "list-waiting",
            parents=[user_parser],
            help="List users waiting for site approval.",
        )

        site_list_users_parser = site_commands_parser.add_parser(
            "list-users",
            parents=[user_parser],
            help="List site users.",
        )

    def approve(self, username):
        """
        Approve another user.
        """
        approval = self.client.site_approve(username)
        utils.print_response(approval)

    def list_waiting(self):
        """
        List users waiting for site approval.
        """
        users = self.client.site_list_waiting()
        utils.print_response(users)

    def list_users(self):
        """
        List site users.
        """
        users = self.client.site_list_users()
        utils.print_response(users)


class AdminCommands:
    """
    Admin specific commands.
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):
        admin_parser = command.add_parser("admin", help="Admin-specific commands.")
        admin_commands_parser = admin_parser.add_subparsers(
            dest="admin_command", metavar="{admin-command}"
        )

        admin_approve_parser = admin_commands_parser.add_parser(
            "approve",
            parents=[user_parser],
            help="Admin-approve another user in metadb.",
        )
        admin_approve_parser.add_argument("username", help="User to be admin-approved.")

        admin_waiting_parser = admin_commands_parser.add_parser(
            "list-waiting",
            parents=[user_parser],
            help="List users waiting for admin approval.",
        )

        admin_list_users_parser = admin_commands_parser.add_parser(
            "list-users", parents=[user_parser], help="List all users in metadb."
        )

    def approve(self, username):
        """
        Admin-approve another user.
        """
        approval = self.client.admin_approve(username)
        utils.print_response(approval)

    def list_waiting(self):
        """
        List users waiting for admin approval.
        """
        users = self.client.admin_list_waiting()
        utils.print_response(users)

    def list_users(self):
        """
        List all users.
        """
        users = self.client.admin_list_users()
        utils.print_response(users)


class CreateCommands:
    """
    Commands for creating.
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):
        create_parser = command.add_parser(
            "create", parents=[user_parser], help="Upload pathogen metadata to metadb."
        )
        create_parser.add_argument("project")
        create_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )

        csv_create_parser = command.add_parser(
            "csv-create",
            parents=[user_parser],
            help="Upload pathogen metadata to metadb via a .csv file.",
        )
        csv_create_parser.add_argument("project")
        csv_create_parser.add_argument("csv")

        tsv_create_parser = command.add_parser(
            "tsv-create",
            parents=[user_parser],
            help="Upload pathogen metadata to metadb via a .tsv file.",
        )
        tsv_create_parser.add_argument("project")
        tsv_create_parser.add_argument("tsv")

    def create(self, project, fields):
        """
        Post a new pathogen record to the database.
        """
        fields = utils.construct_unique_fields_dict(fields)
        creation = self.client.create(project, fields)
        utils.print_response(creation)

    def csv_create(self, project, csv_path):
        """
        Post new pathogen records to the database, using a csv.
        """
        creations = self.client.csv_create(project, csv_path)
        utils.execute_uploads(creations)

    def tsv_create(self, project, tsv_path):
        """
        Post new pathogen records to the database, using a tsv.
        """
        creations = self.client.csv_create(project, tsv_path, delimiter="\t")
        utils.execute_uploads(creations)


class GetCommands:
    """
    Commands for getting.
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):
        get_parser = command.add_parser(
            "get", parents=[user_parser], help="Get pathogen metadata from metadb."
        )
        get_parser.add_argument("project")
        get_parser.add_argument("cid", nargs="?", help="optional")
        get_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )

    def get(self, project, cid, fields):
        """
        Get pathogen records from the database.
        """
        fields = utils.construct_fields_dict(fields)

        results = self.client.get(project, cid, fields)

        result = next(results)
        if result.ok:
            table = pd.json_normalize(result.json()["results"])
            print(table.to_csv(index=False, sep="\t"), end="")
        else:
            utils.print_response(result)

        for result in results:
            if result.ok:
                table = pd.json_normalize(result.json()["results"])
                print(table.to_csv(index=False, sep="\t", header=False), end="")
            else:
                utils.print_response(result)


class UpdateCommands:
    """
    Commands for updating.
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):
        update_parser = command.add_parser(
            "update",
            parents=[user_parser],
            help="Update pathogen metadata within metadb.",
        )
        update_parser.add_argument("project")
        update_parser.add_argument("cid")
        update_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )

        csv_update_parser = command.add_parser(
            "csv-update",
            parents=[user_parser],
            help="Update pathogen metadata within metadb via a .csv file.",
        )
        csv_update_parser.add_argument("project")
        csv_update_parser.add_argument("csv")

        tsv_update_parser = command.add_parser(
            "tsv-update",
            parents=[user_parser],
            help="Update pathogen metadata within metadb via a .tsv file.",
        )
        tsv_update_parser.add_argument("project")
        tsv_update_parser.add_argument("tsv")

    def update(self, project, cid, fields):
        """
        Update a pathogen record in the database.
        """
        fields = utils.construct_unique_fields_dict(fields)
        update = self.client.update(project, cid, fields)
        utils.print_response(update)

    def csv_update(self, project, csv_path):
        """
        Update pathogen records in the database, using a csv.
        """
        updates = self.client.csv_update(project, csv_path)
        utils.execute_uploads(updates)

    def tsv_update(self, project, tsv_path):
        """
        Update pathogen records in the database, using a tsv.
        """
        updates = self.client.csv_update(project, tsv_path, delimiter="\t")
        utils.execute_uploads(updates)


class SuppressCommands:
    """
    Commands for suppressing (soft deleting).
    """

    def __init__(self, username, env_password):
        config = Config()
        self.client = Client(config)
        self.client.continue_session(username=username, env_password=env_password)

    @classmethod
    def add_commands(cls, command, user_parser):

        suppress_parser = command.add_parser(
            "suppress",
            parents=[user_parser],
            help="Suppress pathogen metadata within metadb.",
        )
        suppress_parser.add_argument("project")
        suppress_parser.add_argument("cid")

        csv_suppress_parser = command.add_parser(
            "csv-suppress",
            parents=[user_parser],
            help="Suppress pathogen metadata within metadb via a .csv file.",
        )
        csv_suppress_parser.add_argument("project")
        csv_suppress_parser.add_argument("csv")

        tsv_suppress_parser = command.add_parser(
            "tsv-suppress",
            parents=[user_parser],
            help="Suppress pathogen metadata within metadb via a .tsv file.",
        )
        tsv_suppress_parser.add_argument("project")
        tsv_suppress_parser.add_argument("tsv")

    def suppress(self, project, cid):
        """
        Suppress a pathogen record in the database.
        """
        suppression = self.client.suppress(project, cid)
        utils.print_response(suppression)

    def csv_suppress(self, project, csv_path):
        """
        Suppress pathogen records in the database, using a csv.
        """
        suppressions = self.client.csv_suppress(project, csv_path)
        utils.execute_uploads(suppressions)

    def tsv_suppress(self, project, tsv_path):
        """
        Suppress pathogen records in the database, using a tsv.
        """
        suppressions = self.client.csv_suppress(project, tsv_path, delimiter="\t")
        utils.execute_uploads(suppressions)


def run(args):
    if args.command == "config":
        if args.config_command == "create":
            ConfigCommands.create(
                host=args.host,
                port=args.port,
                config_dir=args.config_dir,
            )
        else:
            config_commands = ConfigCommands()
            if args.config_command == "set-default-user":
                config_commands.set_default_user(args.username)

            elif args.config_command == "get-default-user":
                config_commands.get_default_user()

            elif args.config_command == "add-user":
                config_commands.add_user(args.username)

            elif args.config_command == "list-users":
                config_commands.list_users()

    elif args.command == "site":
        site_commands = SiteCommands(
            username=args.user,
            env_password=args.env_password,
        )

        if args.site_command == "approve":
            site_commands.approve(args.username)

        elif args.site_command == "list-waiting":
            site_commands.list_waiting()

        elif args.site_command == "list-users":
            site_commands.list_users()

    elif args.command == "admin":
        admin_commands = AdminCommands(
            username=args.user,
            env_password=args.env_password,
        )

        if args.admin_command == "approve":
            admin_commands.approve(args.username)

        elif args.admin_command == "list-waiting":
            admin_commands.list_waiting()

        elif args.admin_command == "list-users":
            admin_commands.list_users()

    elif args.command == "register":
        register()

    elif args.command == "login":
        login(args.user, args.env_password)

    elif args.command == "logout":
        logout(args.user, args.env_password)

    elif args.command == "logoutall":
        logoutall(args.user, args.env_password)

    elif args.command == "list-pathogens":
        list_projects(args.user, args.env_password)

    elif args.command in ["create", "csv-create", "tsv-create"]:
        create_commands = CreateCommands(args.user, args.env_password)

        if args.command == "create":
            create_commands.create(args.project, args.field)

        elif args.command == "csv-create":
            create_commands.csv_create(args.project, args.csv)

        elif args.command == "tsv-create":
            create_commands.tsv_create(args.project, args.tsv)

    elif args.command == "get":
        get_commands = GetCommands(args.user, args.env_password)

        get_commands.get(args.project, args.cid, args.field)

    elif args.command in ["update", "csv-update", "tsv-update"]:
        update_commands = UpdateCommands(args.user, args.env_password)

        if args.command == "update":
            update_commands.update(args.project, args.cid, args.field)

        elif args.command == "csv-update":
            update_commands.csv_update(args.project, args.csv)

        elif args.command == "tsv-update":
            update_commands.tsv_update(args.project, args.tsv)

    elif args.command in ["suppress", "csv-suppress", "tsv-suppress"]:
        suppress_commands = SuppressCommands(args.user, args.env_password)

        if args.command == "suppress":
            suppress_commands.suppress(args.project, args.cid)

        elif args.command == "csv-suppress":
            suppress_commands.csv_suppress(args.project, args.csv)

        elif args.command == "tsv-suppress":
            suppress_commands.tsv_suppress(args.project, args.tsv)


def get_args():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument(
        "-u",
        "--user",
        help="Which user to execute the command as. If not provided, the config's default user is chosen.",
    )
    user_parser.add_argument(
        "-p",
        "--env-password",
        action="store_true",
        help="If a password is required, the client will look for the env variable with format 'METADB_<user>_PASSWORD'.",
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version.__version__,
        help="Client version number.",
    )

    command = parser.add_subparsers(dest="command", metavar="{command}")

    ConfigCommands.add_commands(command)

    SiteCommands.add_commands(command, user_parser=user_parser)

    AdminCommands.add_commands(command, user_parser=user_parser)

    register_parser = command.add_parser(
        "register", help="Register a new user in metadb."
    )

    login_parser = command.add_parser(
        "login", parents=[user_parser], help="Log in to metadb."
    )

    logout_parser = command.add_parser(
        "logout",
        parents=[user_parser],
        help="Log out of metadb.",
    )

    logoutall_parser = command.add_parser(
        "logoutall",
        parents=[user_parser],
        help="Log out of metadb everywhere.",
    )

    projects_parser = command.add_parser(
        "list-pathogens",
        parents=[user_parser],
        help="List all pathogens in metadb.",
    )

    CreateCommands.add_commands(command, user_parser=user_parser)

    GetCommands.add_commands(command, user_parser=user_parser)

    UpdateCommands.add_commands(command, user_parser=user_parser)

    SuppressCommands.add_commands(command, user_parser=user_parser)

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    run(args)
