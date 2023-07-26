import os
import sys
import csv
import json
import requests
import concurrent.futures
from django_query_tools.client import F
from .utils import get_input
from .config import OnyxConfig
from typing import Any, Generator, List, Dict, IO


PASSWORD_ENV_VAR_PREFIX = "ONYX_"
PASSWORD_ENV_VAR_POSTFIX = "_PASSWORD"
ENDPOINTS = {
    # ACCOUNTS
    "register": lambda domain: os.path.join(domain, "accounts/register/"),
    "login": lambda domain: os.path.join(domain, "accounts/login/"),
    "logout": lambda domain: os.path.join(domain, "accounts/logout/"),
    "logoutall": lambda domain: os.path.join(domain, "accounts/logoutall/"),
    "site_approve": lambda domain, username: os.path.join(
        domain, f"accounts/site/approve/{username}/"
    ),
    "site_waiting": lambda domain: os.path.join(domain, "accounts/site/waiting/"),
    "site_users": lambda domain: os.path.join(domain, "accounts/site/users/"),
    "admin_approve": lambda domain, username: os.path.join(
        domain, f"accounts/admin/approve/{username}/"
    ),
    "admin_waiting": lambda domain: os.path.join(domain, "accounts/admin/waiting/"),
    "admin_users": lambda domain: os.path.join(domain, "accounts/admin/users/"),
    # DATA
    "create": lambda domain, project: os.path.join(domain, f"data/create/{project}/"),
    "testcreate": lambda domain, project: os.path.join(
        domain, f"data/testcreate/{project}/"
    ),
    "get": lambda domain, project, cid: os.path.join(
        domain, f"data/get/{project}/{cid}/"
    ),
    "filter": lambda domain, project: os.path.join(domain, f"data/filter/{project}/"),
    "query": lambda domain, project: os.path.join(domain, f"data/query/{project}/"),
    "update": lambda domain, project, cid: os.path.join(
        domain, f"data/update/{project}/{cid}/"
    ),
    "testupdate": lambda domain, project, cid: os.path.join(
        domain, f"data/testupdate/{project}/{cid}/"
    ),
    "suppress": lambda domain, project, cid: os.path.join(
        domain, f"data/suppress/{project}/{cid}/"
    ),
    "testsuppress": lambda domain, project, cid: os.path.join(
        domain, f"data/testsuppress/{project}/{cid}/"
    ),
    "delete": lambda domain, project, cid: os.path.join(
        domain, f"data/delete/{project}/{cid}/"
    ),
    "testdelete": lambda domain, project, cid: os.path.join(
        domain, f"data/testdelete/{project}/{cid}/"
    ),
    "choices": lambda domain, project, cid: os.path.join(
        domain, f"data/choices/{project}/{cid}/"
    ),
}


class OnyxClient:
    def __init__(
        self,
        config: OnyxConfig | None = None,
        username: str | None = None,
        env_password: bool = False,
    ):
        """
        Initialise the client.
        """
        if config:
            self.config = config
        else:
            self.config = OnyxConfig()

        # Assign username/env_password flag to the client
        if username is None:
            # If no username was provided, use the default user
            if self.config.default_user is None:
                raise Exception(
                    "No username was provided and there is no default_user in the config. Either provide a username or set a default_user."
                )
            if self.config.default_user not in self.config.users:
                raise Exception(
                    f"default_user '{self.config.default_user}' is not in the users list for the config."
                )

            username = self.config.default_user
        else:
            # Username is case-insensitive
            username = username.lower()

            # The provided user must be in the config
            if username not in self.config.users:
                raise KeyError(
                    f"User '{username}' is not in the config. Add them using the add-user config command."
                )

        # Assign username to the client
        self.username = username

        # Assign flag indicating whether to look for user's password to the client
        self.env_password = env_password

        # Open the token file for the user and assign the current token, and its expiry, to the client
        token_path = os.path.join(
            self.config.dir_path, self.config.users[username]["token"]
        )
        with open(token_path) as token_file:
            try:
                token_data = json.load(token_file)
            except json.decoder.JSONDecodeError as e:
                raise Exception(
                    f"Failed to parse the tokens file: {token_path}\nSomething is wrong with your tokens file. \nTo fix this, either re-add the user to the config via the CLI, or correct the file manually."
                ) from e
            self.token = token_data.get("token")
            self.expiry = token_data.get("expiry")

        self._request_handler = requests.request

    def __enter__(self):
        self.session = requests.Session()
        self._request_handler = self.session.request
        return self

    def __exit__(self, type, value, traceback):
        self.session.close()
        del self.session
        self._request_handler = requests.request

    def _csv_upload(
        self,
        method: str,
        endpoint: str,
        project: str,
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
        multithreaded: bool = False,
        test: bool = False,
        cid_required: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        if test:
            endpoint = "test" + endpoint

        if multithreaded and not self.env_password:
            raise Exception("Multithreaded mode requires env_password = True.")

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
                        url=ENDPOINTS[endpoint](self.config.domain, project, cid),
                        json=record,
                    )
                    yield response

                    if multithreaded:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [
                                executor.submit(
                                    self._request,
                                    method,
                                    url=ENDPOINTS[endpoint](
                                        self.config.domain, project, record.pop("cid")
                                    ),
                                    json=record,
                                )
                                for record in reader
                            ]
                            for future in concurrent.futures.as_completed(futures):
                                yield future.result()
                    else:
                        for record in reader:
                            response = self._request(
                                method=method,
                                url=ENDPOINTS[endpoint](
                                    self.config.domain, project, record.pop("cid")
                                ),
                                json=record,
                            )
                            yield response
                else:
                    response = self._request(
                        method=method,
                        url=ENDPOINTS[endpoint](self.config.domain, project),
                        json=record,
                    )
                    yield response

                    if multithreaded:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = [
                                executor.submit(
                                    self._request,
                                    method,
                                    url=ENDPOINTS[endpoint](
                                        self.config.domain, project
                                    ),
                                    json=record,
                                )
                                for record in reader
                            ]
                            for future in concurrent.futures.as_completed(futures):
                                yield future.result()
                    else:
                        for record in reader:
                            response = self._request(
                                method=method,
                                url=ENDPOINTS[endpoint](self.config.domain, project),
                                json=record,
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
            {"Authorization": f"Token {self.token}"}
        )
        method_response = self._request_handler(method, **kwargs)

        # Token has expired.
        # If an env_password was provided, log in again, obtain a new token, and re-run the method.
        if method_response.status_code == 401 and self.env_password:
            self._login().raise_for_status()
            # A retry mechanism has been incorporated as a failsafe.
            # This is to protect against the case where an onyx endpoint returns a 401 status code,
            # despite the user being able to successfully log in, leading to an infinite loop of
            # re-logging in and re-hitting the endpoint.
            # This scenario should not be possible. But if it happened, it would not be fun at all.
            # So, better safe than sorry...
            return self._request(method, retries=retries - 1, **kwargs)

        return method_response

    def _get_password(self):
        if self.env_password:
            # If the password is meant to be an env var, grab it.
            # If its not there, this is unintended so an error is raised
            password_env_var = (
                PASSWORD_ENV_VAR_PREFIX
                + self.username.upper()
                + PASSWORD_ENV_VAR_POSTFIX
            )
            password = os.environ[password_env_var]
        else:
            # Otherwise, prompt for the password
            print("Please enter your password.")
            password = get_input("password", password=True)
        return password

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
            ENDPOINTS["register"](config.domain),
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
        response = cls._register(config, first_name, last_name, email, site, password)
        response.raise_for_status()
        return response.json()["data"]

    def _login(self) -> requests.Response:
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """
        # Get the password
        password = self._get_password()

        # Log in
        response = self._request_handler(
            "post",
            auth=(self.username, password),
            url=ENDPOINTS["login"](self.config.domain),
        )
        if response.ok:
            self.token = response.json()["data"]["token"]
            self.expiry = response.json()["data"]["expiry"]
            self.config.write_token(self.username, self.token, self.expiry)

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
            url=ENDPOINTS["logout"](self.config.domain),
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

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
            url=ENDPOINTS["logoutall"](self.config.domain),
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    def logoutall(self) -> None:
        """
        Log out the user in all clients.
        """
        response = self._logoutall()
        response.raise_for_status()

    def _site_approve(self, username: str) -> requests.Response:
        """
        Site-approve another user.
        """
        response = self._request(
            method="patch",
            url=ENDPOINTS["site_approve"](self.config.domain, username),
        )
        return response

    def site_approve(self, username: str) -> Dict[str, Any]:
        """
        Site-approve another user.
        """
        response = self._site_approve(username)
        response.raise_for_status()
        return response.json()["data"]

    def _site_list_waiting(self) -> requests.Response:
        """
        List users waiting for site approval.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["site_waiting"](self.config.domain),
        )
        return response

    def site_list_waiting(self) -> List[Dict[str, Any]]:
        """
        List users waiting for site approval.
        """
        response = self._site_list_waiting()
        response.raise_for_status()
        return response.json()["data"]

    def _site_list_users(self) -> requests.Response:
        """
        Get the current users within the site of the requesting user.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["site_users"](self.config.domain),
        )
        return response

    def site_list_users(self) -> List[Dict[str, Any]]:
        """
        Get the current users within the site of the requesting user.
        """
        response = self._site_list_users()
        response.raise_for_status()
        return response.json()["data"]

    def _admin_approve(self, username: str) -> requests.Response:
        """
        Admin-approve another user.
        """
        response = self._request(
            method="patch",
            url=ENDPOINTS["admin_approve"](self.config.domain, username),
        )
        return response

    def admin_approve(self, username: str) -> Dict[str, Any]:
        """
        Admin-approve another user.
        """
        response = self._admin_approve(username)
        response.raise_for_status()
        return response.json()["data"]

    def _admin_list_waiting(self) -> requests.Response:
        """
        List users waiting for admin approval.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["admin_waiting"](self.config.domain),
        )
        return response

    def admin_list_waiting(self) -> List[Dict[str, Any]]:
        """
        List users waiting for admin approval.
        """
        response = self._admin_list_waiting()
        response.raise_for_status()
        return response.json()["data"]

    def _admin_list_users(self) -> requests.Response:
        """
        List all users.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["admin_users"](self.config.domain),
        )
        return response

    def admin_list_users(self) -> List[Dict[str, Any]]:
        """
        List all users.
        """
        response = self._admin_list_users()
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
            url=ENDPOINTS[endpoint](self.config.domain, project),
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
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
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
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
        )

    def csv_create(
        self,
        project: str,
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
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
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
    ) -> requests.Response:
        """
        Get a record from the database.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["get"](self.config.domain, project, cid),
            params={"include": include, "exclude": exclude, "scope": scope},
        )
        return response

    def get(
        self,
        project: str,
        cid: str,
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
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
        return response.json()["data"]["record"]

    def _filter(
        self,
        project: str,
        fields: Dict[str, Any] | None = None,
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
    ) -> Generator[requests.Response, Any, None]:
        """
        Filter records from the database.
        """
        if fields is None:
            fields = {}

        fields = fields | {"include": include, "exclude": exclude, "scope": scope}
        _next = ENDPOINTS["filter"](self.config.domain, project)

        while _next is not None:
            response = self._request(
                method="get",
                url=_next,
                params=fields,
            )
            yield response

            fields = None
            if response.ok:
                _next = response.json()["data"]["next"]
            else:
                _next = None

    def filter(
        self,
        project: str,
        fields: Dict[str, Any] | None = None,
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
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
            for result in response.json()["data"]["records"]:
                yield result

    def _query(
        self,
        project: str,
        query: F | None = None,
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
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
        _next = ENDPOINTS["query"](self.config.domain, project)

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
                _next = response.json()["data"]["next"]
            else:
                _next = None

    def query(
        self,
        project: str,
        query: F | None = None,
        include: List[str] | str | None = None,
        exclude: List[str] | str | None = None,
        scope: List[str] | str | None = None,
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
            for result in response.json()["data"]["records"]:
                yield result

    def _update(
        self,
        project: str,
        cid: str,
        fields: Dict[str, Any] | None = None,
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
            url=ENDPOINTS[endpoint](self.config.domain, project, cid),
            json=fields,
        )
        return response

    def update(
        self,
        project: str,
        cid: str,
        fields: Dict[str, Any] | None = None,
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
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
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
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
            cid_required=True,
        )

    def csv_update(
        self,
        project: str,
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Use a .csv or .tsv to update records in the database.
        """
        responses = self._csv_update(
            project,
            csv_path,
            delimiter=delimiter,
            test=test,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    def _suppress(
        self,
        project: str,
        cid: str,
        test: bool = False,
    ) -> requests.Response:
        """
        Suppress a record in the database.
        """
        if test:
            endpoint = "testsuppress"
        else:
            endpoint = "suppress"

        response = self._request(
            method="delete",
            url=ENDPOINTS[endpoint](self.config.domain, project, cid),
        )
        return response

    def suppress(
        self,
        project: str,
        cid: str,
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Suppress a record in the database.
        """
        response = self._suppress(project, cid, test=test)
        response.raise_for_status()
        return response.json()["data"]

    def _csv_suppress(
        self,
        project: str,
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
        multithreaded: bool = False,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to suppress records in the database.
        """
        yield from self._csv_upload(
            method="delete",
            endpoint="suppress",
            project=project,
            csv_path=csv_path,
            csv_file=csv_file,
            delimiter=delimiter,
            multithreaded=multithreaded,
            test=test,
            cid_required=True,
        )

    def csv_suppress(
        self,
        project: str,
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Use a .csv or .tsv to suppress records in the database.
        """
        responses = self._csv_suppress(
            project,
            csv_path,
            delimiter=delimiter,
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
        test: bool = False,
    ) -> requests.Response:
        """
        Delete a record in the database.
        """
        if test:
            endpoint = "testdelete"
        else:
            endpoint = "delete"

        response = self._request(
            method="delete",
            url=ENDPOINTS[endpoint](self.config.domain, project, cid),
        )
        return response

    def delete(
        self,
        project: str,
        cid: str,
        test: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete a record in the database.
        """
        response = self._suppress(project, cid, test=test)
        response.raise_for_status()
        return response.json()["data"]

    def _csv_delete(
        self,
        project: str,
        csv_path: str | None = None,
        csv_file: IO | None = None,
        delimiter: str | None = None,
        multithreaded: bool = False,
        test: bool = False,
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
            test=test,
            cid_required=True,
        )

    def csv_delete(
        self,
        project: str,
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[Dict[str, Any], Any, None]:
        """
        Use a .csv or .tsv to delete records in the database.
        """
        responses = self._csv_delete(
            project,
            csv_path,
            delimiter=delimiter,
            test=test,
        )
        for response in responses:
            response.raise_for_status()
            for result in response.json()["data"]:
                yield result

    def _choices(self, project: str, field: str) -> requests.Response:
        """
        View choices for a field.
        """
        response = self._request(
            method="get",
            url=ENDPOINTS["choices"](self.config.domain, project, field),
        )
        return response

    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.
        """
        response = self._choices(project, field)
        response.raise_for_status()
        return response.json()["data"]["choices"]
