import os
import stat
import json
from onyx import utils, settings


class Config:
    def __init__(self, path=None):
        """
        Initialise the config.

        If a `path` was not provided, looks for the environment variable given by `settings.CONFIG_DIR_ENV_VAR`.
        """
        # Locate the config
        dir_path, file_path = self.locate_config(dir_path=path)

        # Load the config
        with open(file_path) as config_file:
            config = json.load(config_file)

        # Validate the config structure
        self.validate_config(config)

        # Set up the config object
        self.dir_path = dir_path
        self.file_path = file_path
        self.host = config["host"]
        self.port = config["port"]
        self.users = config["users"]
        self.default_user = config["default_user"]

    def locate_config(self, dir_path=None):
        """
        If a `dir_path` was provided, confirm this is a directory containing a config file.

        Otherwise, use `settings.CONFIG_DIR_ENV_VAR`, and confirm that this is a directory that contains a config file.
        """
        if dir_path:
            # Check config dir path is a directory
            if not os.path.isdir(dir_path):
                raise FileNotFoundError(f"'{dir_path}' does not exist")

            # Check config file path is a file
            file_path = os.path.join(dir_path, settings.CONFIG_FILE_NAME)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Config file does not exist in directory '{dir_path}'"
                )

        else:
            # Find the config directory
            dir_path = os.environ[settings.CONFIG_DIR_ENV_VAR]

            # Check config dir path is a directory
            if not os.path.isdir(dir_path):
                raise FileNotFoundError(
                    f"'{settings.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist"
                )

            # Check config file path is a file
            file_path = os.path.join(dir_path, settings.CONFIG_FILE_NAME)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Config file does not exist in directory '{dir_path}'"
                )

        return dir_path, file_path

    def validate_config(self, config):
        """
        Avoid a million KeyErrors due to problems with the config file.
        """
        for field in settings.CONFIG_FIELDS:
            if field not in config:
                raise KeyError(f"'{field}' key is missing from the config file")

        for user, ufields in config["users"].items():
            for field in settings.USER_FIELDS:
                if field not in ufields:
                    raise KeyError(
                        f"'{field}' key is missing from user '{user}' in the config file"
                    )

    def write_token(self, username, token, expiry):
        with open(self.users[username]["token"], "w") as token_file:
            json.dump({"token": token, "expiry": expiry}, token_file, indent=4)

    def add_user(self, username=None):
        """
        Add user to the config.
        """
        if username is None:
            username = utils.get_input("username")

        # Username is case-insensitive
        username = username.lower()

        token_path = os.path.abspath(
            os.path.join(self.dir_path, username + settings.TOKENS_FILE_POSTFIX)
        )
        self.users[username] = {"token": token_path}

        # Reload the config incase its changed
        # Not perfect but better than just blanket overwriting the file
        dir_path, file_path = self.locate_config(dir_path=self.dir_path)
        self.dir_path = dir_path
        self.file_path = file_path

        # Load the config
        with open(self.file_path) as current_config_file:
            current_config = json.load(current_config_file)

        # Validate the config structure
        self.validate_config(current_config)

        # Update the config
        self.host = current_config["host"]
        self.port = current_config["port"]
        self.users.update(current_config["users"])

        # If there is only one user in the config, make them the default_user
        if len(self.users) == 1:
            self.default_user = username
        else:
            self.default_user = current_config["default_user"]

        # Write to the config file
        with open(self.file_path, "w") as config_file:
            json.dump(
                {
                    "host": self.host,
                    "port": self.port,
                    "users": self.users,
                    "default_user": self.default_user,
                },
                config_file,
                indent=4,
            )

        # Create user tokens file
        with open(token_path, "w") as token:
            json.dump({"token": None, "expiry": None}, token, indent=4)

        # Read-write for OS user only
        os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)

    def set_default_user(self, username=None):
        """
        Set the default user in the config.
        """
        if username is None:
            username = utils.get_input("username")

        # Username is case-insensitive
        username = username.lower()

        if username not in self.users:
            raise KeyError(
                f"User '{username}' is not in the config. Add them using the add-user command"
            )

        self.default_user = username

        with open(self.file_path, "w") as config_file:
            json.dump(
                {
                    "host": self.host,
                    "port": self.port,
                    "users": self.users,
                    "default_user": self.default_user,
                },
                config_file,
                indent=4,
            )

    def get_default_user(self):
        """
        Get the default user in the config.
        """
        return self.default_user

    def list_users(self):
        """
        Get a list of the users in the config.
        """
        return [username for username in self.users]
