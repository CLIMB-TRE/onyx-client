import os
import csv
import inspect
import requests
from requests import HTTPError, RequestException
from typing import Any, Generator, List, Dict, TextIO, Optional, Union
from .config import OnyxConfig
from .field import OnyxField
from .exceptions import (
    OnyxClientError,
    OnyxConnectionError,
    OnyxRequestError,
    OnyxServerError,
)


class OnyxClientBase:
    __slots__ = "config", "_request_handler", "_session"
    ENDPOINTS = {
        "register": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/register/",
            ),
            domain=domain,
        ),
        "login": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/login/",
            ),
            domain=domain,
        ),
        "logout": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/logout/",
            ),
            domain=domain,
        ),
        "logoutall": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/logoutall/",
            ),
            domain=domain,
        ),
        "profile": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/profile/",
            ),
            domain=domain,
        ),
        "waiting": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/waiting/",
            ),
            domain=domain,
        ),
        "approve": lambda domain, username: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/approve",
                str(username),
                "",
            ),
            domain=domain,
            username=username,
        ),
        "siteusers": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/site/",
            ),
            domain=domain,
        ),
        "allusers": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "accounts/all/",
            ),
            domain=domain,
        ),
        "projects": lambda domain: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects/",
            ),
            domain=domain,
        ),
        "fields": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "fields/",
            ),
            domain=domain,
            project=project,
        ),
        "choices": lambda domain, project, field: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "choices",
                str(field),
                "",
            ),
            domain=domain,
            project=project,
            field=field,
        ),
        "create": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "",
            ),
            domain=domain,
            project=project,
        ),
        "filter": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "",
            ),
            domain=domain,
            project=project,
        ),
        "get": lambda domain, project, cid: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                str(cid),
                "",
            ),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "update": lambda domain, project, cid: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                str(cid),
                "",
            ),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "delete": lambda domain, project, cid: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                str(cid),
                "",
            ),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "query": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "query/",
            ),
            domain=domain,
            project=project,
        ),
        "testcreate": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "test/",
            ),
            domain=domain,
            project=project,
        ),
        "testupdate": lambda domain, project, cid: OnyxClient._handle_endpoint(
            lambda: os.path.join(
                str(domain),
                "projects",
                str(project),
                "test",
                str(cid),
                "",
            ),
            domain=domain,
            project=project,
            cid=cid,
        ),
    }

    def __init__(self, config: OnyxConfig):
        self.config = config
        self._session = None
        self._request_handler = requests.request

    def __enter__(self):
        self._session = requests.Session()
        self._request_handler = self._session.request
        return self

    def __exit__(self, type, value, traceback):
        if self._session:
            self._session.close()
        self._request_handler = requests.request

    @classmethod
    def _handle_endpoint(cls, endpoint, **kwargs):
        for name, val in kwargs.items():
            if val is None or not str(val).strip():
                raise OnyxClientError(f"Argument '{name}' was not provided.")

            val = str(val).strip()

            if name != "domain":
                for char in "/?":
                    if char in val:
                        raise OnyxClientError(
                            f"Argument '{name}' contains invalid character: '{char}'."
                        )

                # Crude but effective
                # Prevents calling other endpoints from the get() function with a cid equal to the endpoint name
                # Its not the end of the world if that did happen, but to the user it would be quite confusing
                if name == "cid":
                    for clash in ["test", "query", "fields", "lookups", "choices"]:
                        if val == clash:
                            raise OnyxClientError(
                                f"Argument '{name}' cannot have value '{val}'. This creates a URL that resolves to a different endpoint."
                            )

        return endpoint()

    def _request(self, method: str, retries: int = 3, **kwargs) -> requests.Response:
        if not retries:
            raise Exception(
                "Request retry limit reached. This should not be possible..."
            )

        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.config.token}"}
        )
        method_response = self._request_handler(method, **kwargs)

        # Token has expired or was invalid.
        # If username and password were provided, log in again, obtain a new token, and re-run the method.
        if (
            method_response.status_code == 401
            and self.config.username
            and self.config.password
        ):
            OnyxClientBase.login(self).raise_for_status()
            # A retry mechanism has been incorporated as a failsafe.
            # This is to protect against the case where an onyx endpoint returns a 401 status code,
            # despite the user being able to successfully log in, leading to an infinite loop of
            # re-logging in and re-hitting the endpoint.
            # This scenario should not be possible. But if it happened, it would not be fun at all.
            # So, better safe than sorry...
            return self._request(method, retries=retries - 1, **kwargs)

        return method_response

    @classmethod
    def to_csv(
        cls,
        csv_file: TextIO,
        data: Union[List[Dict[str, Any]], Generator[Dict[str, Any], Any, None]],
        delimiter: Optional[str] = None,
    ):
        # Ensure data is an iterator
        if inspect.isgenerator(data):
            data_iterator = data
        else:
            data_iterator = iter(data)

        row = next(data_iterator, None)
        if row:
            fields = row.keys()

            # Create CSV writer
            if delimiter is None:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fields,
                )
            else:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fields,
                    delimiter=delimiter,
                )

            # Write data
            writer.writeheader()
            writer.writerow(row)
            for row in data_iterator:
                writer.writerow(row)

    def _csv_upload(
        self,
        method: str,
        endpoint: str,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
        cid_required: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        # Get appropriate endpoint for test/prod
        if test:
            endpoint = "test" + endpoint

        # Create CSV reader
        if delimiter is None:
            reader = csv.DictReader(
                csv_file,
                skipinitialspace=True,
            )
        else:
            reader = csv.DictReader(
                csv_file,
                delimiter=delimiter,
                skipinitialspace=True,
            )

        # Read the first two records (if they exist) and store in 'records' list
        # This is done to protect against two scenarios:
        # - There are no records in the file (never allowed)
        # - There is more than one record, but multiline = False (not allowed)
        records = []

        record_1 = next(reader, None)
        if record_1:
            records.append(record_1)
        else:
            raise OnyxClientError("File must contain at least one record.")

        record_2 = next(reader, None)
        if record_2:
            if not multiline:
                raise OnyxClientError(
                    "File contains multiple records but this is not allowed. To upload multiple records, set 'multiline' = True."
                )
            records.append(record_2)

        # Iterate over the read and unread records and upload sequentially
        for iterator in (records, reader):
            for record in iterator:
                if fields:
                    record = record | fields

                if cid_required:
                    # Grab the cid, if required for the URL
                    cid = record.pop("cid", None)
                    if not cid:
                        raise OnyxClientError("Record requires a 'cid' for upload.")
                    url = OnyxClient.ENDPOINTS[endpoint](
                        self.config.domain, project, cid
                    )
                else:
                    url = OnyxClient.ENDPOINTS[endpoint](self.config.domain, project)

                response = self._request(
                    method=method,
                    url=url,
                    json=record,
                )
                yield response

    def _csv_handle_multiline(
        self,
        responses: Generator[requests.Response, Any, None],
        multiline: bool,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if multiline:
            results = []
            for response in responses:
                response.raise_for_status()
                results.append(response.json()["data"])
            return results
        else:
            response = next(responses, None)
            if response is None:
                raise OnyxClientError("Iterator must contain at least one record.")

            response.raise_for_status()
            return response.json()["data"]

    def projects(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["projects"](self.config.domain),
        )
        return response

    def fields(
        self,
        project: str,
        scope: Union[List[str], str, None] = None,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["fields"](self.config.domain, project),
            params={"scope": scope},
        )
        return response

    def choices(self, project: str, field: str) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["choices"](self.config.domain, project, field),
        )
        return response

    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> requests.Response:
        if test:
            endpoint = "testcreate"
        else:
            endpoint = "create"

        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS[endpoint](self.config.domain, project),
            json=fields,
        )
        return response

    def get(
        self,
        project: str,
        cid: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["get"](self.config.domain, project, cid),
            params={"include": include, "exclude": exclude, "scope": scope},
        )
        return response

    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
        summarise: Optional[str] = None,
    ) -> Generator[requests.Response, Any, None]:
        if fields is None:
            fields = {}

        fields = fields | {
            "include": include,
            "exclude": exclude,
            "scope": scope,
            "summarise": summarise,
        }
        _next = OnyxClient.ENDPOINTS["filter"](self.config.domain, project)

        while _next is not None:
            response = self._request(
                method="get",
                url=_next,
                params=fields,
            )
            yield response

            fields = None
            if response.ok:
                _next = response.json().get("next")
            else:
                _next = None

    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
        summarise: Optional[str] = None,
    ) -> Generator[requests.Response, Any, None]:
        if query:
            if not isinstance(query, OnyxField):
                raise OnyxClientError(
                    f"Query must be an instance of {OnyxField}. Received: {type(query)}"
                )
            else:
                query_json = query.query
        else:
            query_json = None

        fields = {
            "include": include,
            "exclude": exclude,
            "scope": scope,
            "summarise": summarise,
        }
        _next = OnyxClient.ENDPOINTS["query"](self.config.domain, project)

        while _next is not None:
            response = self._request(
                method="post",
                url=_next,
                json=query_json,
                params=fields,
            )
            yield response

            fields = None
            if response.ok:
                _next = response.json().get("next")
            else:
                _next = None

    def update(
        self,
        project: str,
        cid: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> requests.Response:
        if test:
            endpoint = "testupdate"
        else:
            endpoint = "update"

        response = self._request(
            method="patch",
            url=OnyxClient.ENDPOINTS[endpoint](self.config.domain, project, cid),
            json=fields,
        )
        return response

    def delete(
        self,
        project: str,
        cid: str,
    ) -> requests.Response:
        response = self._request(
            method="delete",
            url=OnyxClient.ENDPOINTS["delete"](self.config.domain, project, cid),
        )
        return response

    def csv_create(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="post",
            endpoint="create",
            project=project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )

    def csv_update(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="patch",
            endpoint="update",
            project=project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
            cid_required=True,
        )

    def csv_delete(
        self,
        project: str,
        csv_file: TextIO,
        delimiter: Optional[str] = None,
        multiline: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="delete",
            endpoint="delete",
            project=project,
            csv_file=csv_file,
            delimiter=delimiter,
            multiline=multiline,
            cid_required=True,
        )

    @classmethod
    def register(
        cls,
        domain: str,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> requests.Response:
        response = requests.post(
            OnyxClient.ENDPOINTS["register"](domain),
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "site": site,
            },
        )
        return response

    def login(self) -> requests.Response:
        if self.config.username and self.config.password:
            credentials = (self.config.username, self.config.password)
        else:
            credentials = None

        response = self._request_handler(
            "post",
            auth=credentials,
            url=OnyxClient.ENDPOINTS["login"](self.config.domain),
        )
        if response.ok:
            self.config.token = response.json()["data"]["token"]

        return response

    def logout(self) -> requests.Response:
        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS["logout"](self.config.domain),
        )
        if response.ok:
            self.config.token = None

        return response

    def logoutall(self) -> requests.Response:
        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS["logoutall"](self.config.domain),
        )
        if response.ok:
            self.config.token = None

        return response

    def profile(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["profile"](self.config.domain),
        )
        return response

    def approve(self, username: str) -> requests.Response:
        response = self._request(
            method="patch",
            url=OnyxClient.ENDPOINTS["approve"](self.config.domain, username),
        )
        return response

    def waiting(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["waiting"](self.config.domain),
        )
        return response

    def site_users(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["siteusers"](self.config.domain),
        )
        return response

    def all_users(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["allusers"](self.config.domain),
        )
        return response


def onyx_errors(method):
    """
    Decorator that coerces `requests` library errors into appropriate `OnyxError` subclasses.
    """
    if inspect.isgeneratorfunction(method):

        def wrapped_generator_method(self, *args, **kwargs):
            try:
                yield from method(self, *args, **kwargs)

            except HTTPError as e:
                if e.response is None:
                    # TODO: Seems this does not need handling?
                    raise e  #  type: ignore
                elif e.response.status_code < 500:
                    raise OnyxRequestError(
                        message=str(e),
                        response=e.response,
                    ) from e
                else:
                    raise OnyxServerError(
                        message=str(e),
                        response=e.response,
                    ) from e
            except RequestException as e:
                raise OnyxConnectionError(str(e)) from e

        return wrapped_generator_method
    else:

        def wrapped_method(self, *args, **kwargs):
            try:
                return method(self, *args, **kwargs)

            except HTTPError as e:
                if e.response is None:
                    # TODO: Seems this does not need handling?
                    raise e  #  type: ignore
                elif e.response.status_code < 500:
                    raise OnyxRequestError(
                        message=str(e),
                        response=e.response,
                    ) from e
                else:
                    raise OnyxServerError(
                        message=str(e),
                        response=e.response,
                    ) from e
            except RequestException as e:
                raise OnyxConnectionError(str(e)) from e

        return wrapped_method


class OnyxClient(OnyxClientBase):
    """
    Class for querying and manipulating data within Onyx.
    """

    def __init__(self, config: OnyxConfig) -> None:
        """
        Initialise a client.

        Args:
            config: Object that stores information for connecting and authenticating with Onyx.

        Examples:
            The recommended way to initialise a client (as a context manager):
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                pass # Do something with the client here
            ```

            Alternatively, the client can be initialised as follows:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            client = OnyxClient(config)
            # Do something with the client here
            ```

        Tips:
            - When making multiple requests, using the client as a context manager can improve performance.
            - This is due to the fact that the client will re-use the same session for all requests, rather than creating a new session for each request.
            - For more information, see: https://requests.readthedocs.io/en/master/user/advanced/#session-objects
        """
        super().__init__(config)

    @onyx_errors
    def projects(self) -> List[Dict[str, str]]:
        """
        View available projects.

        Returns:
            List of projects.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                projects = client.projects()
            ```
            >>> projects
            [
                {
                    "project": "project",
                    "action": "add",
                    "scope": "base",
                },
                {
                    "project": "project",
                    "action": "view",
                    "scope": "base",
                },
            ]
        """

        response = super().projects()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def fields(
        self,
        project: str,
        scope: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        View fields for a project.

        Args:
            project: Name of the project.
            scope: Additional named group(s) of fields to include in the output.

        Returns:
            Dict of fields.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                fields = client.fields("project")
            ```
            >>> fields
            {
                "version": "0.1.0",
                "fields": {
                    "cid": {
                        "description": "Unique identifier for a project record.",
                        "type": "text",
                        "required": True,
                    },
                    "published_date": {
                        "description": "Date the record was published.",
                        "type": "date (YYYY-MM-DD)",
                        "required": True,
                    },
                    "country": {
                        "description": "Country of origin.",
                        "type": "choice",
                        "required": False,
                        "values": [
                            "ENG",
                            "WALES",
                            "SCOT",
                            "NI",
                        ],
                    },
                },
            }
        """

        response = super().fields(project, scope=scope)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.

        Args:
            project: Name of the project.
            field: Choice field on the project.

        Returns:
            List of choices for the field.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                choices = client.choices("project", "country")
            ```
            >>> choices
            ["ENG", "WALES", "SCOT", "NI"]
        """

        response = super().choices(project, field)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def get(
        self,
        project: str,
        cid: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Get a record from a project.

        Args:
            project: Name of the project.
            cid: Unique identifier for the record in the project.
            fields: Series of conditions on fields, used to filter the data.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            scope: Additional named group(s) of fields to include in the output.

        Returns:
            Dict containing the record.

        Examples:
            Get a record by CID:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record = client.get("project", "C-1234567890")
            ```
            >>> record
            {
                "cid": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }

            Get a record by fields that uniquely identify it:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record = client.get(
                    "project",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            >>> record
            {
                "cid": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }

            The `include`, `exclude`, and `scope` arguments can be used to control the fields returned:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                record_v1 = client.get(
                    "project",
                    cid="C-1234567890",
                    include=["cid", "published_date"],
                )
                record_v2 = client.get(
                    "project",
                    cid="C-1234567890",
                    exclude=["field2"],
                )
                record_v3 = client.get(
                    "project",
                    cid="C-1234567890",
                    scope="extra_fields",
                )
            ```
            >>> record_v1
            {
                "cid": "C-1234567890",
                "published_date": "2023-01-01",
            }
            >>> record_v2
            {
                "cid": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
            }
            >>> record_v3
            {
                "cid": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
                "extra_field1": "extra_value1",
                "extra_field2": "extra_value2",
            }

        Tips:
            - Including/excluding fields to reduce the size of the returned data can improve performance.
        """

        if cid and fields:
            raise OnyxClientError("Cannot provide both 'cid' and 'fields'.")

        if not (cid or fields):
            raise OnyxClientError("Must provide either 'cid' or 'fields'.")

        if cid:
            response = super().get(
                project,
                cid,
                include=include,
                exclude=exclude,
                scope=scope,
            )
            response.raise_for_status()
            return response.json()["data"]
        else:
            responses = super().filter(
                project,
                fields=fields,
                include=include,
                exclude=exclude,
                scope=scope,
            )
            response = next(responses, None)
            if response is None:
                raise OnyxClientError(
                    f"Expected one record to be returned but received no response."
                )

            response.raise_for_status()
            count = len(response.json()["data"])
            if count != 1:
                raise OnyxClientError(
                    f"Expected one record to be returned but received: {count}"
                )

            return response.json()["data"][0]

    @onyx_errors
    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
        summarise: Optional[str] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter records from a project.

        Args:
            project: Name of the project.
            fields: Series of conditions on fields, used to filter the data.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            scope: Additional named group(s) of fields to include in the output.
            summarise: For a given field in the filtered data, return the frequency of each of its values.

        Returns:
            Generator of records. If a summarise field is provided, each record will be a dict containing a value of the field and its frequency.

        Notes:
            - The fields argument must be a dict of field conditions. Each of these specifies a requirement that the returned data must match.
            - These conditions can be a simple match on a value (e.g. `"published_date" : "2023-01-01"`).
            - Or, they can use a 'lookup' for more complex matching conditions (e.g. `"published_date__year" : "2023"`).
            - Multi-value lookups must be provided as a comma-separated string of values (e.g. `"published_date__range" : "2023-01-01, 2023-01-02"`).

        Examples:
            Retrieve all records that match a set of field requirements:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records = list(
                    client.filter(
                        project="project",
                        fields={
                            "field1": "abcd",
                            "published_date__range" : "2023-01-01, 2023-01-02",
                        },
                    )
                )
            ```
            >>> records
            [
                {
                    "cid": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "cid": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]

            The `summarise` argument can be used to return the frequency of each value for a given field:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records = list(
                    client.filter(
                        project="project",
                        fields={
                            "field1": "abcd",
                            "published_date__range" : "2023-01-01, 2023-01-02",
                        },
                        summarise="published_date",
                    )
                )
            ```
            >>> records
            [
                {
                    "published_date": "2023-01-01",
                    "count": 1,
                },
                {
                    "published_date": "2023-01-02",
                    "count": 1,
                },
            ]
        """

        responses = super().filter(
            project,
            fields=fields,
            include=include,
            exclude=exclude,
            scope=scope,
            summarise=summarise,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_errors
    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
        summarise: Optional[str] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Query records from a project.

        Args:
            project: Name of the project.
            query: OnyxField object representing the query being made.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            scope: Additional named group(s) of fields to include in the output.
            summarise: For a given field in the filtered data, return the frequency of each of its values.

        Returns:
            Generator of records. If a summarise field is provided, each record will be a dict containing a value of the field and its frequency.

        Notes:
            - The query argument must be an instance of OnyxField.
            - OnyxField instances can be combined into complex expressions using Python's bitwise operators: `&` (AND), `|` (OR), `^` (XOR), and `~` (NOT).
            - Multi-value lookups (e.g. 'in', 'range') support passing a Python list as the value. These are coerced into comma-separated strings internally.

        Examples:
            Retrieve all records that match the query provided by an OnyxField object:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient, OnyxField

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records = list(
                    client.query(
                        project="project",
                        query=(
                            OnyxField(field1="abcd")
                            & OnyxField(published_date__range=["2023-01-01", "2023-01-02"])
                        ),
                    )
                )
            ```
            >>> records
            [
                {
                    "cid": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "cid": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]
        """

        responses = super().query(
            project,
            query=query,
            include=include,
            exclude=exclude,
            scope=scope,
            summarise=summarise,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @classmethod
    @onyx_errors
    def to_csv(
        cls,
        csv_file: TextIO,
        data: Union[List[Dict[str, Any]], Generator[Dict[str, Any], Any, None]],
        delimiter: Optional[str] = None,
    ):
        """
        Write a set of records to a CSV file.

        Args:
            csv_file: File object for the CSV file being written to.
            data: The data being written to the CSV file. Must be either a list / generator of dict records.
            delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                client.to_csv(
                    csv_file=csv_file,
                    data=client.filter(
                        "project",
                        fields={
                            "field1": "value1",
                            "field2": "value2",
                        },
                )
            ```
        """
        super().to_csv(
            csv_file=csv_file,
            data=data,
            delimiter=delimiter,
        )

    @onyx_errors
    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a record in a project.

        Args:
            project: Name of the project.
            fields: Object representing the record to be created.
            test: If True, runs the command as a test. Default: False

        Returns:
            Dict containing the CID of the created record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.create(
                    "project",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            >>> result
            {"cid": "C-1234567890"}
        """

        response = super().create(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def update(
        self,
        project: str,
        cid: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Update a record in a project.

        Args:
            project: Name of the project.
            cid: Unique identifier for the record in the project.
            fields: Object representing the record to be updated.
            test: If True, runs the command as a test. Default: False

        Returns:
            Dict containing the CID of the updated record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.update(
                    project="project",
                    cid="C-1234567890",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            >>> result
            {"cid": "C-1234567890"}
        """

        response = super().update(project, cid, fields=fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def delete(
        self,
        project: str,
        cid: str,
    ) -> Dict[str, Any]:
        """
        Delete a record in a project.

        Args:
            project: Name of the project.
            cid: Unique identifier for the record in the project.

        Returns:
            Dict containing the CID of the deleted record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                result = client.delete(
                    project="project",
                    cid="C-1234567890",
                )
            ```
            >>> result
            {"cid": "C-1234567890"}
        """

        response = super().delete(project, cid)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def csv_create(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to create record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
            delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
            multiline: If True, allows processing of CSV files with more than one record. Default: False
            test: If True, runs the command as a test. Default: False

        Returns:
            Dict containing the CID of the created record. If multiline = True, returns a list of dicts containing the CID of each created record.

        Examples:
            Create a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_create(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            >>> result
            {"cid": "C-1234567890"}

            Create multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_create(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            >>> results
            [
                {"cid": "C-1234567890"},
                {"cid": "C-1234567891"},
                {"cid": "C-1234567892"},
            ]
        """

        responses = super().csv_create(
            project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )
        return self._csv_handle_multiline(responses, multiline)

    @onyx_errors
    def csv_update(
        self,
        project: str,
        csv_file: TextIO,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multiline: bool = False,
        test: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to update record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
            delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
            multiline: If True, allows processing of CSV files with more than one record. Default: False
            test: If True, runs the command as a test. Default: False

        Returns:
            Dict containing the CID of the updated record. If multiline = True, returns a list of dicts containing the CID of each updated record.

        Examples:
            Update a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_update(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            >>> result
            {"cid": "C-1234567890"}

            Update multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_update(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            >>> results
            [
                {"cid": "C-1234567890"},
                {"cid": "C-1234567891"},
                {"cid": "C-1234567892"},
            ]
        """

        responses = super().csv_update(
            project,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multiline=multiline,
            test=test,
        )
        return self._csv_handle_multiline(responses, multiline)

    @onyx_errors
    def csv_delete(
        self,
        project: str,
        csv_file: TextIO,
        delimiter: Optional[str] = None,
        multiline: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Use a CSV file to delete record(s) in a project.

        Args:
            project: Name of the project.
            csv_file: File object for the CSV file being used for record upload.
            delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
            multiline: If True, allows processing of CSV files with more than one record. Default: False

        Returns:
            Dict containing the CID of the deleted record. If multiline = True, returns a list of dicts containing the CID of each deleted record.

        Examples:
            Delete a single record:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                result = client.csv_delete(
                    project="project",
                    csv_file=csv_file,
                )
            ```
            >>> result
            {"cid": "C-1234567890"}

            Delete multiple records:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client, open("/path/to/file.csv") as csv_file:
                results = client.csv_delete(
                    project="project",
                    csv_file=csv_file,
                    multiline=True,
                )
            ```
            >>> results
            [
                {"cid": "C-1234567890"},
                {"cid": "C-1234567891"},
                {"cid": "C-1234567892"},
            ]
        """

        responses = super().csv_delete(
            project,
            csv_file=csv_file,
            delimiter=delimiter,
            multiline=multiline,
        )
        return self._csv_handle_multiline(responses, multiline)

    @classmethod
    @onyx_errors
    def register(
        cls,
        domain: str,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            domain: Name of the domain.
            first_name: First name of the user.
            last_name: Last name of the user.
            email: Email address of the user.
            site: Name of the site.
            password: Password for the user.

        Returns:
            Dict containing the user's information.

        Examples:
            ```python
            import os
            from onyx import OnyxClient, OnyxEnv

            registration = OnyxClient.register(
                domain=os.environ[OnyxEnv.DOMAIN],
                first_name="Bill",
                last_name="Will",
                email="bill@email.com",
                site="site",
                password="pass123",
            )
            ```
            >>> registration
            {
                "username": "onyx-willb",
                "site": "site",
                "email": "bill@email.com",
                "first_name": "Bill",
                "last_name": "Will",
            }
        """
        response = super().register(
            domain,
            first_name,
            last_name,
            email,
            site,
            password,
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def login(self) -> Dict[str, Any]:
        """
        Log in the user.

        Returns:
            Dict containing the user's authentication token and it's expiry.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                username=os.environ[OnyxEnv.USERNAME],
                password=os.environ[OnyxEnv.PASSWORD],
            )

            with OnyxClient(config) as client:
                token = client.login()
            ```
            >>> token
            {
                "expiry": "2024-01-01T00:00:00.000000Z",
                "token": "abc123",
            }
        """

        response = super().login()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def logout(self) -> None:
        """
        Log out the user.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                client.logout()
            ```
        """

        response = super().logout()
        response.raise_for_status()

    @onyx_errors
    def logoutall(self) -> None:
        """
        Log out the user in all clients.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                client.logoutall()
            ```
        """

        response = super().logoutall()
        response.raise_for_status()

    @onyx_errors
    def profile(self) -> Dict[str, str]:
        """
        View the user's information.

        Returns:
            Dict containing the user's information.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                profile = client.profile()
            ```
            >>> profile
            {
                "username": "user",
                "site": "site",
                "email": "user@email.com",
            }
        """

        response = super().profile()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def approve(self, username: str) -> Dict[str, Any]:
        """
        Approve another user.

        Args:
            username: Username of the user to be approved.

        Returns:
            Dict confirming user approval success.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                approval = client.approve("waiting_user")
            ```
            >>> approval
            {
                "username": "waiting_user",
                "is_approved": True,
            }
        """

        response = super().approve(username)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def waiting(self) -> List[Dict[str, Any]]:
        """
        Get users waiting for approval.

        Returns:
            List of users waiting for approval.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                users = client.waiting()
            ```
            >>> users
            [
                {
                    "username": "waiting_user",
                    "site": "site",
                    "email": "waiting_user@email.com",
                    "date_joined": "2023-01-01T00:00:00.000000Z",
                }
            ]
        """

        response = super().waiting()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def site_users(self) -> List[Dict[str, Any]]:
        """
        Get users within the site of the requesting user.

        Returns:
            List of users within the site of the requesting user.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config):
                users = client.site_users()
            ```
            >>> users
            [
                {
                    "username": "user",
                    "site": "site",
                    "email": "user@email.com",
                }
            ]
        """

        response = super().site_users()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.

        Returns:
            List of all users.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                users = client.all_users()
            ```
            >>> users
            [
                {
                    "username": "user",
                    "site": "site",
                    "email": "user@email.com",
                },
                {
                    "username": "another_user",
                    "site": "another_site",
                    "email": "another_user@email.com",
                },
            ]
        """

        response = super().all_users()
        response.raise_for_status()
        return response.json()["data"]
