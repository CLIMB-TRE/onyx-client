import os
import stat  # TODO: Create tokens file with correct file permissions
import json
from typing import Any, List, Dict, Tuple, Optional, Union

# TODO: Appropriate error messages for stuff such as domain not existing (i.e. when there is no config file)


class OnyxConfig:
    __slots__ = "config_path", "domain", "username", "password", "token"
    CONFIG_FILE_PATH = "~/.onyx"

    def __init__(
        self,
        config_path: Optional[str] = None,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        self.domain = domain
        self.username = username
        self.password = password
        self.token = token

        if config_path:
            self.config_path = config_path
        else:
            self.config_path = OnyxConfig.CONFIG_FILE_PATH

        self.config_path = self.config_path.replace("~", os.path.expanduser("~"))

        if os.path.isfile(self.config_path):
            with open(self.config_path) as config_file:
                config = json.load(config_file)
                if not self.domain:
                    self.domain = config["domain"]

                if not self.token:
                    self.token = config["token"]
        else:
            pass  # TODO: Check for domain, if not raise error cause this is needed

    def write_token(self, token: Union[str, None]) -> None:
        """Update the tokens file for `username`.

        Parameters
        ----------
        token : str, optional
            The token being written to their tokens file.
        """

        with open(self.config_path, "w") as config_file:
            json.dump(
                {
                    "domain": self.domain,
                    "token": token,
                },
                config_file,
                indent=4,
            )
