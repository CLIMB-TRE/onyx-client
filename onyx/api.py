import os
import sys
import csv
import requests
import concurrent.futures
from typing import Any, Generator, List, Dict, IO, Optional, Union
from django_query_tools.client import F
from .config import OnyxConfig


class OnyxClient:
    __slots__ = "config", "_request_handler", "_session"
    ENDPOINTS = {
        "register": lambda domain: os.path.join(domain, "accounts/register/"),
        "login": lambda domain: os.path.join(domain, "accounts/login/"),
        "logout": lambda domain: os.path.join(domain, "accounts/logout/"),
        "logoutall": lambda domain: os.path.join(domain, "accounts/logoutall/"),
        "profile": lambda domain: os.path.join(domain, "accounts/profile/"),
        "waiting": lambda domain: os.path.join(domain, "accounts/waiting/"),
        "approve": lambda domain, username: os.path.join(
            domain, "accounts/approve", username, ""
        ),
        "siteusers": lambda domain: os.path.join(domain, "accounts/site/"),
        "allusers": lambda domain: os.path.join(domain, "accounts/all/"),
        "projects": lambda domain: os.path.join(domain, "projects/"),
        "fields": lambda domain, project: os.path.join(
            domain, f"projects", project, "fields/"
        ),
        "choices": lambda domain, project, field: os.path.join(
            domain, "projects", project, "choices", field, ""
        ),
        "create": lambda domain, project: os.path.join(domain, "projects", project, ""),
        "filter": lambda domain, project: os.path.join(domain, "projects", project, ""),
        "get": lambda domain, project, cid: os.path.join(
            domain, "projects", project, cid, ""
        ),
        "update": lambda domain, project, cid: os.path.join(
            domain, "projects", project, cid, ""
        ),
        "delete": lambda domain, project, cid: os.path.join(
            domain, "projects", project, cid, ""
        ),
        "query": lambda domain, project: os.path.join(
            domain, "projects", project, "query/"
        ),
        "testcreate": lambda domain, project: os.path.join(
            domain, "projects", project, "test/"
        ),
        "testupdate": lambda domain, project, cid: os.path.join(
            domain, "projects", project, "test", cid, ""
        ),
    }

    def __init__(self, config: OnyxConfig):
        """Initialise the client.

        Parameters
        ----------
        config : OnyxConfig
            Config object containing user credentials.
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

        if multithreaded and not self.config.password:
            raise Exception("Multithreaded mode requires a password.")

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

    def _request(self, method: str, retries: int = 3, **kwargs) -> requests.Response:
        """
        Carry out a request while handling token authorisation.
        """

        if not retries:
            raise Exception(
                "Request retry limit reached. This should not be possible..."
            )

        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.config.token}"}
        )
        method_response = self._request_handler(method, **kwargs)

        # Token has expired.
        # If a password was provided, log in again, obtain a new token, and re-run the method.
        if method_response.status_code == 401 and self.config.password:
            self._login().raise_for_status()
            # A retry mechanism has been incorporated as a failsafe.
            # This is to protect against the case where an onyx endpoint returns a 401 status code,
            # despite the user being able to successfully log in, leading to an infinite loop of
            # re-logging in and re-hitting the endpoint.
            # This scenario should not be possible. But if it happened, it would not be fun at all.
            # So, better safe than sorry...
            return self._request(method, retries=retries - 1, **kwargs)

        return method_response

    @classmethod
    def _register(
        cls,
        config: OnyxConfig,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> requests.Response:
        """
        Create a new user.
        """

        response = requests.post(
            OnyxClient.ENDPOINTS["register"](config.domain),
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "site": site,
            },
        )
        return response

    @classmethod
    def register(
        cls,
        config: OnyxConfig,
        first_name: str,
        last_name: str,
        email: str,
        site: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Create a new user.
        """

        response = cls._register(
            config,
            first_name,
            last_name,
            email,
            site,
            password,
        )
        response.raise_for_status()
        return response.json()["data"]

    def _login(self) -> requests.Response:
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """

        # TODO: Handle properly
        assert self.config.username
        assert self.config.password

        response = self._request_handler(
            "post",
            auth=(self.config.username, self.config.password),
            url=OnyxClient.ENDPOINTS["login"](self.config.domain),
        )
        if response.ok:
            self.config.token = response.json()["data"]["token"]
            self.config.write_token(self.config.token)

        return response

    def login(self) -> Dict[str, Any]:
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """

        response = self._login()
        response.raise_for_status()
        return response.json()["data"]

    def _logout(self) -> requests.Response:
        """
        Log out the user in this client.
        """

        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS["logout"](self.config.domain),
        )
        if response.ok:
            self.config.token = None
            self.config.write_token(self.config.token)

        return response

    def logout(self) -> None:
        """
        Log out the user in this client.
        """

        response = self._logout()
        response.raise_for_status()

    def _logoutall(self) -> requests.Response:
        """
        Log out the user in all clients.
        """

        response = self._request(
            method="post",
            url=OnyxClient.ENDPOINTS["logoutall"](self.config.domain),
        )
        if response.ok:
            self.config.token = None
            self.config.write_token(self.config.token)

        return response

    def logoutall(self) -> None:
        """
        Log out the user in all clients.
        """

        response = self._logoutall()
        response.raise_for_status()

    def _profile(self) -> requests.Response:
        """
        View the logged-in user's information.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["profile"](self.config.domain),
        )
        return response

    def profile(self) -> Dict[str, str]:
        """
        View the logged-in user's information.
        """

        response = self._profile()
        response.raise_for_status()
        return response.json()["data"]

    def _approve(self, username: str) -> requests.Response:
        """
        Approve a user.
        """

        response = self._request(
            method="patch",
            url=OnyxClient.ENDPOINTS["approve"](self.config.domain, username),
        )
        return response

    def approve(self, username: str) -> Dict[str, Any]:
        """
        Approve another user.
        """

        response = self._approve(username)
        response.raise_for_status()
        return response.json()["data"]

    def _waiting(self) -> requests.Response:
        """
        Get users waiting for approval.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["waiting"](self.config.domain),
        )
        return response

    def waiting(self) -> List[Dict[str, Any]]:
        """
        Get users waiting for approval.
        """

        response = self._waiting()
        response.raise_for_status()
        return response.json()["data"]

    def _site_users(self) -> requests.Response:
        """
        Get the users within the site of the requesting user.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["siteusers"](self.config.domain),
        )
        return response

    def site_users(self) -> List[Dict[str, Any]]:
        """
        Get the users within the site of the requesting user.
        """

        response = self._site_users()
        response.raise_for_status()
        return response.json()["data"]

    def _all_users(self) -> requests.Response:
        """
        Get all users.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["allusers"](self.config.domain),
        )
        return response

    def all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        """

        response = self._all_users()
        response.raise_for_status()
        return response.json()["data"]

    def _create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> requests.Response:
        """
        Post a record to the database.
        """

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

    def create(
        self,
        project: str,
        fields: Dict[str, Any],
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Post a record to the database.
        """

        response = self._create(project, fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    def _csv_create(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Post a .csv or .tsv containing records to the database.
        """

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

        responses = self._csv_create(
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

    def _get(
        self,
        project: str,
        cid: str,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> requests.Response:
        """
        Get a record from the database.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["get"](self.config.domain, project, cid),
            params={"include": include, "exclude": exclude, "scope": scope},
        )
        return response

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

        response = self._get(
            project,
            cid,
            include=include,
            exclude=exclude,
            scope=scope,
        )
        response.raise_for_status()
        return response.json()["data"]

    def _filter(
        self,
        project: str,
        fields: Optional[Dict[str, Any]] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Generator[requests.Response, Any, None]:
        """
        Filter records from the database.
        """

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

        responses = self._filter(
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

    def _query(
        self,
        project: str,
        query: Optional[F] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Generator[requests.Response, Any, None]:
        """
        Get records from the database.
        """

        if query:
            if not isinstance(query, F):
                raise Exception("Query must be an F object.")
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

    def query(
        self,
        project: str,
        query: Optional[F] = None,
        include: Union[List[str], str, None] = None,
        exclude: Union[List[str], str, None] = None,
        scope: Union[List[str], str, None] = None,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Get records from the database.
        """

        responses = self._query(
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

    def _update(
        self,
        project: str,
        cid: str,
        fields: Optional[Dict[str, Any]] = None,
        test: bool = False,
    ) -> requests.Response:
        """
        Update a record in the database.
        """

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

        response = self._update(project, cid, fields=fields, test=test)
        response.raise_for_status()
        return response.json()["data"]

    def _csv_update(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        fields: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to update records in the database.
        """

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

        responses = self._csv_update(
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

    def _delete(
        self,
        project: str,
        cid: str,
    ) -> requests.Response:
        """
        Delete a record in the database.
        """

        response = self._request(
            method="delete",
            url=OnyxClient.ENDPOINTS["delete"](self.config.domain, project, cid),
        )
        return response

    def delete(
        self,
        project: str,
        cid: str,
    ) -> Dict[str, Any]:
        """
        Delete a record in the database.
        """

        response = self._delete(project, cid)
        response.raise_for_status()
        return response.json()["data"]

    def _csv_delete(
        self,
        project: str,
        csv_path: Optional[str] = None,
        csv_file: Optional[IO] = None,
        delimiter: Optional[str] = None,
        multithreaded: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to delete records in the database.
        """

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

        responses = self._csv_delete(
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

    def _projects(self) -> requests.Response:
        """
        View available projects.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["projects"](self.config.domain),
        )
        return response

    def projects(self) -> Dict[str, List[str]]:
        """
        View available projects.
        """

        response = self._projects()
        response.raise_for_status()
        return response.json()["data"]

    def _fields(
        self,
        project: str,
        scope: Union[List[str], str, None] = None,
    ) -> requests.Response:
        """
        View fields for a project.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["fields"](self.config.domain, project),
            params={"scope": scope},
        )
        return response

    def fields(
        self,
        project: str,
        scope: Union[List[str], str, None] = None,
    ) -> Dict[str, Any]:
        """
        View fields for a project.
        """

        response = self._fields(project, scope=scope)
        response.raise_for_status()
        return response.json()["data"]

    def _choices(self, project: str, field: str) -> requests.Response:
        """
        View choices for a field.
        """

        response = self._request(
            method="get",
            url=OnyxClient.ENDPOINTS["choices"](self.config.domain, project, field),
        )
        return response

    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.
        """

        response = self._choices(project, field)
        response.raise_for_status()
        return response.json()["data"]
