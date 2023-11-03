import io
import requests
import pytest
from unittest import TestCase, mock
from onyx import OnyxConfig, OnyxClient
from onyx.exceptions import OnyxClientError


DOMAIN = "https://onyx.domain"
TOKEN = "token"
EXPIRY = "expiry"
FIRST_NAME = "first_name"
LAST_NAME = "last_name"
USERNAME = "username"
PASSWORD = "password"
EMAIL = "email"
SITE = "site"
OTHER_USERNAME = "other_username"
OTHER_EMAIL = "other_email"
PROJECT = "project"
ADMIN_SCOPE = "admin"
CID = "C-0123456789"
CHOICE_FIELD = "choice_field"
INVALID_AUTH_DATA = {
    "status": "fail",
    "code": 401,
    "messages": {
        "detail": "Invalid username/password.",
    },
}
PROJECT_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "project": PROJECT,
            "action": "view",
            "scope": "base",
        }
    ],
}
FIELDS_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "version": "0.1.0",
        "fields": {
            "cid": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a project. Set by Onyx.",
            }
        },
    },
}
FIELDS_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "version": "0.1.0",
        "fields": {
            "cid": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a project. Set by Onyx.",
            },
            "suppressed": {
                "type": "bool",
                "required": True,
                "description": "True/False for whether a record is suppressed. Set by Onyx.",
            },
        },
    },
}
CHOICES_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        "choice_1",
        "choice_2",
        "choice_3",
    ],
}
CREATE_FIELDS = {
    "field_1": "value_1",
    "field_2": "value_2",
}
CSV_CREATE_EMPTY_FILE = "field_1,field_2\n"
TSV_CREATE_EMPTY_FILE = "field_1\tfield_2\n"
CSV_CREATE_SINGLE_FILE = "field_1,field_2\nvalue_1,value_2"
TSV_CREATE_SINGLE_FILE = "field_1\tfield_2\nvalue_1\tvalue_2"
CSV_CREATE_MULTI_FILE = "field_1,field_2\nvalue_1,value_2\nvalue_1,value_2"
TSV_CREATE_MULTI_FILE = "field_1\tfield_2\nvalue_1\tvalue_2\nvalue_1\tvalue_2"
CSV_CREATE_SINGLE_MISSING_FILE = "field_1\nvalue_1"
TSV_CREATE_SINGLE_MISSING_FILE = "field_1\nvalue_1"
CSV_CREATE_MULTI_MISSING_FILE = "field_1\nvalue_1\nvalue_1"
TSV_CREATE_MULTI_MISSING_FILE = "field_1\nvalue_1\nvalue_1"
MISSING_CREATE_FIELDS = {"field_2": "value_2"}
CREATE_DATA = {
    "status": "success",
    "code": 201,
    "data": {
        "cid": CID,
    },
}
TESTCREATE_DATA = {
    "status": "success",
    "code": 201,
    "data": {
        "cid": None,
    },
}
GET_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "field_1": "value_1",
        "field_2": "value_2",
    },
}
GET_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "field_1": "value_1",
        "field_2": "value_2",
        "field_3": "value_3",
    },
}
FILTER_PAGE_1_URL = f"{OnyxClient.ENDPOINTS['filter'](DOMAIN, PROJECT)}?cursor=page_1"
FILTER_PAGE_2_URL = f"{OnyxClient.ENDPOINTS['filter'](DOMAIN, PROJECT)}?cursor=page_2"
FILTER_PAGE_1_DATA = {
    "status": "success",
    "code": 200,
    "next": FILTER_PAGE_2_URL,
    "previous": None,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
    ],
}
FILTER_PAGE_2_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": FILTER_PAGE_1_URL,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
    ],
}
FILTER_PAGE_1_ADMIN_URL = f"{OnyxClient.ENDPOINTS['filter'](DOMAIN, PROJECT)}?cursor=page_1&scope={ADMIN_SCOPE}"
FILTER_PAGE_2_ADMIN_URL = f"{OnyxClient.ENDPOINTS['filter'](DOMAIN, PROJECT)}?cursor=page_2&scope={ADMIN_SCOPE}"
FILTER_PAGE_1_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "next": FILTER_PAGE_2_ADMIN_URL,
    "previous": None,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
    ],
}
FILTER_PAGE_2_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": FILTER_PAGE_1_ADMIN_URL,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
    ],
}
QUERY_PAGE_1_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_1"
QUERY_PAGE_2_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_2"
QUERY_PAGE_1_DATA = {
    "status": "success",
    "code": 200,
    "next": QUERY_PAGE_2_URL,
    "previous": None,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
    ],
}
QUERY_PAGE_2_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": QUERY_PAGE_1_URL,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
        },
    ],
}
QUERY_PAGE_1_ADMIN_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_1&scope={ADMIN_SCOPE}"
QUERY_PAGE_2_ADMIN_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_2&scope={ADMIN_SCOPE}"
QUERY_PAGE_1_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "next": QUERY_PAGE_2_ADMIN_URL,
    "previous": None,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
    ],
}
QUERY_PAGE_2_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": QUERY_PAGE_1_ADMIN_URL,
    "data": [
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
        {
            "field_1": "value_1",
            "field_2": "value_2",
            "field_3": "value_3",
        },
    ],
}
UPDATE_FIELDS = {
    "field_3": "value_3",
    "field_4": "value_4",
}
CSV_UPDATE_EMPTY_FILE = "cid,field_3,field_4\n"
TSV_UPDATE_EMPTY_FILE = "cid\tfield_3\tfield_4\n"
CSV_UPDATE_SINGLE_FILE = f"cid,field_3,field_4\n{CID},value_3,value_4"
TSV_UPDATE_SINGLE_FILE = f"cid\tfield_3\tfield_4\n{CID}\tvalue_3\tvalue_4"
CSV_UPDATE_MULTI_FILE = (
    f"cid,field_3,field_4\n{CID},value_3,value_4\n{CID},value_3,value_4"
)
TSV_UPDATE_MULTI_FILE = (
    f"cid\tfield_3\tfield_4\n{CID}\tvalue_3\tvalue_4\n{CID}\tvalue_3\tvalue_4"
)
CSV_UPDATE_SINGLE_MISSING_FILE = "field_3,field_4\nvalue_3,value_4"
TSV_UPDATE_SINGLE_MISSING_FILE = "field_3\tfield_4\nvalue_3\tvalue_4"
CSV_UPDATE_MULTI_MISSING_FILE = "field_3,field_4\nvalue_3,value_4\nvalue_3,value_4"
TSV_UPDATE_MULTI_MISSING_FILE = "field_3\tfield_4\nvalue_3\tvalue_4\nvalue_3\tvalue_4"
MISSING_UPDATE_FIELDS = {"cid": CID}
UPDATE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "cid": CID,
    },
}
TESTUPDATE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "cid": CID,
    },
}
CSV_DELETE_EMPTY_FILE = f"cid\n"
TSV_DELETE_EMPTY_FILE = f"cid\n"
CSV_DELETE_SINGLE_FILE = f"cid\n{CID}"
TSV_DELETE_SINGLE_FILE = f"cid\n{CID}"
CSV_DELETE_MULTI_FILE = f"cid\n{CID}\n{CID}"
TSV_DELETE_MULTI_FILE = f"cid\n{CID}\n{CID}"
DELETE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "cid": CID,
    },
}
REGISTER_FIELDS = {
    "first_name": FIRST_NAME,
    "last_name": LAST_NAME,
    "email": EMAIL,
    "password": PASSWORD,
    "site": SITE,
}
REGISTER_DATA = {
    "status": "success",
    "code": 201,
    "data": {
        "username": USERNAME,
        "site": SITE,
        "email": EMAIL,
        "first_name": FIRST_NAME,
        "last_name": LAST_NAME,
    },
}
LOGIN_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "token": TOKEN,
        "expiry": EXPIRY,
    },
}
LOGOUT_DATA = {
    "status": "success",
    "code": 204,
    "data": None,
}
LOGOUTALL_DATA = {
    "status": "success",
    "code": 204,
    "data": None,
}
PROFILE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "username": USERNAME,
        "email": EMAIL,
        "site": SITE,
    },
}
WAITING_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "username": OTHER_USERNAME,
            "email": OTHER_EMAIL,
            "site": SITE,
        }
    ],
}
SITE_USERS_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "username": USERNAME,
            "email": EMAIL,
            "site": SITE,
        }
    ],
}
ALL_USERS_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "username": USERNAME,
            "email": EMAIL,
            "site": SITE,
        },
        {
            "username": OTHER_USERNAME,
            "email": OTHER_EMAIL,
            "site": SITE,
        },
    ],
}
APPROVE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "username": OTHER_USERNAME,
        "is_approved": True,
    },
}


class MockResponse:
    def __init__(self, data):
        self.data = data
        self.status_code = data["code"]
        if self.status_code < 400:
            self.ok = True
        else:
            self.ok = False

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(
                "Something bad happened.",
                response=self,  #  type: ignore
            )


def mock_request(
    method=None,
    headers=None,
    auth=None,
    url=None,
    params=None,
    json=None,
):
    if not headers:
        headers = {}

    if not params:
        params = {}

    if not json:
        json = {}

    if method == "post" and url == OnyxClient.ENDPOINTS["login"](DOMAIN):
        if auth == (USERNAME, PASSWORD):
            return MockResponse(LOGIN_DATA)
        else:
            return MockResponse(INVALID_AUTH_DATA)

    if headers.get("Authorization") != f"Token {TOKEN}":
        return MockResponse(INVALID_AUTH_DATA)

    if method == "post":
        if (
            url == OnyxClient.ENDPOINTS["create"](DOMAIN, PROJECT)
            and json == CREATE_FIELDS
        ):
            return MockResponse(CREATE_DATA)

        elif (
            url == OnyxClient.ENDPOINTS["testcreate"](DOMAIN, PROJECT)
            and json == CREATE_FIELDS
        ):
            return MockResponse(TESTCREATE_DATA)

        elif url == OnyxClient.ENDPOINTS["query"](DOMAIN, PROJECT):
            if params.get("scope") == None:
                return MockResponse(QUERY_PAGE_1_DATA)

            elif params.get("scope") == ADMIN_SCOPE:
                return MockResponse(QUERY_PAGE_1_ADMIN_DATA)

        elif url == QUERY_PAGE_2_URL:
            return MockResponse(QUERY_PAGE_2_DATA)

        elif url == QUERY_PAGE_2_ADMIN_URL:
            return MockResponse(QUERY_PAGE_2_ADMIN_DATA)

        elif url == OnyxClient.ENDPOINTS["logout"](DOMAIN):
            return MockResponse(LOGOUT_DATA)

        elif url == OnyxClient.ENDPOINTS["logoutall"](DOMAIN):
            return MockResponse(LOGOUTALL_DATA)

    elif method == "get":
        if url == OnyxClient.ENDPOINTS["projects"](DOMAIN):
            return MockResponse(PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, PROJECT):
            if params.get("scope") == None:
                return MockResponse(FIELDS_DATA)

            elif params.get("scope") == ADMIN_SCOPE:
                return MockResponse(FIELDS_ADMIN_DATA)

        elif url == OnyxClient.ENDPOINTS["choices"](DOMAIN, PROJECT, CHOICE_FIELD):
            return MockResponse(CHOICES_DATA)

        elif url == OnyxClient.ENDPOINTS["get"](DOMAIN, PROJECT, CID):
            if params.get("scope") == None:
                return MockResponse(GET_DATA)

            elif params.get("scope") == ADMIN_SCOPE:
                return MockResponse(GET_ADMIN_DATA)

        elif url == OnyxClient.ENDPOINTS["filter"](DOMAIN, PROJECT):
            if params.get("scope") == None:
                return MockResponse(FILTER_PAGE_1_DATA)

            elif params.get("scope") == ADMIN_SCOPE:
                return MockResponse(FILTER_PAGE_1_ADMIN_DATA)

        elif url == FILTER_PAGE_2_URL:
            return MockResponse(FILTER_PAGE_2_DATA)

        elif url == FILTER_PAGE_2_ADMIN_URL:
            return MockResponse(FILTER_PAGE_2_ADMIN_DATA)

        elif url == OnyxClient.ENDPOINTS["profile"](DOMAIN):
            return MockResponse(PROFILE_DATA)

        elif url == OnyxClient.ENDPOINTS["waiting"](DOMAIN):
            return MockResponse(WAITING_DATA)

        elif url == OnyxClient.ENDPOINTS["siteusers"](DOMAIN):
            return MockResponse(SITE_USERS_DATA)

        elif url == OnyxClient.ENDPOINTS["allusers"](DOMAIN):
            return MockResponse(ALL_USERS_DATA)

    elif method == "patch":
        if (
            url == OnyxClient.ENDPOINTS["update"](DOMAIN, PROJECT, CID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(UPDATE_DATA)

        elif (
            url == OnyxClient.ENDPOINTS["testupdate"](DOMAIN, PROJECT, CID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(TESTUPDATE_DATA)

        elif url == OnyxClient.ENDPOINTS["approve"](DOMAIN, OTHER_USERNAME):
            return MockResponse(APPROVE_DATA)

    elif method == "delete":
        if url == OnyxClient.ENDPOINTS["delete"](DOMAIN, PROJECT, CID):
            return MockResponse(DELETE_DATA)

    return MockResponse(
        {
            "status": "fail",
            "code": 400,
            "messages": {"detail": "Something bad happened."},
        },
    )


def mock_register_post(url=None, json=None):
    if not json:
        json = {}

    if url == OnyxClient.ENDPOINTS["register"](DOMAIN) and all(
        json.get(field) == value for field, value in REGISTER_FIELDS.items()
    ):
        return MockResponse(REGISTER_DATA)

    return MockResponse(
        {
            "status": "fail",
            "code": 400,
            "messages": {"detail": "Something bad happened."},
        },
    )


class OnyxClientTestCase(TestCase):
    def setUp(self) -> None:
        self.config = OnyxConfig(
            domain=DOMAIN,
            username=USERNAME,
            password=PASSWORD,
        )
        self.client = OnyxClient(self.config)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_projects(self, mock_request):
        self.assertEqual(self.client.projects(), PROJECT_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_fields(self, mock_request):
        self.assertEqual(self.client.fields(PROJECT), FIELDS_DATA["data"])
        self.assertEqual(
            self.client.fields(PROJECT, scope=ADMIN_SCOPE), FIELDS_ADMIN_DATA["data"]
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.fields(empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_choices(self, mock_request):
        self.assertEqual(
            self.client.choices(PROJECT, CHOICE_FIELD), CHOICES_DATA["data"]
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.choices(empty, CHOICE_FIELD)

            with pytest.raises(OnyxClientError):
                self.client.choices(PROJECT, empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_create(self, mock_request):
        self.assertEqual(
            self.client.create(PROJECT, CREATE_FIELDS), CREATE_DATA["data"]
        )
        self.assertEqual(
            self.client.create(PROJECT, CREATE_FIELDS, test=True),
            TESTCREATE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.create(empty, CREATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.create(empty, CREATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_get(self, mock_request):
        # TODO: Test fields, include, exclude
        self.assertEqual(self.client.get(PROJECT, CID), GET_DATA["data"])
        self.assertEqual(
            self.client.get(PROJECT, CID, scope=ADMIN_SCOPE), GET_ADMIN_DATA["data"]
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.get(empty, CID)

            with pytest.raises(OnyxClientError):
                self.client.get(PROJECT, empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_filter(self, mock_request):
        # TODO: Test fields, include, exclude
        self.assertEqual(
            [x for x in self.client.filter(PROJECT)],
            FILTER_PAGE_1_DATA["data"] + FILTER_PAGE_2_DATA["data"],
        )
        self.assertEqual(
            [x for x in self.client.filter(PROJECT, scope=ADMIN_SCOPE)],
            FILTER_PAGE_1_ADMIN_DATA["data"] + FILTER_PAGE_2_ADMIN_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                [x for x in self.client.filter(empty)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_query(self, mock_request):
        # TODO: Test query, include, exclude
        self.assertEqual(
            [x for x in self.client.query(PROJECT)],
            QUERY_PAGE_1_DATA["data"] + QUERY_PAGE_2_DATA["data"],
        )
        self.assertEqual(
            [x for x in self.client.query(PROJECT, scope=ADMIN_SCOPE)],
            QUERY_PAGE_1_ADMIN_DATA["data"] + QUERY_PAGE_2_ADMIN_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                [x for x in self.client.query(empty)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_update(self, mock_request):
        self.assertEqual(
            self.client.update(PROJECT, CID, UPDATE_FIELDS), UPDATE_DATA["data"]
        )
        self.assertEqual(
            self.client.update(PROJECT, CID, UPDATE_FIELDS, test=True),
            TESTUPDATE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.update(empty, CID, UPDATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.update(empty, CID, UPDATE_FIELDS, test=True)

            with pytest.raises(OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_delete(self, mock_request):
        self.assertEqual(self.client.delete(PROJECT, CID), DELETE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.delete(empty, CID)

            with pytest.raises(OnyxClientError):
                self.client.delete(PROJECT, empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_csv_create(self, mock_request):
        for data, test in [
            (CREATE_DATA["data"], False),
            (TESTCREATE_DATA["data"], True),
        ]:
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(CSV_CREATE_SINGLE_FILE),
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(TSV_CREATE_SINGLE_FILE),
                    delimiter="\t",
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(CSV_CREATE_MULTI_FILE),
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(TSV_CREATE_MULTI_FILE),
                    delimiter="\t",
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(CSV_CREATE_SINGLE_MISSING_FILE),
                    fields=MISSING_CREATE_FIELDS,
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(TSV_CREATE_SINGLE_MISSING_FILE),
                    fields=MISSING_CREATE_FIELDS,
                    delimiter="\t",
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(CSV_CREATE_MULTI_MISSING_FILE),
                    fields=MISSING_CREATE_FIELDS,
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_create(
                    PROJECT,
                    io.StringIO(TSV_CREATE_MULTI_MISSING_FILE),
                    fields=MISSING_CREATE_FIELDS,
                    delimiter="\t",
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
        self.assertEqual(self.config.token, TOKEN)

        with pytest.raises(OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(CSV_CREATE_EMPTY_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(TSV_CREATE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(CSV_CREATE_MULTI_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(TSV_CREATE_MULTI_FILE),
                delimiter="\t",
            )

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_csv_update(self, mock_request):
        for data, test in [
            (UPDATE_DATA["data"], False),
            (TESTUPDATE_DATA["data"], True),
        ]:
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(CSV_UPDATE_SINGLE_FILE),
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(TSV_UPDATE_SINGLE_FILE),
                    delimiter="\t",
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(CSV_UPDATE_MULTI_FILE),
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(TSV_UPDATE_MULTI_FILE),
                    delimiter="\t",
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(CSV_UPDATE_SINGLE_MISSING_FILE),
                    fields=MISSING_UPDATE_FIELDS,
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(TSV_UPDATE_SINGLE_MISSING_FILE),
                    fields=MISSING_UPDATE_FIELDS,
                    delimiter="\t",
                    test=test,
                ),
                data,
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(CSV_UPDATE_MULTI_MISSING_FILE),
                    fields=MISSING_UPDATE_FIELDS,
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
            self.assertEqual(
                self.client.csv_update(
                    PROJECT,
                    io.StringIO(TSV_UPDATE_MULTI_MISSING_FILE),
                    fields=MISSING_UPDATE_FIELDS,
                    delimiter="\t",
                    multiline=True,
                    test=test,
                ),
                [data, data],
            )
        self.assertEqual(self.config.token, TOKEN)

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_EMPTY_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_MULTI_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_MULTI_FILE),
                delimiter="\t",
            )

        # Testing lack of CID for update
        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_SINGLE_MISSING_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_MULTI_MISSING_FILE),
                multiline=True,
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_SINGLE_MISSING_FILE),
                delimiter="\t",
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_MULTI_MISSING_FILE),
                delimiter="\t",
                multiline=True,
            )

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_csv_delete(self, mock_request):
        self.assertEqual(
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_SINGLE_FILE),
            ),
            DELETE_DATA["data"],
        )
        self.assertEqual(
            self.client.csv_delete(
                PROJECT,
                io.StringIO(TSV_DELETE_SINGLE_FILE),
                delimiter="\t",
            ),
            DELETE_DATA["data"],
        )
        self.assertEqual(
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_MULTI_FILE),
                multiline=True,
            ),
            [DELETE_DATA["data"], DELETE_DATA["data"]],
        )
        self.assertEqual(
            self.client.csv_delete(
                PROJECT,
                io.StringIO(TSV_DELETE_MULTI_FILE),
                delimiter="\t",
                multiline=True,
            ),
            [DELETE_DATA["data"], DELETE_DATA["data"]],
        )
        self.assertEqual(self.config.token, TOKEN)

        with pytest.raises(OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_EMPTY_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(TSV_DELETE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_MULTI_FILE),
            )

        with pytest.raises(OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(TSV_DELETE_MULTI_FILE),
                delimiter="\t",
            )

    @mock.patch("requests.post", side_effect=mock_register_post)
    def test_register(self, mock_request):
        self.assertEqual(
            OnyxClient.register(
                domain=DOMAIN,
                first_name=FIRST_NAME,
                last_name=LAST_NAME,
                email=EMAIL,
                site=SITE,
                password=PASSWORD,
            ),
            REGISTER_DATA["data"],
        )

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                OnyxClient.register(
                    domain=empty,
                    first_name=FIRST_NAME,
                    last_name=LAST_NAME,
                    email=EMAIL,
                    site=SITE,
                    password=PASSWORD,
                )

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_login(self, mock_request):
        self.assertEqual(self.client.login(), LOGIN_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logout(self, mock_request):
        self.assertEqual(self.client.logout(), LOGOUT_DATA["data"])
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logoutall(self, mock_request):
        self.assertEqual(self.client.logoutall(), LOGOUTALL_DATA["data"])
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_profile(self, mock_request):
        self.assertEqual(self.client.profile(), PROFILE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_approve(self, mock_request):
        self.assertEqual(self.client.approve(OTHER_USERNAME), APPROVE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.approve(empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_waiting(self, mock_request):
        self.assertEqual(self.client.waiting(), WAITING_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_site_users(self, mock_request):
        self.assertEqual(self.client.site_users(), SITE_USERS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_all_users(self, mock_request):
        self.assertEqual(self.client.all_users(), ALL_USERS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)
