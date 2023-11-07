from requests import Response


class OnyxError(Exception):
    """
    Generic base class for all Onyx exceptions.
    """

    pass


class OnyxConfigError(OnyxError):
    """
    OnyxConfig validation error.
    """

    pass


class OnyxClientError(OnyxError):
    """
    OnyxClient validation error.
    """

    pass


class OnyxFieldError(OnyxError):
    """
    OnyxField validation error.
    """


class OnyxConnectionError(OnyxError):
    """
    Onyx connection error.
    """

    pass


class OnyxHTTPError(OnyxError):
    """
    Onyx request caused a server failure or error (code `4xx` / `5xx`).
    """

    def __init__(self, message: str, response: Response):
        self.response = response
        super().__init__(message)


class OnyxRequestError(OnyxHTTPError):
    """
    Onyx request caused a server failure (code `4xx`).
    """

    pass


class OnyxServerError(OnyxHTTPError):
    """
    Onyx request caused a server error (code `5xx`).
    """

    pass
