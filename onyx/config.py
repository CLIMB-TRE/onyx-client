import os
import json
from typing import Optional, Union

# TODO: Appropriate error messages for stuff such as domain not existing (i.e. when there is no config file)
# TODO: Ok as first step. refactor to do what Andy said and pull out file management


class OnyxConfig:
    __slots__ = "config_path", "domain", "username", "password", "token"
    CONFIG_FILE_PATH = "~/.onyx"

    def __init__(
        self,
        config_path: Optional[str] = None,
        domain: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.domain = domain
        self.token = token

        if config_path:
            self.config_path = config_path
        else:
            self.config_path = OnyxConfig.CONFIG_FILE_PATH

        self.config_path = self.config_path.replace("~", os.path.expanduser("~"))

        if os.path.isfile(self.config_path):
            with open(self.config_path) as config_file:
                config = json.load(config_file)

                if not self.domain and config.get("domain"):
                    self.domain = str(config["domain"])

                if not self.token and config.get("token"):
                    self.token = str(config["token"])
        else:
            if not self.domain:
                raise Exception("Could not find domain name.")

        self.username = username
        self.password = password

    def write_token(self, token: Union[str, None]) -> None:
        """Update the tokens file for `username`.

        Parameters
        ----------
        token : str, optional
            The token being written to their tokens file.
        """

        if os.path.isfile(self.config_path):
            with open(self.config_path, "w") as config_file:
                config = {
                    "domain": self.domain,
                    "token": token,
                }
                json.dump(
                    config,
                    config_file,
                    indent=4,
                )
