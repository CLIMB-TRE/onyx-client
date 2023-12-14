from typing import Optional
from .exceptions import OnyxConfigError


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

    @classmethod
    def _validate_domain(
        cls,
        domain: str,
    ):
        if not domain:
            raise OnyxConfigError("A 'domain' must be provided for connecting to Onyx.")

    @classmethod
    def _validate_auth(
        cls,
        token: Optional[str],
        username: Optional[str],
        password: Optional[str],
    ):
        if (not token) and not (username and password):
            raise OnyxConfigError(
                "Either a 'token' or login credentials ('username' and 'password') must be provided for authenticating to Onyx."
            )

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

        Args:
            domain: Domain for connecting to Onyx.
            token: Token for authenticating with Onyx.
            username: Username for authenticating with Onyx.
            password: Password for authenticating with Onyx.

        Examples:
            Create a config using environment variables for the domain and an API token:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )
            ```

            Or using environment variables for the domain and login credentials:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                username=os.environ[OnyxEnv.USERNAME],
                password=os.environ[OnyxEnv.PASSWORD],
            )
            ```
        """

        self._validate_domain(domain)
        self._validate_auth(token, username, password)
        self.domain = domain
        self.token = token
        self.username = username
        self.password = password
