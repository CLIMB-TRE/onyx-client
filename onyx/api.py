import os
import sys
import csv
import requests
import concurrent.futures
from typing import Any, Generator, List, Dict, IO, Optional, Union
from django_query_tools.client import F as OnyxField
from .config import OnyxConfig


class OnyxError(Exception):
    def __init__(self, response: requests.Response):
        self.response = response


def onyx_error(method):
    def wrapped_method(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except requests.HTTPError as e:
            if e.response is None:
                raise e

            raise OnyxError(e.response)

    return wrapped_method


class OnyxClientBase:
    __slots__ = "config", "_request_handler", "_session"
    ENDPOINTS = {
        "register": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/register/"),
            domain=domain,
        ),
        "login": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/login/"),
            domain=domain,
        ),
        "logout": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/logout/"),
            domain=domain,
        ),
        "logoutall": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/logoutall/"),
            domain=domain,
        ),
        "profile": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/profile/"),
            domain=domain,
        ),
        "waiting": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/waiting/"),
            domain=domain,
        ),
        "approve": lambda domain, username: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/approve", username, ""),
            domain=domain,
            username=username,
        ),
        "siteusers": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/site/"),
            domain=domain,
        ),
        "allusers": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "accounts/all/"),
            domain=domain,
        ),
        "projects": lambda domain: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects/"),
            domain=domain,
        ),
        "fields": lambda domain, project: OnyxClient._handle_endpoint(
            os.path.join(domain, f"projects", project, "fields/"),
            domain=domain,
            project=project,
        ),
        "choices": lambda domain, project, field: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, "choices", field, ""),
            domain=domain,
            project=project,
            field=field,
        ),
        "create": lambda domain, project: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, ""),
            domain=domain,
            project=project,
        ),
        "filter": lambda domain, project: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, ""),
            domain=domain,
            project=project,
        ),
        "get": lambda domain, project, cid: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, cid, ""),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "update": lambda domain, project, cid: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, cid, ""),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "delete": lambda domain, project, cid: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, cid, ""),
            domain=domain,
            project=project,
            cid=cid,
        ),
        "query": lambda domain, project: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, "query/"),
            domain=domain,
            project=project,
        ),
        "testcreate": lambda domain, project: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, "test/"),
            domain=domain,
            project=project,
        ),
        "testupdate": lambda domain, project, cid: OnyxClient._handle_endpoint(
            os.path.join(domain, "projects", project, "test", cid, ""),
            domain=domain,
            project=project,
            cid=cid,
        ),
    }

    def __init__(self, config: OnyxConfig):
        """
        Initialise a client.

        Parameters
        ----------
        config : OnyxConfig
            Object that stores information for connecting and authenticating with Onyx.
        """

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
            if not val or not str(val).strip():
                raise Exception(f"Endpoint argument '{name}' was not provided.")

        return endpoint

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
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
        cid_required: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        if test:
            endpoint = "test" + endpoint

        if multithreaded and not (self.config.username and self.config.password):
            raise Exception("Multithreaded mode requires a username and password.")

        if csv_path and csv_file:
            raise Exception("Cannot provide both csv_path and csv_file.")

        if csv_path:
            if csv_path == "-":
                csv_file = sys.stdin
            else:
                csv_file = open(csv_path)
        else:
            if not csv_file:
                raise Exception("Must provide either csv_path or csv_file.")

        overwrite = lambda x, ow: x | ow if ow else x

        try:
            if delimiter is None:
                reader = csv.DictReader(csv_file)
            else:
                reader = csv.DictReader(csv_file, delimiter=delimiter)

            record = next(reader, None)

            if record:
                if cid_required:
                    cid = record.pop("cid", None)
                    if cid is None:
                        raise KeyError("A 'cid' column must be provided.")

                    response = self._request(
                        method=method,
                        url=OnyxClient.ENDPOINTS[endpoint](
                            self.config.domain, project, cid
                        ),
                        json=overwrite(record, fields),
                    )
                    yield response

                    if multithreaded:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [
                                executor.submit(
                                    self._request,
                                    method,
                                    url=OnyxClient.ENDPOINTS[endpoint](
                                        self.config.domain, project, record.pop("cid")
                                    ),
                                    json=overwrite(record, fields),
                                )
                                for record in reader
                            ]
                            for future in concurrent.futures.as_completed(futures):
                                yield future.result()
                    else:
                        for record in reader:
                            response = self._request(
                                method=method,
                                url=OnyxClient.ENDPOINTS[endpoint](
                                    self.config.domain, project, record.pop("cid")
                                ),
                                json=overwrite(record, fields),
                            )
                            yield response
                else:
                    response = self._request(
                        method=method,
                        url=OnyxClient.ENDPOINTS[endpoint](self.config.domain, project),
                        json=overwrite(record, fields),
                    )
                    yield response

                    if multithreaded:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [
                                executor.submit(
                                    self._request,
                                    method,
                                    url=OnyxClient.ENDPOINTS[endpoint](
                                        self.config.domain, project
                                    ),
                                    json=overwrite(record, fields),
                                )
                                for record in reader
                            ]
                            for future in concurrent.futures.as_completed(futures):
                                yield future.result()
                    else:
                        for record in reader:
                            response = self._request(
                                method=method,
                                url=OnyxClient.ENDPOINTS[endpoint](
                                    self.config.domain, project
                                ),
                                json=overwrite(record, fields),
                            )
                            yield response
        finally:
            # Close the file, only if it was opened within this function
            if csv_path and csv_file is not sys.stdin:
                csv_file.close()

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

    def csv_create(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="post",
            endpoint="create",
            project=project,
            csv_path=csv_path,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
        )

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
                raise Exception(f"Query must be an instance of {OnyxField}.")
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

    def csv_update(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="patch",
            endpoint="update",
            project=project,
            csv_path=csv_path,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
            cid_required=True,
        )

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

    def csv_delete(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        yield from self._csv_upload(
            method="delete",
            endpoint="delete",
            project=project,
            csv_path=csv_path,
            csv_file=csv_file,
            delimiter=delimiter,
            multithreaded=multithreaded,
            cid_required=True,
        )

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


class OnyxClient(OnyxClientBase):
    """
    Class for querying and manipulating metadata within Onyx.
    """

    @classmethod
    @onyx_error
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

    @onyx_error
    def login(self) -> Dict[str, Any]:
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """

        response = super().login()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def logout(self) -> None:
        """
        Log out the user in this client.
        """

        response = super().logout()
        response.raise_for_status()

    @onyx_error
    def logoutall(self) -> None:
        """
        Log out the user in all clients.
        """

        response = super().logoutall()
        response.raise_for_status()

    @onyx_error
    def profile(self) -> Dict[str, str]:
        """
        View the logged-in user's information.
        """

        response = super().profile()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def approve(self, username: str) -> Dict[str, Any]:
        """
        Approve another user.
        """

        response = super().approve(username)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def waiting(self) -> List[Dict[str, Any]]:
        """
        Get users waiting for approval.
        """

        response = super().waiting()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def site_users(self) -> List[Dict[str, Any]]:
        """
        Get the users within the site of the requesting user.
        """

        response = super().site_users()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        """

        response = super().all_users()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Post a record to the database.
        """

        response = super().create(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def csv_create(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Post a .csv or .tsv containing records to the database.
        """

        responses = super().csv_create(
            project,
            csv_path=csv_path,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_error
    def get(
        self,
        project: str,
        cid: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        Get a record from the database.
        """

        response = super().get(
            project,
            cid,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Filter records from the database.
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

    @onyx_error
    def query(
        self,
        project: str,
        query: Optional[OnyxField] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Get records from the database.
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

    @onyx_error
    def update(
        self,
        project: str,
        cid: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Update a record in the database.
        """

        response = super().update(project, cid, fields=fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def csv_update(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Use a .csv or .tsv to update records in the database.
        """

        responses = super().csv_update(
            project,
            csv_path=csv_path,
            csv_file=csv_file,
            fields=fields,
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_error
    def delete(
        self,
        project: str,
        cid: str,
    ) -> Dict[str, Any]:
        """
        Delete a record in the database.
        """

        response = super().delete(project, cid)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def csv_delete(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Use a .csv or .tsv to delete records in the database.
        """

        responses = super().csv_delete(
            project,
            csv_path=csv_path,
            csv_file=csv_file,
            delimiter=delimiter,
            multithreaded=multithreaded,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    @onyx_error
    def projects(self) -> List[Dict[str, str]]:
        """
        View available projects.
        """

        response = super().projects()
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def fields(
        self,
        project: str,
        scope: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        View fields for a project.
        """

        response = super().fields(project, scope=scope)
        response.raise_for_status()
        return response.json()["data"]

    @onyx_error
    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.
        """

        response = super().choices(project, field)
        response.raise_for_status()
        return response.json()["data"]
