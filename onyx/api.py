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


class OnyxClient:
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
        "create": lambda domain, project: os.path.join(
            domain, f"data/create/{project}/"
        ),
        "testcreate": lambda domain, project: os.path.join(
            domain, f"data/testcreate/{project}/"
        ),
        "get": lambda domain, project, cid: os.path.join(
            domain, f"data/get/{project}/{cid}/"
        ),
        "filter": lambda domain, project: os.path.join(
            domain, f"data/filter/{project}/"
        ),
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

    @classmethod
    def register(cls, config, first_name, last_name, email, site, password):
        """
        Create a new user.
        """
        response = requests.post(
            cls.ENDPOINTS["register"](config.domain),
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "site": site,
            },
        )
        return response

    def __init__(self, config=None, username=None, env_password=False):
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

        self._request = requests.request

    def __enter__(self):
        self.session = requests.Session()
        self._request = self.session.request
        return self

    def __exit__(self, type, value, traceback):
        self.session.close()
        del self.session
        self._request = requests.request

    def get_password(self):
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

    def request(self, method, **kwargs):
        """
        Carry out a request while handling token authorisation.
        """
        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.token}"}
        )
        method_response = self._request(method, **kwargs)

        if method_response.status_code == 401 and self.env_password:
            login_response = self._request(
                "post",
                self.ENDPOINTS["login"](self.config.domain),
                auth=(self.username, self.get_password()),
            )

            if login_response.ok:
                self.token = login_response.json()["data"]["token"]
                self.expiry = login_response.json()["data"]["expiry"]
                self.config.write_token(self.username, self.token, self.expiry)

                # TODO: There is a potential infinite loop here
                # In the case where a valid-authed method somehow returns 401
                return self.request(method, **kwargs)

            login_response.raise_for_status()

        return method_response

    def login(self):
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """
        # Get the password
        password = self.get_password()

        # Log in
        response = self._request(
            "post",
            auth=(self.username, password),
            url=self.ENDPOINTS["login"](self.config.domain),
        )
        if response.ok:
            self.token = response.json()["data"]["token"]
            self.expiry = response.json()["data"]["expiry"]
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    def logout(self):
        """
        Log out the user in this client.
        """
        response = self.request(
            method="post",
            url=self.ENDPOINTS["logout"](self.config.domain),
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    def logoutall(self):
        """
        Log out the user in all clients.
        """
        response = self.request(
            method="post",
            url=self.ENDPOINTS["logoutall"](self.config.domain),
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    def site_approve(self, username):
        """
        Site-approve another user.
        """
        response = self.request(
            method="patch",
            url=self.ENDPOINTS["site_approve"](self.config.domain, username),
        )
        return response

    def site_list_waiting(self):
        """
        List users waiting for site approval.
        """
        response = self.request(
            method="get",
            url=self.ENDPOINTS["site_waiting"](self.config.domain),
        )
        return response

    def site_list_users(self):
        """
        Get the current users within the site of the requesting user.
        """
        response = self.request(
            method="get",
            url=self.ENDPOINTS["site_users"](self.config.domain),
        )
        return response

    def admin_approve(self, username):
        """
        Admin-approve another user.
        """
        response = self.request(
            method="patch",
            url=self.ENDPOINTS["admin_approve"](self.config.domain, username),
        )
        return response

    def admin_list_waiting(self):
        """
        List users waiting for admin approval.
        """
        response = self.request(
            method="get",
            url=self.ENDPOINTS["admin_waiting"](self.config.domain),
        )
        return response

    def admin_list_users(self):
        """
        List all users.
        """
        response = self.request(
            method="get",
            url=self.ENDPOINTS["admin_users"](self.config.domain),
        )
        return response

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

        response = self.request(
            method="post",
            url=self.ENDPOINTS[endpoint](self.config.domain, project),
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
        if test:
            endpoint = "testcreate"
        else:
            endpoint = "create"

        if multithreaded and not self.env_password:
            raise Exception("Multithreaded upload requires env_password = True.")

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
                response = self.request(
                    method="post",
                    url=self.ENDPOINTS[endpoint](self.config.domain, project),
                    json=record,
                )
                yield response

                if multithreaded:
                    # Bit of an experimental one
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(
                                self.request,
                                "post",
                                url=self.ENDPOINTS[endpoint](
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
                        response = self.request(
                            method="post",
                            url=self.ENDPOINTS[endpoint](self.config.domain, project),
                            json=record,
                        )
                        yield response
        finally:
            # Close the file, only if it was opened within this function
            if csv_path and csv_file is not sys.stdin:
                csv_file.close()

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
        response = self.request(
            method="get",
            url=self.ENDPOINTS["get"](self.config.domain, project, cid),
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
        _next = self.ENDPOINTS["filter"](self.config.domain, project)

        while _next is not None:
            response = self.request(
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
        _next = self.ENDPOINTS["query"](self.config.domain, project)

        while _next is not None:
            response = self.request(
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

        response = self.request(
            method="patch",
            url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
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
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to update records in the database.
        """
        if test:
            endpoint = "testupdate"
        else:
            endpoint = "update"

        if csv_path == "-":
            csv_file = sys.stdin
        else:
            csv_file = open(csv_path)
        try:
            if delimiter is None:
                reader = csv.DictReader(csv_file)
            else:
                reader = csv.DictReader(csv_file, delimiter=delimiter)

            for record in reader:
                cid = record.pop("cid", None)
                if cid is None:
                    raise KeyError("A 'cid' column must be provided.")

                response = self.request(
                    method="patch",
                    url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
                    json=record,
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

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

        response = self.request(
            method="delete",
            url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
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
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to suppress records in the database.
        """
        if test:
            endpoint = "testsuppress"
        else:
            endpoint = "suppress"

        if csv_path == "-":
            csv_file = sys.stdin
        else:
            csv_file = open(csv_path)
        try:
            if delimiter is None:
                reader = csv.DictReader(csv_file)
            else:
                reader = csv.DictReader(csv_file, delimiter=delimiter)

            for record in reader:
                cid = record.get("cid")
                if cid is None:
                    raise KeyError("A 'cid' column must be provided.")

                response = self.request(
                    method="delete",
                    url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

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

        response = self.request(
            method="delete",
            url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
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
        csv_path: str,
        delimiter: str | None = None,
        test: bool = False,
    ) -> Generator[requests.Response, Any, None]:
        """
        Use a .csv or .tsv to delete records in the database.
        """
        if test:
            endpoint = "testdelete"
        else:
            endpoint = "delete"

        if csv_path == "-":
            csv_file = sys.stdin
        else:
            csv_file = open(csv_path)
        try:
            if delimiter is None:
                reader = csv.DictReader(csv_file)
            else:
                reader = csv.DictReader(csv_file, delimiter=delimiter)

            for record in reader:
                cid = record.get("cid")
                if cid is None:
                    raise KeyError("A 'cid' column must be provided.")

                response = self.request(
                    method="delete",
                    url=self.ENDPOINTS[endpoint](self.config.domain, project, cid),
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

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
        response = self.request(
            method="get",
            url=self.ENDPOINTS["choices"](self.config.domain, project, field),
        )
        return response

    def choices(self, project: str, field: str) -> List[str]:
        """
        View choices for a field.
        """
        response = self._choices(project, field)
        response.raise_for_status()
        return response.json()["data"]["choices"]
