from requests import Response


class OnyxError(Exception):
    """
    Generic class for all Onyx exceptions.
    """

    pass


class OnyxConfigError(OnyxError):
    """
    Config validation error.

    This error occurs due to validation failures when initialising an `OnyxConfig` object.

    Examples:
        - A `domain` was not provided.
        - Neither a `token` or valid login credentials (`username` and `password`) were provided.
    """

    pass


class OnyxClientError(OnyxError):
    """
    Client validation error.

    This error occurs due to validation failures within an `OnyxClient` object, and **not** due to error codes returned by the Onyx API.

    Examples:
        - Incorrect types were provided to `OnyxClient` methods.
        - Empty strings were provided for required arguments such as the `climb_id`, creating an invalid URL.
        - Empty CSV/TSV files are provided on `OnyxClient.csv_create`, `OnyxClient.csv_update`, or `OnyxClient.csv_delete`.
        - CSV/TSV files with more than one record are provided to `OnyxClient.csv_create`, `OnyxClient.csv_update`, or `OnyxClient.csv_delete` when `multiline = False`.

    Notes:
        - One counter-intuitive cause of this error is when an `OnyxClient.get` request using `fields` returns more than one result.
        - This is not an `OnyxRequestError` because for this particular combination of parameters, an underlying call to the `OnyxClient.filter` method is made.
        - The request to the Onyx API may be successful, but return more than one record. However, the `OnyxClient.get` method expects a single record, resulting in the error being raised.
        - This behaviour may change in the future.
    """

    pass


class OnyxFieldError(OnyxError):
    """
    Field validation error.

    This error occurs due to validation failures within the `OnyxField` class.

    Examples:
        - The user did not provide exactly one key-value pair on initialisation.
        - An attempt was made to combine an `OnyxField` instance with a different type.
        - The structure of the underlying `OnyxField.query` is somehow incorrect.
    """

    pass


class OnyxConnectionError(OnyxError):
    """
    Onyx connection error.

    This error occurs due to a failure to connect to the Onyx API.

    Notes:
        - This error occurs due to any subclass of `requests.RequestException` (excluding `requests.HTTPError`) being raised.
        - For more information, see: https://requests.readthedocs.io/en/latest/api/#requests.RequestException
    """

    pass


class OnyxHTTPError(OnyxError):
    """
    Onyx HTTP error.

    This error occurs due to a request to the Onyx API either failing (code `4xx`) or causing a server error (code `5xx`).

    Notes:
        - This error occurs due to a `requests.HTTPError` being raised.
        - Like the `requests.HTTPError` class, instances of this class have a `response` object containing details of the error.
        - For more information on the `response` object, see: https://requests.readthedocs.io/en/latest/api/#requests.Response

    Examples:
        ```python
        import os
        from onyx import OnyxConfig, OnyxEnv, OnyxClient, OnyxField
        from onyx.exceptions import OnyxHTTPError

        config = OnyxConfig(
            domain=os.environ[OnyxEnv.DOMAIN],
            token=os.environ[OnyxEnv.TOKEN],
        )

        with OnyxClient(config) as client:
            try:
                records = list(
                    client.query(
                        project="project",
                        query=(
                            OnyxField(field1="abcd")
                            & OnyxField(published_date__range=["2023-01-01", "2023-01-02"])
                        ),
                    )
                )
            except OnyxHTTPError as e:
                print(e.response.json())
        ```

    """

    def __init__(self, message: str, response: Response):
        self.response = response
        super().__init__(message)


class OnyxRequestError(OnyxHTTPError):
    """
    Onyx request error.

    This error occurs due to a failed request to the Onyx API (code `4xx`).

    Examples:
        - Invalid field names or field values (`400 Bad Request`).
        - Invalid authentication credentials (`401 Unauthorized`).
        - A request was made for something which the user has insufficient permissions for (`403 Forbidden`).
        - An invalid project / CLIMB ID / anonymised value was provided (`404 Not Found`).
        - An invalid HTTP method was used (`405 Method Not Allowed`).
    """

    pass


class OnyxServerError(OnyxHTTPError):
    """
    Onyx server error.

    This error occurs due to a request to the Onyx API causing a server error (code `5xx`).

    Warning:
        Server errors are unintended and should be reported to an admin if encountered.
    """

    pass
