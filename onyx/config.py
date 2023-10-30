from typing import Optional


class OnyxEnv:
    DOMAIN = "ONYX_DOMAIN"
    TOKEN = "ONYX_TOKEN"
    USERNAME = "ONYX_USERNAME"
    PASSWORD = "ONYX_PASSWORD"


class OnyxConfig:
    """
    Class for storing information required to connect/authenticate with Onyx.
    """

    __slots__ = "domain", "token", "username", "password"

    def __init__(
        self,
        domain: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialise a config.

        This object stores information required to connect and authenticate with Onyx.

        A domain must be provided, alongside an API token and/or the username + password.

        Parameters
        ----------
        domain : str
            Domain for connecting to Onyx.
        token : str, optional
            Token for authenticating with Onyx.
        username : str, optional
            Username for authenticating with Onyx.
        password : str, optional
            Password for authenticating with Onyx.
        """

        if not domain:
            raise Exception("A domain must be provided for connecting to Onyx.")

        if (not token) and not (username and password):
            raise Exception(
                "Either a token or login credentials (username and password) must be provided for authenticating to Onyx."
            )

        self.domain = domain
        self.token = token
        self.username = username
        self.password = password
