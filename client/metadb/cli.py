import os
import sys
import csv
import stat
import json
import requests
import argparse
from metadb import version, utils, settings
from metadb.config import Config
from metadb.api import Client


class ConfigRequired:
    def __init__(self):
        self.config = Config()


class ClientRequired(ConfigRequired):
    def __init__(self):
        super().__init__()
        self.client = Client(self.config)


class SessionRequired(ClientRequired):
    def __init__(self, username, env_password):
        super().__init__()
        self.client.continue_session(username=username, env_password=env_password)


class ConfigCommands(ConfigRequired):
    """
    Commands involving creation/altering of the config.
    """

    @classmethod
    def add_commands(cls, command):
        config_parser = command.add_parser("config", help="Config-specific commands.")
        config_commands_parser = config_parser.add_subparsers(
            dest="config_command", metavar="{config-command}", required=True
        )
        create_parser = config_commands_parser.add_parser(
            "create", help="Create a config."
        )
        create_parser.add_argument("--host", help="METADB host name.")
        create_parser.add_argument("--port", type=int, help="METADB port number.")
        create_parser.add_argument(
            "--config-dir",
            help="Path to the config directory.",
        )
        set_default_parser = config_commands_parser.add_parser(
            "setdefault", help="Set the default user."
        )
        set_default_parser.add_argument(
            "username", nargs="?", help="User to be set as the default."
        )
        get_default_parser = config_commands_parser.add_parser(
            "getdefault", help="Get the default user."
        )
        add_user_parser = config_commands_parser.add_parser(
            "adduser",
            help="Add a pre-existing user to the config.",
        )
        add_user_parser.add_argument(
            "username", nargs="?", help="User to be added to the config."
        )
        users_parser = config_commands_parser.add_parser(
            "users", help="List all users in the config."
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

    def set_default(self, username):
        """
        Set the default user in the config.
        """
        self.config.set_default_user(username)
        print(f"The user has been set as the default user.")

    def get_default(self):
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

    def users(self):
        """
        List all users in the config.
        """
        users = self.config.list_users()
        for user in users:
            print(user)


class RegisterCommands(ClientRequired):
    """
    Commands involving registration.
    """

    @classmethod
    def add_commands(cls, command):
        register_parser = command.add_parser("register", help="Register a new user.")

    def register(self):
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

        registration = self.client.register(
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
                self.client.config.add_user(username)
                print("The user has been added to the config.")


class LoginCommands(ClientRequired):
    """
    Commands involving login/logout.
    """

    @classmethod
    def add_commands(cls, command):
        login_parser = command.add_parser("login", help="Log in to metadb.")
        logout_parser = command.add_parser("logout", help="Log out of metadb.")
        logoutall_parser = command.add_parser(
            "logoutall", help="Log out of metadb on all devices."
        )

    def login(self, username, env_password):
        """
        Log in as a user.
        """
        response = self.client.login(
            username=username,
            env_password=env_password,
        )
        utils.print_response(response, status_only=True)

    def logout(self, username, env_password):
        """
        Log out the current user.
        """
        self.client.continue_session(username=username, env_password=env_password)
        response = self.client.logout()
        utils.print_response(response, status_only=True)

    def logoutall(self, username, env_password):
        """
        Log out the current user everywhere.
        """
        self.client.continue_session(username=username, env_password=env_password)
        response = self.client.logoutall()
        utils.print_response(response, status_only=True)


class SiteCommands(SessionRequired):
    """
    Site specific commands.
    """

    @classmethod
    def add_commands(cls, command):
        site_parser = command.add_parser("site", help="Site-specific commands.")
        site_commands_parser = site_parser.add_subparsers(
            dest="site_command", metavar="{site-command}", required=True
        )
        approve_parser = site_commands_parser.add_parser(
            "approve", help="Site-approve another user."
        )
        approve_parser.add_argument("username", help="User to be site-approved.")
        waiting_parser = site_commands_parser.add_parser(
            "waiting",
            help="List users waiting for site approval.",
        )
        users_parser = site_commands_parser.add_parser(
            "users",
            help="List site users.",
        )

    def approve(self, username):
        """
        Site-approve another user.
        """
        approval = self.client.site_approve(username)
        utils.print_response(approval)

    def waiting(self):
        """
        List users waiting for site approval.
        """
        users = self.client.site_list_waiting()
        utils.print_response(users)

    def users(self):
        """
        List site users.
        """
        users = self.client.site_list_users()
        utils.print_response(users)


class AdminCommands(SessionRequired):
    """
    Admin specific commands.
    """

    @classmethod
    def add_commands(cls, command):
        admin_parser = command.add_parser("admin", help="Admin-specific commands.")
        admin_commands_parser = admin_parser.add_subparsers(
            dest="admin_command", metavar="{admin-command}", required=True
        )
        approve_parser = admin_commands_parser.add_parser(
            "approve",
            help="Admin-approve another user.",
        )
        approve_parser.add_argument("username", help="User to be admin-approved.")
        waiting_parser = admin_commands_parser.add_parser(
            "waiting",
            help="List users waiting for admin approval.",
        )
        allusers_parser = admin_commands_parser.add_parser(
            "allusers", help="List all users."
        )

    def approve(self, username):
        """
        Admin-approve another user.
        """
        approval = self.client.admin_approve(username)
        utils.print_response(approval)

    def waiting(self):
        """
        List users waiting for admin approval.
        """
        users = self.client.admin_list_waiting()
        utils.print_response(users)

    def allusers(self):
        """
        List all users.
        """
        users = self.client.admin_list_users()
        utils.print_response(users)


class CreateCommands(SessionRequired):
    """
    Commands for creating records.
    """

    @classmethod
    def add_commands(cls, command):
        create_parser = command.add_parser("create", help="Upload metadata.")
        create_parser.add_argument("project")
        create_exclusive_parser = create_parser.add_mutually_exclusive_group(
            required=True
        )
        create_exclusive_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )
        create_exclusive_parser.add_argument(
            "--csv", help="Upload metadata via a .csv file."
        )
        create_exclusive_parser.add_argument(
            "--tsv", help="Upload metadata via a .tsv file."
        )
        testcreate_parser = command.add_parser(
            "testcreate", help="Test uploading metadata."
        )
        testcreate_parser.add_argument("project")
        testcreate_exclusive_parser = testcreate_parser.add_mutually_exclusive_group(
            required=True
        )
        testcreate_exclusive_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )
        testcreate_exclusive_parser.add_argument(
            "--csv", help="Test uploading metadata via a .csv file."
        )
        testcreate_exclusive_parser.add_argument(
            "--tsv", help="Test uploading metadata via a .tsv file."
        )

    def create(self, project, fields, test=False):
        """
        Post a new record to the database.
        """
        fields = utils.construct_unique_fields_dict(fields)
        creation = self.client.create(project, fields, test=test)
        utils.print_response(creation)

    def csv_create(self, project, csv_path, delimiter=None, test=False):
        """
        Post new records to the database, using a csv or tsv.
        """
        creations = self.client.csv_create(
            project, csv_path, delimiter=delimiter, test=test
        )
        utils.execute_uploads(creations)


class GetCommands(SessionRequired):
    """
    Commands for getting records.
    """

    @classmethod
    def add_commands(cls, command):
        get_parser = command.add_parser("get", help="Get metadata.")
        get_parser.add_argument("project")
        get_parser.add_argument("cid", nargs="?", help="optional")
        get_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )

    def get(self, project, cid, fields):
        """
        Get records from the database.
        """
        fields = utils.construct_fields_dict(fields)

        if cid:
            fields.setdefault("cid", []).append(cid)
            response = self.client.request(
                method=requests.get,
                url=self.client.endpoints["get"](project),
                params=fields,
            )
            utils.print_response(response)

        else:
            results = self.client.get(project, cid, fields)

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


class UpdateCommands(SessionRequired):
    """
    Commands for updating records.
    """

    @classmethod
    def add_commands(cls, command):
        update_parser = command.add_parser("update", help="Update metadata.")
        update_parser.add_argument("project")
        update_parser.add_argument(
            "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
        )
        update_exclusive_parser = update_parser.add_mutually_exclusive_group(
            required=True
        )
        update_exclusive_parser.add_argument("cid", nargs="?", help="optional")
        update_exclusive_parser.add_argument(
            "--csv", help="Update metadata via a .csv file."
        )
        update_exclusive_parser.add_argument(
            "--tsv", help="Update metadata via a .tsv file."
        )

    def update(self, project, cid, fields):
        """
        Update a record in the database.
        """
        fields = utils.construct_unique_fields_dict(fields)
        update = self.client.update(project, cid, fields)
        utils.print_response(update)

    def csv_update(self, project, csv_path, delimiter=None):
        """
        Update records in the database, using a csv or tsv.
        """
        updates = self.client.csv_update(project, csv_path, delimiter=delimiter)
        utils.execute_uploads(updates)


class SuppressCommands(SessionRequired):
    """
    Commands for suppressing (soft deleting) records.
    """

    @classmethod
    def add_commands(cls, command):
        suppress_parser = command.add_parser("suppress", help="Suppress metadata.")
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

    def suppress(self, project, cid):
        """
        Suppress a record in the database.
        """
        suppression = self.client.suppress(project, cid)
        utils.print_response(suppression)

    def csv_suppress(self, project, csv_path, delimiter=None):
        """
        Suppress records in the database, using a csv or tsv.
        """
        suppressions = self.client.csv_suppress(project, csv_path, delimiter=delimiter)
        utils.execute_uploads(suppressions)


class DeleteCommands(SessionRequired):
    """
    Commands for deleting records.
    """

    @classmethod
    def add_commands(cls, command):
        delete_parser = command.add_parser("delete", help="Delete metadata.")
        delete_parser.add_argument("project")
        delete_exclusive_parser = delete_parser.add_mutually_exclusive_group(
            required=True
        )
        delete_exclusive_parser.add_argument("cid", nargs="?", help="optional")
        delete_exclusive_parser.add_argument(
            "--csv", help="Delete metadata via a .csv file."
        )
        delete_exclusive_parser.add_argument(
            "--tsv", help="Delete metadata via a .tsv file."
        )

    def delete(self, project, cid):
        """
        Delete a record in the database.
        """
        deletion = self.client.delete(project, cid)
        utils.print_response(deletion)

    def csv_delete(self, project, csv_path, delimiter=None):
        """
        Delete records in the database, using a csv or tsv.
        """
        deletions = self.client.csv_delete(project, csv_path, delimiter=delimiter)
        utils.execute_uploads(deletions)


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
            if args.config_command == "setdefault":
                config_commands.set_default(args.username)
            elif args.config_command == "getdefault":
                config_commands.get_default()
            elif args.config_command == "adduser":
                config_commands.add_user(args.username)
            elif args.config_command == "users":
                config_commands.users()

    elif args.command == "site":
        site_commands = SiteCommands(args.user, args.env_password)
        if args.site_command == "approve":
            site_commands.approve(args.username)
        elif args.site_command == "waiting":
            site_commands.waiting()
        elif args.site_command == "users":
            site_commands.users()

    elif args.command == "admin":
        admin_commands = AdminCommands(args.user, args.env_password)
        if args.admin_command == "approve":
            admin_commands.approve(args.username)
        elif args.admin_command == "waiting":
            admin_commands.waiting()
        elif args.admin_command == "allusers":
            admin_commands.allusers()

    elif args.command == "register":
        register_commands = RegisterCommands()
        register_commands.register()

    elif args.command in ["login", "logout", "logoutall"]:
        login_commands = LoginCommands()
        if args.command == "login":
            login_commands.login(args.user, args.env_password)
        elif args.command == "logout":
            login_commands.logout(args.user, args.env_password)
        elif args.command == "logoutall":
            login_commands.logoutall(args.user, args.env_password)

    elif args.command in ["create", "testcreate"]:
        create_commands = CreateCommands(args.user, args.env_password)
        if args.field:
            create_commands.create(
                args.project, args.field, test=(args.command == "testcreate")
            )
        elif args.csv:
            create_commands.csv_create(
                args.project, args.csv, test=(args.command == "testcreate")
            )
        elif args.tsv:
            create_commands.csv_create(
                args.project,
                args.tsv,
                delimiter="\t",
                test=(args.command == "testcreate"),
            )

    elif args.command == "get":
        get_commands = GetCommands(args.user, args.env_password)
        get_commands.get(args.project, args.cid, args.field)

    elif args.command == "update":
        update_commands = UpdateCommands(args.user, args.env_password)
        if args.cid and args.field:
            update_commands.update(args.project, args.cid, args.field)
        elif args.csv:
            update_commands.csv_update(args.project, args.csv)
        elif args.tsv:
            update_commands.csv_update(args.project, args.tsv, delimiter="\t")

    elif args.command == "suppress":
        suppress_commands = SuppressCommands(args.user, args.env_password)
        if args.cid:
            suppress_commands.suppress(args.project, args.cid)
        elif args.csv:
            suppress_commands.csv_suppress(args.project, args.csv)
        elif args.tsv:
            suppress_commands.csv_suppress(args.project, args.tsv, delimiter="\t")

    elif args.command == "delete":
        delete_commands = DeleteCommands(args.user, args.env_password)
        if args.cid:
            delete_commands.delete(args.project, args.cid)
        elif args.csv:
            delete_commands.csv_delete(args.project, args.csv)
        elif args.tsv:
            delete_commands.csv_delete(args.project, args.tsv, delimiter="\t")


def get_args():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument(
        "-u",
        "--user",
        help="Which user to execute the command as.",
    )
    user_parser.add_argument(
        "-p",
        "--env-password",
        action="store_true",
        help="If a password is required, the client will look for the env variable with format 'METADB_<user>_PASSWORD'.",
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
    ConfigCommands.add_commands(command)
    SiteCommands.add_commands(command)
    AdminCommands.add_commands(command)
    RegisterCommands.add_commands(command)
    LoginCommands.add_commands(command)
    CreateCommands.add_commands(command)
    GetCommands.add_commands(command)
    UpdateCommands.add_commands(command)
    SuppressCommands.add_commands(command)
    DeleteCommands.add_commands(command)
    args = parser.parse_args()

    if args.command == "update" and (args.cid and not args.field):
        parser.error("the following arguments are required: -f/--field")

    return args


def main():
    args = get_args()
    run(args)
