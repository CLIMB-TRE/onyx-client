import os
import sys
import csv
import json
import requests
import concurrent.futures
from django_query_tools.client import F
from metadb import utils, settings
from metadb.config import Config


class Client:
    def __init__(self, config):
        """
        Initialise the client with a given config.
        """
        self.config = config
        self.url = f"http://{self.config.host}:{self.config.port}"
        self.endpoints = {
            # accounts
            "register": f"{self.url}/accounts/register/",
            "login": f"{self.url}/accounts/login/",
            "logout": f"{self.url}/accounts/logout/",
            "logoutall": f"{self.url}/accounts/logoutall/",
            "site_approve": lambda x: f"{self.url}/accounts/site/approve/{x}/",
            "site_waiting": f"{self.url}/accounts/site/waiting/",
            "site_users": f"{self.url}/accounts/site/users/",
            "admin_approve": lambda x: f"{self.url}/accounts/admin/approve/{x}/",
            "admin_waiting": f"{self.url}/accounts/admin/waiting/",
            "admin_users": f"{self.url}/accounts/admin/users/",
            # data
            "create": lambda x: f"{self.url}/data/create/{x}/",
            "testcreate": lambda x: f"{self.url}/data/testcreate/{x}/",
            "get": lambda x, y: f"{self.url}/data/get/{x}/{y}/",
            "filter": lambda x: f"{self.url}/data/filter/{x}/",
            "query": lambda x: f"{self.url}/data/query/{x}/",
            "update": lambda x, y: f"{self.url}/data/update/{x}/{y}/",
            "testupdate": lambda x, y: f"{self.url}/data/testupdate/{x}/{y}/",
            "suppress": lambda x, y: f"{self.url}/data/suppress/{x}/{y}/",
            "testsuppress": lambda x, y: f"{self.url}/data/testsuppress/{x}/{y}/",
            "delete": lambda x, y: f"{self.url}/data/delete/{x}/{y}/",
            "testdelete": lambda x, y: f"{self.url}/data/testdelete/{x}/{y}/",
        }

    def request(self, method, **kwargs):
        """
        Carry out a request while handling token authorisation.
        """
        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.token}"}
        )
        method_response = method(**kwargs)

        if method_response.status_code == 401 and self.env_password:
            login_response = requests.post(
                self.endpoints["login"],
                auth=(self.username, self.get_password()),
            )

            if login_response.ok:
                self.token = login_response.json()["data"]["token"]
                self.expiry = login_response.json()["data"]["expiry"]
                self.config.write_token(self.username, self.token, self.expiry)

                return self.request(method, **kwargs)

            login_response.raise_for_status()

        return method_response

    def register(self, first_name, last_name, email, site, password):
        """
        Create a new user.
        """
        response = requests.post(
            self.endpoints["register"],
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "site": site,
            },
        )
        return response

    def continue_session(self, username=None, env_password=False):
        if username is None:
            # Attempt to use default_user if no username was provided
            if self.config.default_user is None:
                raise Exception(
                    "No username was provided and there is no default_user in the config. Either provide a username or set a default_user"
                )
            else:
                # The default_user must be in the config
                if self.config.default_user not in self.config.users:
                    raise Exception(
                        f"default_user '{self.config.default_user}' is not in the users list for the config"
                    )
                username = self.config.default_user
        else:
            # Username is case-insensitive
            username = username.lower()

            # The provided user must be in the config
            if username not in self.config.users:
                raise KeyError(
                    f"User '{username}' is not in the config. Add them using the add-user config command"
                )

        # Assign username to the client
        self.username = username

        # Assign flag indicating whether to look for user's password to the client
        self.env_password = env_password

        # Open the token file for the user and assign the current token, and its expiry, to the client
        with open(self.config.users[username]["token"]) as token_file:
            token_data = json.load(token_file)
            self.token = token_data.get("token")
            self.expiry = token_data.get("expiry")

        return username

    def get_password(self):
        if self.env_password:
            # If the password is meant to be an env var, grab it.
            # If its not there, this is unintended so an error is raised
            password_env_var = (
                settings.PASSWORD_ENV_VAR_PREFIX
                + self.username.upper()
                + settings.PASSWORD_ENV_VAR_POSTFIX
            )
            password = os.environ[password_env_var]
        else:
            # Otherwise, prompt for the password
            print("Please enter your password.")
            password = utils.get_input("password", password=True)
        return password

    def login(self, username=None, env_password=False):
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """

        # Assigns username/env_password flag to the client
        self.continue_session(username, env_password=env_password)

        # Get the password
        password = self.get_password()

        # Log in
        response = requests.post(
            self.endpoints["login"], auth=(self.username, password)
        )
        if response.ok:
            self.token = response.json()["data"]["token"]
            self.expiry = response.json()["data"]["expiry"]
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def logout(self):
        """
        Log out the user in this client.
        """
        response = self.request(
            method=requests.post,
            url=self.endpoints["logout"],
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def logoutall(self):
        """
        Log out the user in all clients.
        """
        response = self.request(
            method=requests.post,
            url=self.endpoints["logoutall"],
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def site_approve(self, username):
        """
        Site-approve another user.
        """
        response = self.request(
            method=requests.patch,
            url=self.endpoints["site_approve"](username),
        )
        return response

    @utils.session_required
    def site_list_waiting(self):
        """
        List users waiting for site approval.
        """
        response = self.request(
            method=requests.get,
            url=self.endpoints["site_waiting"],
        )
        return response

    @utils.session_required
    def site_list_users(self):
        """
        Get the current users within the site of the requesting user.
        """
        response = self.request(
            method=requests.get,
            url=self.endpoints["site_users"],
        )
        return response

    @utils.session_required
    def admin_approve(self, username):
        """
        Admin-approve another user.
        """
        response = self.request(
            method=requests.patch,
            url=self.endpoints["admin_approve"](username),
        )
        return response

    @utils.session_required
    def admin_list_waiting(self):
        """
        List users waiting for admin approval.
        """
        response = self.request(
            method=requests.get,
            url=self.endpoints["admin_waiting"],
        )
        return response

    @utils.session_required
    def admin_list_users(self):
        """
        List all users.
        """
        response = self.request(
            method=requests.get,
            url=self.endpoints["admin_users"],
        )
        return response

    @utils.session_required
    def create(self, project, fields, test=False):
        """
        Post a record to the database.
        """
        if test:
            endpoint = "testcreate"
        else:
            endpoint = "create"

        response = self.request(
            method=requests.post,
            url=self.endpoints[endpoint](project),
            json=fields,
        )
        return response

    @utils.session_required
    def csv_create(
        self, project, csv_path, delimiter=None, multithreaded=False, test=False
    ):
        """
        Post a .csv or .tsv containing records to the database.
        """
        if test:
            endpoint = "testcreate"
        else:
            endpoint = "create"

        if csv_path == "-":
            csv_file = sys.stdin
        else:
            csv_file = open(csv_path)
        try:
            if delimiter is None:
                reader = csv.DictReader(csv_file)
            else:
                reader = csv.DictReader(csv_file, delimiter=delimiter)

            record = next(reader, None)

            if record:
                response = self.request(
                    method=requests.post,
                    url=self.endpoints[endpoint](project),
                    json=record,
                )
                yield response

                if multithreaded:
                    # Bit of an experimental one
                    if not self.env_password:
                        raise Exception(
                            "To use multithreaded upload, set env_password = True on the client"
                        )

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(
                                self.request,
                                requests.post,
                                url=self.endpoints[endpoint](project),
                                json=record,
                            )
                            for record in reader
                        ]
                        for future in concurrent.futures.as_completed(futures):
                            yield future.result()

                else:
                    for record in reader:
                        response = self.request(
                            method=requests.post,
                            url=self.endpoints[endpoint](project),
                            json=record,
                        )
                        yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

    @utils.session_required
    def get(self, project, cid, scope=None):
        """
        Get a record from the database.
        """
        response = self.request(
            method=requests.get,
            url=self.endpoints["get"](project, cid),
            params={"scope": scope},
        )
        utils.raise_for_status(response)
        return response.json()["data"]["record"]

    @utils.session_required
    def filter(self, project, fields=None, scope=None):
        """
        Filter records from the database.
        """
        if fields is None:
            fields = {}

        if scope:
            fields["scope"] = scope

        _next = self.endpoints["filter"](project)

        while _next is not None:
            response = self.request(
                method=requests.get,
                url=_next,
                params=fields,
            )
            utils.raise_for_status(response)
            _next = response.json()["data"]["next"]
            fields = None

            for result in response.json()["data"]["records"]:
                yield result

    @utils.session_required
    def query(self, project, query=None, scope=None):
        """
        Get records from the database.
        """
        if query:
            if not isinstance(query, F):
                raise Exception("Query must be an F object")
            else:
                query = query.query

        fields = {"scope": scope}
        _next = self.endpoints["query"](project)

        while _next is not None:
            response = self.request(
                method=requests.post,
                url=_next,
                json=query,
                params=fields,
            )
            utils.raise_for_status(response)
            _next = response.json()["data"]["next"]
            fields = None

            for result in response.json()["data"]["records"]:
                yield result

    @utils.session_required
    def update(self, project, cid, fields, test=False):
        """
        Update a record in the database.
        """
        if test:
            endpoint = "testupdate"
        else:
            endpoint = "update"

        response = self.request(
            method=requests.patch,
            url=self.endpoints[endpoint](project, cid),
            json=fields,
        )
        return response

    @utils.session_required
    def csv_update(self, project, csv_path, delimiter=None, test=False):
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
                    raise KeyError("cid column must be provided")

                response = self.request(
                    method=requests.patch,
                    url=self.endpoints[endpoint](project, cid),
                    json=record,
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

    @utils.session_required
    def suppress(self, project, cid, test=False):
        """
        Suppress a record in the database.
        """
        if test:
            endpoint = "testsuppress"
        else:
            endpoint = "suppress"

        response = self.request(
            method=requests.delete,
            url=self.endpoints[endpoint](project, cid),
        )
        return response

    @utils.session_required
    def csv_suppress(self, project, csv_path, delimiter=None, test=False):
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
                    raise KeyError("cid column must be provided")

                response = self.request(
                    method=requests.delete,
                    url=self.endpoints[endpoint](project, cid),
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()

    @utils.session_required
    def delete(self, project, cid, test=False):
        """
        Delete a record in the database.
        """
        if test:
            endpoint = "testdelete"
        else:
            endpoint = "delete"

        response = self.request(
            method=requests.delete,
            url=self.endpoints[endpoint](project, cid),
        )
        return response

    @utils.session_required
    def csv_delete(self, project, csv_path, delimiter=None, test=False):
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
                    raise KeyError("cid column must be provided")

                response = self.request(
                    method=requests.delete,
                    url=self.endpoints[endpoint](project, cid),
                )
                yield response
        finally:
            if csv_file is not sys.stdin:
                csv_file.close()


class Session:
    def __init__(self, username=None, env_password=False, login=False, logout=False):
        self.config = Config()
        self.client = Client(self.config)
        self.username = username
        self.env_password = env_password
        self.login = login
        self.logout = logout

    def __enter__(self):
        if self.login:
            response = self.client.login(
                username=self.username,
                env_password=self.env_password,
            )
            response.raise_for_status()
        else:
            self.client.continue_session(
                username=self.username,
                env_password=self.env_password,
            )
        return self.client

    def __exit__(self, type, value, traceback):
        if self.logout:
            self.client.logout()
