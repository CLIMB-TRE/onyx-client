import os
import enum
from typing import Optional


class OnyxEnv(enum.Enum):
    DOMAIN = "ONYX_DOMAIN"
    USERNAME = "ONYX_USERNAME"
    PASSWORD = "ONYX_PASSWORD"
    TOKEN = "ONYX_TOKEN"
    DISPLAY = "ONYX_DISPLAY"


class OnyxConfig:
    """
    Class for storing information required to connect/authenticate with Onyx.
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        credentials: Optional[tuple[str, str]] = None,
        token: Optional[str] = None,
    ) -> None:
        """
        Initialise the config.
        """

        if not domain:
            domain = os.environ[OnyxEnv.DOMAIN.value]

        if not credentials:
            username = os.getenv(OnyxEnv.USERNAME.value)
            password = os.getenv(OnyxEnv.PASSWORD.value)

            if username and password:
                credentials = (username, password)

        if not token:
            token = os.getenv(OnyxEnv.TOKEN.value)

        self.domain = domain
        self.credentials = credentials
        self.token = token

        if not self.domain:
            raise Exception("Must provide a domain to connect to Onyx.")

        if not (self.credentials or self.token):
            raise Exception(
                "Must provide either credentials (username, password) or a token to authenticate with Onyx."
            )
