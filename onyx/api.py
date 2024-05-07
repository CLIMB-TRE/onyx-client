import posixpath
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
        "projects": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects/",
            ),
            domain=domain,
        ),
        "types": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects/types/",
            ),
            domain=domain,
        ),
        "lookups": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects/lookups/",
            ),
            domain=domain,
        ),
        "fields": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "fields/",
            ),
            domain=domain,
            project=project,
        ),
        "choices": lambda domain, project, field: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
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
        "get": lambda domain, project, climb_id: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                str(climb_id),
                "",
            ),
            domain=domain,
            project=project,
            climb_id=climb_id,
        ),
        "filter": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "",
            ),
            domain=domain,
            project=project,
        ),
        "query": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "query/",
            ),
            domain=domain,
            project=project,
        ),
        "history": lambda domain, project, climb_id: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "history",
                str(climb_id),
                "",
            ),
            domain=domain,
            project=project,
            climb_id=climb_id,
        ),
        "identify": lambda domain, project, field: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "identify",
                str(field),
                "",
            ),
            domain=domain,
            project=project,
            field=field,
        ),
        "create": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "",
            ),
            domain=domain,
            project=project,
        ),
        "testcreate": lambda domain, project: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "test/",
            ),
            domain=domain,
            project=project,
        ),
        "update": lambda domain, project, climb_id: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                str(climb_id),
                "",
            ),
            domain=domain,
            project=project,
            climb_id=climb_id,
        ),
        "testupdate": lambda domain, project, climb_id: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                "test",
                str(climb_id),
                "",
            ),
            domain=domain,
            project=project,
            climb_id=climb_id,
        ),
        "delete": lambda domain, project, climb_id: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "projects",
                str(project),
                str(climb_id),
                "",
            ),
            domain=domain,
            project=project,
            climb_id=climb_id,
        ),
        "register": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/register/",
            ),
            domain=domain,
        ),
        "login": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/login/",
            ),
            domain=domain,
        ),
        "logout": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/logout/",
            ),
            domain=domain,
        ),
        "logoutall": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/logoutall/",
            ),
            domain=domain,
        ),
        "profile": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/profile/",
            ),
            domain=domain,
        ),
        "activity": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/activity/",
            ),
            domain=domain,
        ),
        "waiting": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/waiting/",
            ),
            domain=domain,
        ),
        "approve": lambda domain, username: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/approve",
                str(username),
                "",
            ),
            domain=domain,
            username=username,
        ),
        "siteusers": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/site/",
            ),
            domain=domain,
        ),
        "allusers": lambda domain: OnyxClient._handle_endpoint(
            lambda: posixpath.join(
                str(domain),
                "accounts/all/",
            ),
            domain=domain,
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

                # Crude but effective prevention of unexpectedly calling other endpoints
                # Its not the end of the world if that did happen, but to the user it would be quite confusing
                clashes = {
                    "project": ["types", "lookups"],
                    "climb_id": [
                        "test",
                        "query",
                        "fields",
                        "choices",
                        "history",
                        "identify",
                    ],
                }

                if name in clashes:
                    for clash in clashes[name]:
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
        climb_id_required: bool = False,
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

                if climb_id_required:
                    # Grab the climb_id, if required for the URL
                    climb_id = record.pop("climb_id", None)
                    if not climb_id:
                        raise OnyxClientError(
                            "Record requires a 'climb_id' for upload."
                        )
                    url = OnyxClient.ENDPOINTS[endpoint](
                        self.config.domain, project, climb_id
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

    def types(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["types"](self.config.domain),
        )
        return response

    def lookups(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["lookups"](self.config.domain),
        )
        return response

    def fields(self, project: str) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["fields"](self.config.domain, project),
        )
        return response

    def choices(self, project: str, field: str) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["choices"](self.config.domain, project, field),
        )
        return response

    def get(
        self,
        project: str,
        climb_id: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["get"](self.config.domain, project, climb_id),
            params={"include": include, "exclude": exclude},
        )
        return response

    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        summarise: Union[List[str], str, None] = None,
        **kwargs: Any,
    ) -> Generator[requests.Response, Any, None]:
        if fields is None:
            fields = {}

        for field, value in kwargs.items():
            if type(value) in {list, tuple, set}:
                value = ",".join(map(lambda x: str(x) if x is not None else "", value))
            fields[field] = value

        for field, value in fields.items():
            if type(value) in {list, tuple, set}:
                fields[field] = [v if v is not None else "" for v in value]
            if value is None:
                fields[field] = ""

        fields = fields | {
            "include": include,
            "exclude": exclude,
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
        summarise: Union[List[str], str, None] = None,
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

    def history(
        self,
        project: str,
        climb_id: str,
    ) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["history"](self.config.domain, project, climb_id),
        )
        return response

    def identify(
        self,
        project: str,
        field: str,
        value: str,
        site: Optional[str] = None,
    ) -> requests.Response:
        identify_json = {"value": value}
        if site:
            identify_json = identify_json | {"site": site}

        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS["identify"](self.config.domain, project, field),
            json=identify_json,
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

    def update(
        self,
        project: str,
        climb_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> requests.Response:
        if test:
            endpoint = "testupdate"
        else:
            endpoint = "update"

        response = self._request(
            method="patch",
            url=OnyxClient.ENDPOINTS[endpoint](self.config.domain, project, climb_id),
            json=fields,
        )
        return response

    def delete(
        self,
        project: str,
        climb_id: str,
    ) -> requests.Response:
        response = self._request(
            method="delete",
            url=OnyxClient.ENDPOINTS["delete"](self.config.domain, project, climb_id),
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
            climb_id_required=True,
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
            climb_id_required=True,
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

    def activity(self) -> requests.Response:
        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["activity"](self.config.domain),
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
            config: `OnyxConfig` object that stores information for connecting and authenticating with Onyx.

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
                pass # Do something with the client here
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
            ```python
            >>> projects
            [
                {
                    "project": "project_1",
                    "scope": "admin",
                    "actions": [
                        "get",
                        "list",
                        "filter",
                        "add",
                        "change",
                        "delete",
                    ],
                },
                {
                    "project": "project_2",
                    "scope": "analyst",
                    "actions": [
                        "get",
                        "list",
                        "filter",
                    ],
                },
            ]
            ```
        """

        response = super().projects()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def types(self) -> List[Dict[str, Any]]:
        """
        View available field types.

        Returns:
            List of field types.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                field_types = client.types()
            ```
            ```python
            >>> field_types
            [
                {
                    "type": "text",
                    "description": "A string of characters.",
                    "lookups": [
                        "exact",
                        "ne",
                        "in",
                        "notin",
                        "contains",
                        "startswith",
                        "endswith",
                        "iexact",
                        "icontains",
                        "istartswith",
                        "iendswith",
                        "length",
                        "length__in",
                        "length__range",
                        "isnull",
                    ],
                },
                {
                    "type": "choice",
                    "description": "A restricted set of options.",
                    "lookups": [
                        "exact",
                        "ne",
                        "in",
                        "notin",
                        "isnull",
                    ],
                },
            ]
            ```
        """

        response = super().types()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def lookups(self) -> List[Dict[str, Any]]:
        """
        View available lookups.

        Returns:
            List of lookups.

        Examples:
            ```python
            import os

            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                lookups = client.lookups()
            ```
            ```python
            >>> lookups
            [
                {
                    "lookup": "exact",
                    "description": "The field's value must be equal to the query value.",
                    "types": [
                        "text",
                        "choice",
                        "integer",
                        "decimal",
                        "date",
                        "datetime",
                        "bool",
                    ],
                },
                {
                    "lookup": "ne",
                    "description": "The field's value must not be equal to the query value.",
                    "types": [
                        "text",
                        "choice",
                        "integer",
                        "decimal",
                        "date",
                        "datetime",
                        "bool",
                    ],
                },
            ]
            ```
        """

        response = super().lookups()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def fields(self, project: str) -> Dict[str, Any]:
        """
        View fields for a project.

        Args:
            project: Name of the project.

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
            ```python
            >>> fields
            {
                "version": "0.1.0",
                "fields": {
                    "climb_id": {
                        "description": "Unique identifier for a project record in Onyx.",
                        "type": "text",
                        "required": True,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                        ],
                        "restrictions": [
                            "Max length: 12",
                        ],
                    },
                    "is_published": {
                        "description": "Indicator for whether a project record has been published.",
                        "type": "bool",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                            "add",
                            "change",
                        ],
                        "default": True,
                    },
                    "published_date": {
                        "description": "The date the project record was published in Onyx.",
                        "type": "date (YYYY-MM-DD)",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                        ],
                    },
                    "country": {
                        "description": "Country of origin.",
                        "type": "choice",
                        "required": False,
                        "actions": [
                            "get",
                            "list",
                            "filter",
                            "add",
                            "change",
                        ],
                        "values": [
                            "ENG",
                            "WALES",
                            "SCOT",
                            "NI",
                        ],
                    },
                },
            }
            ```
        """

        response = super().fields(project)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def choices(self, project: str, field: str) -> Dict[str, Dict[str, Any]]:
        """
        View choices for a field.

        Args:
            project: Name of the project.
            field: Choice field on the project.

        Returns:
            Dictionary mapping choices to information about the choice.

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
            ```python
            >>> choices
            {
                "ENG": {
                    "description": "England",
                    "is_active" : True,
                },
                "WALES": {
                    "description": "Wales",
                    "is_active" : True,
                },
                "SCOT": {
                    "description": "Scotland",
                    "is_active" : True,
                },
                "NI": {
                    "description": "Northern Ireland",
                    "is_active" : True,
                },
            }
            ```
        """

        response = super().choices(project, field)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def get(
        self,
        project: str,
        climb_id: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Get a record from a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record in the project.
            fields: Dictionary of field filters used to uniquely identify the record.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.

        Returns:
            Dict containing the record.

        Examples:
            Get a record by CLIMB ID:
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
            ```python
            >>> record
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }
            ```

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
            ```python
            >>> record
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
                "field2": "value2",
            }
            ```

            The `include` and `exclude` arguments can be used to control the fields returned:
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
                    climb_id="C-1234567890",
                    include=["climb_id", "published_date"],
                )
                record_v2 = client.get(
                    "project",
                    climb_id="C-1234567890",
                    exclude=["field2"],
                )
            ```
            ```python
            >>> record_v1
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
            }
            >>> record_v2
            {
                "climb_id": "C-1234567890",
                "published_date": "2023-01-01",
                "field1": "value1",
            }
            ```

        Tips:
            - Including/excluding fields to reduce the size of the returned data can improve performance.
        """

        if climb_id and fields:
            raise OnyxClientError("Cannot provide both 'climb_id' and 'fields'.")

        if not (climb_id or fields):
            raise OnyxClientError("Must provide either 'climb_id' or 'fields'.")

        if climb_id:
            response = super().get(
                project,
                climb_id,
                include=include,
                exclude=exclude,
            )
            response.raise_for_status()
            return response.json()["data"]
        else:
            responses = super().filter(
                project,
                fields=fields,
                include=include,
                exclude=exclude,
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
        summarise: Union[List[str], str, None] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter records from a project.

        Args:
            project: Name of the project.
            fields: Dictionary of field filters.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            summarise: For a given field (or group of fields), return the frequency of each unique value (or unique group of values).
            **kwargs: Additional keyword arguments are interpreted as field filters.

        Returns:
            Generator of records. If a summarise argument is provided, each record will be a dict containing values of the summary fields and a count for the frequency.

        Notes:
            - Field filters specify requirements that the returned data must satisfy. They can be provided as keyword arguments, or as a dictionary to the `fields` argument.
            - These filters can be a simple match on a value (e.g. `"published_date" : "2023-01-01"`), or they can use a 'lookup' for more complex matching conditions (e.g. `"published_date__iso_year" : "2023"`).
            - Multi-value lookups (e.g. `in`, `range`) can also be used. For keyword arguments, multiple values can be provided as a Python list. For the `fields` dictionary, multiple values must be provided as a comma-separated string (see examples below).

        Examples:
            Retrieve all records that match a set of field requirements:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            # Field conditions can either be provided as keyword arguments:
            with OnyxClient(config) as client:
                records = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                    )
                )

            # Or as a dictionary to the 'fields' argument:
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
            ```python
            >>> records
            [
                {
                    "climb_id": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "climb_id": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]
            ```

            The `summarise` argument can be used to return the frequency of each unique value for a given field, or the frequency of each unique set of values for a group of fields:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                records_v1 = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                        summarise="published_date",
                    )
                )

                records_v2 = list(
                    client.filter(
                        project="project",
                        field1="abcd",
                        published_date__range=["2023-01-01", "2023-01-02"],
                        summarise=["published_date", "field2"],
                    )
                )
            ```
            ```python
            >>> records_v1
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
            >>> records_v2
            [
                {
                    "published_date": "2023-01-01",
                    "field2": 123,
                    "count": 1,
                },
                {
                    "published_date": "2023-01-02",
                    "field2": 456,
                    "count": 1,
                },
            ]
            ```

        """

        responses = super().filter(
            project,
            fields=fields,
            include=include,
            exclude=exclude,
            summarise=summarise,
            **kwargs,
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
        summarise: Union[List[str], str, None] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Query records from a project.

        This method supports more complex filtering than the `OnyxClient.filter` method.
        Here, filters can be combined using Python's bitwise operators, representing AND, OR, XOR and NOT operations.

        Args:
            project: Name of the project.
            query: `OnyxField` object representing the query being made.
            include: Fields to include in the output.
            exclude: Fields to exclude from the output.
            summarise: For a given field (or group of fields), return the frequency of each unique value (or unique group of values).

        Returns:
            Generator of records. If a summarise argument is provided, each record will be a dict containing values of the summary fields and a count for the frequency.

        Notes:
            - The `query` argument must be an instance of `OnyxField`.
            - `OnyxField` instances can be combined into complex expressions using Python's bitwise operators: `&` (AND), `|` (OR), `^` (XOR), and `~` (NOT).
            - Multi-value lookups (e.g. `in`, `range`) support passing a Python list (see example below).

        Examples:
            Retrieve all records that match the query provided by an `OnyxField` object:
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
            ```python
            >>> records
            [
                {
                    "climb_id": "C-1234567890",
                    "published_date": "2023-01-01",
                    "field1": "abcd",
                    "field2": 123,
                },
                {
                    "climb_id": "C-1234567891",
                    "published_date": "2023-01-02",
                    "field1": "abcd",
                    "field2": 456,
                },
            ]
            ```
        """

        responses = super().query(
            project,
            query=query,
            include=include,
            exclude=exclude,
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
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.

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
    def history(
        self,
        project: str,
        climb_id: str,
    ) -> Dict[str, Any]:
        """
        View the history of a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record in the project.

        Returns:
            Dict containing the history of the record.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                history = client.history("project", "C-1234567890")
            ```
            ```python
            >>> history
            {
                "climb_id": "C-1234567890",
                "history": [
                    {
                        "username": "user",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "action": "add",
                    },
                    {
                        "username": "user",
                        "timestamp": "2023-01-02T00:00:00Z",
                        "action": "change",
                        "changes": [
                            {
                                "field": "field_1",
                                "type": "text",
                                "from": "value1",
                                "to": "value2",
                            },
                            {
                                "field": "field_2",
                                "type": "integer",
                                "from": 3,
                                "to": 4,
                            },
                            {
                                "field": "nested_field",
                                "type": "relation",
                                "action": "add",
                                "count" : 3,
                            },
                            {
                                "field": "nested_field",
                                "type": "relation",
                                "action": "change",
                                "count" : 10,
                            },
                        ],
                    },
                ],
            }
            ```
        """
        response = super().history(project, climb_id)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def identify(
        self,
        project: str,
        field: str,
        value: str,
        site: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get the anonymised identifier for a value on a field.

        Args:
            project: Name of the project.
            field: Field on the project.
            value: Value to identify.
            site: Site to identify the value on. If not provided, defaults to the user's site.

        Returns:
            Dict containing the project, site, field, value and anonymised identifier.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                identification = client.identify("project", "sample_id", "hidden-value")
            ```
            ```python
            >>> identification
            {
                "project": "project",
                "site": "site",
                "field": "sample_id",
                "value": "hidden-value",
                "identifier": "S-1234567890",
            }
            ```
        """

        response = super().identify(project, field, value, site=site)
        response.raise_for_status()
        return response.json()["data"]

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
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the created record.

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
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().create(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def update(
        self,
        project: str,
        climb_id: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Update a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record in the project.
            fields: Object representing the record to be updated.
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the updated record.

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
                    climb_id="C-1234567890",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                    },
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().update(project, climb_id, fields=fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def delete(
        self,
        project: str,
        climb_id: str,
    ) -> Dict[str, Any]:
        """
        Delete a record in a project.

        Args:
            project: Name of the project.
            climb_id: Unique identifier for the record in the project.

        Returns:
            Dict containing the CLIMB ID of the deleted record.

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
                    climb_id="C-1234567890",
                )
            ```
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```
        """

        response = super().delete(project, climb_id)
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
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the created record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each created record.

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
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

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
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
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
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`
            test: If `True`, runs the command as a test. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the updated record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each updated record.

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
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

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
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
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
            delimiter: CSV delimiter. If not provided, defaults to `","` for CSVs. Set this to `"\\t"` to work with TSV files.
            multiline: If `True`, allows processing of CSV files with more than one record. Default: `False`

        Returns:
            Dict containing the CLIMB ID of the deleted record. If `multiline = True`, returns a list of dicts containing the CLIMB ID of each deleted record.

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
            ```python
            >>> result
            {"climb_id": "C-1234567890"}
            ```

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
            ```python
            >>> results
            [
                {"climb_id": "C-1234567890"},
                {"climb_id": "C-1234567891"},
                {"climb_id": "C-1234567892"},
            ]
            ```
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
            ```python
            >>> registration
            {
                "username": "onyx-willb",
                "site": "site",
                "email": "bill@email.com",
                "first_name": "Bill",
                "last_name": "Will",
            }
            ```
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
            ```python
            >>> token
            {
                "expiry": "2024-01-01T00:00:00.000000Z",
                "token": "abc123",
            }
            ```
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
            ```python
            >>> profile
            {
                "username": "user",
                "site": "site",
                "email": "user@email.com",
            }
            ```
        """

        response = super().profile()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def activity(self) -> List[Dict[str, Any]]:
        """
        View the user's latest activity.

        Returns:
            List of the user's latest activity.

        Examples:
            ```python
            import os
            from onyx import OnyxConfig, OnyxEnv, OnyxClient

            config = OnyxConfig(
                domain=os.environ[OnyxEnv.DOMAIN],
                token=os.environ[OnyxEnv.TOKEN],
            )

            with OnyxClient(config) as client:
                activity = client.activity()
            ```
            ```python
            >>> activity
            [
                {
                    "date": "2023-01-01T00:00:00.000000Z",
                    "address": "127.0.0.1",
                    "endpoint": "/projects/project/",
                    "method": "POST",
                    "status": 400,
                    "exec_time": 29,
                    "error_messages" : "b'{\"status\":\"fail\",\"code\":400,\"messages\":{\"site\":[\"Select a valid choice.\"]}}'",
                },
                {
                    "timestamp": "2023-01-02T00:00:00.000000Z",
                    "address": "127.0.0.1",
                    "endpoint": "/accounts/activity/",
                    "method": "GET",
                    "status": 200,
                    "exec_time": 22,
                    "error_messages": "",
                },
            ]
            ```
        """

        response = super().activity()
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
            ```python
            >>> approval
            {
                "username": "waiting_user",
                "is_approved": True,
            }
            ```
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
            ```python
            >>> users
            [
                {
                    "username": "waiting_user",
                    "site": "site",
                    "email": "waiting_user@email.com",
                    "date_joined": "2023-01-01T00:00:00.000000Z",
                }
            ]
            ```
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
            ```python
            >>> users
            [
                {
                    "username": "user",
                    "site": "site",
                    "email": "user@email.com",
                }
            ]
            ```
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
            ```python
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
            ```
        """

        response = super().all_users()
        response.raise_for_status()
        return response.json()["data"]
