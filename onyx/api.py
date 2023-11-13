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
    ) -> Generator[requests.Response, Any, None]:
        if fields is None:
            fields = {}

        fields = fields | {"include": include, "exclude": exclude, "scope": scope}
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
                _next = response.json()["next"]
            else:
                _next = None

    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
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

        fields = {"include": include, "exclude": exclude, "scope": scope}
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
                _next = response.json()["next"]
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

    def __init__(self, config: OnyxConfig):
        """
        Initialise a client.

        :param config: Object that stores information for connecting and authenticating with Onyx.
        """
        super().__init__(config)

    @onyx_errors
    def projects(self) -> List[Dict[str, str]]:
        """
        View available projects.
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

        :param project: Name of the project.
        :param scope: Additional named group(s) of fields to include in the output.
        """

        response = super().fields(project, scope=scope)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.

        :param project: Name of the project.
        :param field: Choice field on the project.
        """

        response = super().choices(project, field)
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

        :param project: Name of the project.
        :param fields: Object representing the record to be created.
        :param test: If True, runs the command as a test. Default: False
        """

        response = super().create(project, fields, test=test)
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

        :param project: Name of the project.
        :param cid: Unique identifier for the record in the project.
        :param fields: Series of conditions on fields, used to uniquely identify a record.
        :param include: Fields to include in the output.
        :param exclude: Fields to exclude from the output.
        :param scope: Additional named group(s) of fields to include in the output.
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
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter records from a project.

        :param project: Name of the project.
        :param fields: Series of conditions on fields, used to filter the data.
        :param include: Fields to include in the output.
        :param exclude: Fields to exclude from the output.
        :param scope: Additional named group(s) of fields to include in the output.
        """

        responses = super().filter(
            project,
            fields=fields,
            include=include,
            exclude=exclude,
            scope=scope,
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
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Query records from a project.

        :param project: Name of the project.
        :param query: Arbitrarily complex expression on fields, used to filter the data.
        :param include: Fields to include in the output.
        :param exclude: Fields to exclude from the output.
        :param scope: Additional named group(s) of fields to include in the output.
        """

        responses = super().query(
            project,
            query=query,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

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

        :param project: Name of the project.
        :param cid: Unique identifier for the record in the project.
        :param fields: Object representing the updates being made to the record.
        :param test: If True, runs the command as a test. Default: False
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

        :param project: Name of the project.
        :param cid: Unique identifier for the record in the project.
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

        :param project: Name of the project.
        :param csv_file: File object for the CSV file being used for record upload.
        :param fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
        :param delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
        :param multiline: If True, allows processing of CSV files with more than one record. Default: False
        :param test: If True, runs the command as a test. Default: False
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

        :param project: Name of the project.
        :param csv_file: File object for the CSV file being used for record upload.
        :param fields: Additional fields provided for each record being uploaded. Takes precedence over fields in the CSV.
        :param delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
        :param multiline: If True, allows processing of CSV files with more than one record. Default: False
        :param test: If True, runs the command as a test. Default: False
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

        :param project: Name of the project.
        :param csv_file: File object for the CSV file being used for record upload.
        :param delimiter: CSV delimiter. If not provided, defaults to ',' for CSVs. Set this to '\\t' to work with TSV files.
        :param multiline: If True, allows processing of CSV files with more than one record. Default: False
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

        :param domain: Domain name for connecting to Onyx.
        :param first_name: First name of the registering user.
        :param last_name: Last name of the registering user.
        :param email: Email of the registering user.
        :param site: Site code of the registering user.
        :param password: Password of the registering user.
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
        """

        response = super().login()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def logout(self) -> None:
        """
        Log out the user.
        """

        response = super().logout()
        response.raise_for_status()

    @onyx_errors
    def logoutall(self) -> None:
        """
        Log out the user in all clients.
        """

        response = super().logoutall()
        response.raise_for_status()

    @onyx_errors
    def profile(self) -> Dict[str, str]:
        """
        View the user's information.
        """

        response = super().profile()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def approve(self, username: str) -> Dict[str, Any]:
        """
        Approve another user.

        :param username: Name of the user being approved.
        """

        response = super().approve(username)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def waiting(self) -> List[Dict[str, Any]]:
        """
        Get users waiting for approval.
        """

        response = super().waiting()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def site_users(self) -> List[Dict[str, Any]]:
        """
        Get users within the site of the requesting user.
        """

        response = super().site_users()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_errors
    def all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        """

        response = super().all_users()
        response.raise_for_status()
        return response.json()["data"]
