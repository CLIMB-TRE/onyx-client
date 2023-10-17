import os
import stat
import json
from typing import Any, List, Dict, Tuple, Optional, Union


# Central config file
CONFIG_FILE_NAME = "config.json"

# Environment variables
ONYX_CLIENT_CONFIG = "ONYX_CLIENT_CONFIG"  # Config directory path

# Required config fields
CONFIG_FIELDS = ["domain", "users", "default_user"]

# Required fields for each user in the config
USER_FIELDS = ["token"]

# User tokens file name
USER_TOKENS_FILE = lambda username: f"{username.lower()}_token.json"


class OnyxConfig:
    """
    Class for managing the config directory (and files within) that are used by `OnyxClient`.
    """

    def __init__(self, directory: Optional[str] = None) -> None:
        """Initialise the config.

        Parameters
        ----------
        directory : str, optional
            Path to config directory. If not provided, uses directory stored in the `ONYX_CLIENT_CONFIG` environment variable.
        """

        # Locate the config
        directory, file_path = self._locate_config(directory=directory)

        # Load the config
        with open(file_path) as config_file:
            config = json.load(config_file)

        # Validate the structure of the config
        self._validate_config(config)

        # Set up the config object
        self.directory = directory
        self.file_path = file_path
        self.domain = config["domain"]  # TODO: Environment variable for the domain
        self.users = config["users"]
        self.default_user = config["default_user"]

    def _locate_config(self, directory: Optional[str] = None) -> Tuple[str, str]:
        """Locate the config directory, and confirm that it contains a config file.

        Parameters
        ----------
        directory : str, optional
            Path to config directory. If not provided, uses directory stored in the `ONYX_CLIENT_CONFIG` environment variable.

        Returns
        -------
        tuple
            Two strings: the config directory path, and the config file path.
        """

        if directory:
            # Check config dir path is a directory
            if not os.path.isdir(directory):
                raise FileNotFoundError(f"'{directory}' does not exist.")

            # Check config file path is a file
            file_path = os.path.join(directory, CONFIG_FILE_NAME)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Config file does not exist in directory '{directory}'."
                )
        else:
            # Find the config directory
            directory = os.environ[ONYX_CLIENT_CONFIG]

            # Check config dir path is a directory
            if not os.path.isdir(directory):
                raise FileNotFoundError(
                    f"'{ONYX_CLIENT_CONFIG}' points to a directory that does not exist."
                )

            # Check config file path is a file
            file_path = os.path.join(directory, CONFIG_FILE_NAME)
            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Config file does not exist in directory '{directory}'."
                )

        return directory, file_path

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Avoid a million KeyErrors due to problems with the config file.

        Parameters
        ----------
        config : dict
            Config file loaded into a python dict.
        """

        for field in CONFIG_FIELDS:
            if field not in config:
                raise KeyError(f"'{field}' key is missing from the config file.")

        for user, ufields in config["users"].items():
            for field in USER_FIELDS:
                if field not in ufields:
                    raise KeyError(
                        f"'{field}' key is missing from user '{user}' in the config file."
                    )

    def write_token(
        self, username: str, token: Union[str, None], expiry: Union[str, None]
    ) -> None:
        """Update the tokens file for `username`.

        Parameters
        ----------
        username : str
            User within config who is having tokens updated.
        token : str, optional
            The token being written to their tokens file.
        expiry : str, optional
            Expiry of the token.
        """

        with open(
            os.path.join(self.directory, self.users[username]["token"]), "w"
        ) as token_file:
            json.dump({"token": token, "expiry": expiry}, token_file, indent=4)

    def add_user(self, username: str) -> None:
        """Add a new user to the config.

        Parameters
        ----------
        username : str
            Name of the user being added.
        """

        # Reload the config incase its changed
        # Not perfect but better than just blanket overwriting the file
        directory, file_path = self._locate_config(directory=self.directory)
        self.directory = directory
        self.file_path = file_path

        # Load the config
        with open(self.file_path) as current_config_file:
            current_config = json.load(current_config_file)

        # Validate the config structure
        self._validate_config(current_config)

        # Update the config with current information
        self.domain = current_config["domain"]
        self.users.update(current_config["users"])

        # Add the new user and their token file name to the config users
        username = username.lower()  # Username is case-insensitive
        self.users[username] = {"token": USER_TOKENS_FILE(username)}

        # If there is only one user in the config, make them the default_user
        if len(self.users) == 1:
            self.default_user = username
        else:
            self.default_user = current_config["default_user"]

        # Write to the config file
        with open(self.file_path, "w") as config_file:
            json.dump(
                {
                    "domain": self.domain,
                    "users": self.users,
                    "default_user": self.default_user,
                },
                config_file,
                indent=4,
            )

        # Create user tokens file
        self.write_token(username, None, None)

        # Read-write for OS user only
        os.chmod(
            os.path.join(self.directory, self.users[username]["token"]),
            stat.S_IRUSR | stat.S_IWUSR,
        )

    def set_default_user(self, username: str) -> None:
        """Set the default user in the config.

        Parameters
        ----------
        username : str
            Name of the user being set as default.
        """

        # Username is case-insensitive
        username = username.lower()

        if username not in self.users:
            raise KeyError(
                f"User '{username}' is not in the config. Add them using the add-user command."
            )

        self.default_user = username

        with open(self.file_path, "w") as config_file:
            json.dump(
                {
                    "domain": self.domain,
                    "users": self.users,
                    "default_user": self.default_user,
                },
                config_file,
                indent=4,
            )

    def get_default_user(self) -> str:
        """
        Get the default user in the config.
        """

        return self.default_user

    def list_users(self) -> List[str]:
        """
        Get a list of the users in the config.
        """

        return [username for username in self.users]
