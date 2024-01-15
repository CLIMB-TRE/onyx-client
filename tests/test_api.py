import io
import requests
import pytest
from unittest import TestCase, mock
from onyx import OnyxConfig, OnyxClient, exceptions, OnyxField


DOMAIN = "https://onyx.domain"
BAD_DOMAIN = "not-onyx"
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
INVALID_AUTH_DATA = {
    "status": "fail",
    "code": 401,
    "messages": {
        "detail": "Invalid username/password.",
    },
}
PROJECT = "project"
NOT_PROJECT = "not_project"
ERROR_CAUSING_PROJECT = "error_causing_project"
ADMIN_SCOPE = "admin"
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
            "climb_id": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a project. Set by Onyx.",
            },
            "sample_id": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a biological sample.",
            },
            "run_name": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a sequencing run.",
            },
            "source_type": {
                "type": "text",
                "required": True,
                "description": "Where was the sample sourced. Is it human, animal... or something else...",
            },
        },
    },
}
FIELDS_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "version": "0.1.0",
        "fields": {
            "climb_id": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a project. Set by Onyx.",
            },
            "sample_id": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a biological sample.",
            },
            "run_name": {
                "type": "text",
                "required": True,
                "description": "Unique identifier for a sequencing run.",
            },
            "source_type": {
                "type": "text",
                "required": False,
                "description": "Where was the sample sourced.",
            },
            "country": {
                "type": "bool",
                "required": False,
                "description": "Country of origin for the sample.",
                "values": [
                    "England",
                    "N. Ireland",
                    "Scotland",
                    "Wales",
                ],
            },
        },
    },
}
FIELDS_NOT_PROJECT_DATA = {
    "status": "fail",
    "code": 404,
    "messages": {
        "detail": "Project not found.",
    },
}
FIELDS_ERROR_CAUSING_PROJECT_DATA = {
    "status": "fail",
    "code": 500,
    "messages": {
        "detail": "Internal server error. Oh dear...",
    },
}
CHOICE_FIELD = "country"
CHOICES_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        "England",
        "N. Ireland",
        "Scotland",
        "Wales",
    ],
}
CLIMB_ID = "C-0123456789"
CREATE_FIELDS = {
    "sample_id": "sample-123",
    "run_name": "run-456",
}
CSV_CREATE_EMPTY_FILE = "sample_id, run_name\n"
TSV_CREATE_EMPTY_FILE = "sample_id\t run_name\n"
CSV_CREATE_SINGLE_FILE = "sample_id, run_name\nsample-123, run-456"
TSV_CREATE_SINGLE_FILE = "sample_id\t run_name\nsample-123\t run-456"
CSV_CREATE_MULTI_FILE = "sample_id, run_name\nsample-123, run-456\nsample-123, run-456"
TSV_CREATE_MULTI_FILE = (
    "sample_id\t run_name\nsample-123\t run-456\nsample-123\t run-456"
)
CSV_CREATE_SINGLE_MISSING_FILE = "sample_id\nsample-123"
TSV_CREATE_SINGLE_MISSING_FILE = "sample_id\nsample-123"
CSV_CREATE_MULTI_MISSING_FILE = "sample_id\nsample-123\nsample-123"
TSV_CREATE_MULTI_MISSING_FILE = "sample_id\nsample-123\nsample-123"
MISSING_CREATE_FIELDS = {"run_name": "run-456"}
CREATE_DATA = {
    "status": "success",
    "code": 201,
    "data": {
        "climb_id": CLIMB_ID,
    },
}
TESTCREATE_DATA = {
    "status": "success",
    "code": 201,
    "data": {
        "climb_id": None,
    },
}
GET_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
        "published_date": "2023-09-18",
        "sample_id": "sample-123",
        "run_name": "run-456",
    },
}
GET_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
        "published_date": "2023-09-18",
        "sample_id": "sample-123",
        "run_name": "run-456",
        "country": "England",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
    ],
}
SAMPLE_ID = "sample-abc"
RUN_NAME = "run-def"
FILTER_SPECIFIC_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-abc",
            "run_name": "run-def",
        },
    ],
}
INCLUDE_FIELDS = ["climb_id", "published_date"]
FILTER_SPECIFIC_INCLUDE_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
        },
    ],
}
EXCLUDE_FIELDS = ["run_name"]
FILTER_SPECIFIC_EXCLUDE_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-abc",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
        },
    ],
}
QUERY_SPECIFIC_BODY = {"&": [{"sample_id": SAMPLE_ID}, {"run_name": RUN_NAME}]}
QUERY_PAGE_1_ADMIN_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_1&scope={ADMIN_SCOPE}"
QUERY_PAGE_2_ADMIN_URL = f"{OnyxClient.ENDPOINTS['query'](DOMAIN, PROJECT)}?cursor=page_2&scope={ADMIN_SCOPE}"
QUERY_PAGE_1_ADMIN_DATA = {
    "status": "success",
    "code": 200,
    "next": QUERY_PAGE_2_ADMIN_URL,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
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
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
        {
            "climb_id": CLIMB_ID,
            "published_date": "2023-09-18",
            "sample_id": "sample-123",
            "run_name": "run-456",
            "country": "England",
        },
    ],
}
UPDATE_FIELDS = {
    "country": "England",
    "source_type": "humanoid",
}
CSV_UPDATE_EMPTY_FILE = "climb_id, country, source_type\n"
TSV_UPDATE_EMPTY_FILE = "climb_id\t country\t source_type\n"
CSV_UPDATE_SINGLE_FILE = (
    f"climb_id, country, source_type\n{CLIMB_ID}, England, humanoid"
)
TSV_UPDATE_SINGLE_FILE = (
    f"climb_id\t country\t source_type\n{CLIMB_ID}\t England\t humanoid"
)
CSV_UPDATE_MULTI_FILE = f"climb_id, country, source_type\n{CLIMB_ID}, England, humanoid\n{CLIMB_ID}, England, humanoid"
TSV_UPDATE_MULTI_FILE = f"climb_id\t country\t source_type\n{CLIMB_ID}\t England\t humanoid\n{CLIMB_ID}\t England\t humanoid"
CSV_UPDATE_SINGLE_MISSING_FILE = "country, source_type\nEngland, humanoid"
TSV_UPDATE_SINGLE_MISSING_FILE = "country\t source_type\nEngland\t humanoid"
CSV_UPDATE_MULTI_MISSING_FILE = (
    "country, source_type\nEngland, humanoid\nEngland, humanoid"
)
TSV_UPDATE_MULTI_MISSING_FILE = (
    "country\t source_type\nEngland\t humanoid\nEngland\t humanoid"
)
MISSING_UPDATE_FIELDS = {"climb_id": CLIMB_ID}
UPDATE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
    },
}
TESTUPDATE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
    },
}
CSV_DELETE_EMPTY_FILE = f"climb_id\n"
TSV_DELETE_EMPTY_FILE = f"climb_id\n"
CSV_DELETE_SINGLE_FILE = f"climb_id\n{CLIMB_ID}"
TSV_DELETE_SINGLE_FILE = f"climb_id\n{CLIMB_ID}"
CSV_DELETE_MULTI_FILE = f"climb_id\n{CLIMB_ID}\n{CLIMB_ID}"
TSV_DELETE_MULTI_FILE = f"climb_id\n{CLIMB_ID}\n{CLIMB_ID}"
DELETE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
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
                "Something terrible happened.",
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

    if not url:
        url = ""

    if not params:
        params = {}

    if not json:
        json = {}

    if url.startswith(BAD_DOMAIN):
        raise requests.ConnectionError

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
                if json == QUERY_SPECIFIC_BODY:
                    if params.get("include") == INCLUDE_FIELDS:
                        return MockResponse(FILTER_SPECIFIC_INCLUDE_DATA)
                    elif params.get("exclude") == EXCLUDE_FIELDS:
                        return MockResponse(FILTER_SPECIFIC_EXCLUDE_DATA)
                    else:
                        return MockResponse(FILTER_SPECIFIC_DATA)
                else:
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

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, NOT_PROJECT):
            return MockResponse(FIELDS_NOT_PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, ERROR_CAUSING_PROJECT):
            return MockResponse(FIELDS_ERROR_CAUSING_PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["choices"](DOMAIN, PROJECT, CHOICE_FIELD):
            return MockResponse(CHOICES_DATA)

        elif url == OnyxClient.ENDPOINTS["get"](DOMAIN, PROJECT, CLIMB_ID):
            if params.get("scope") == None:
                return MockResponse(GET_DATA)

            elif params.get("scope") == ADMIN_SCOPE:
                return MockResponse(GET_ADMIN_DATA)

        elif url == OnyxClient.ENDPOINTS["filter"](DOMAIN, PROJECT):
            if params.get("scope") == None:
                if (
                    params.get("sample_id") == SAMPLE_ID
                    and params.get("run_name") == RUN_NAME
                ):
                    if params.get("include") == INCLUDE_FIELDS:
                        return MockResponse(FILTER_SPECIFIC_INCLUDE_DATA)
                    elif params.get("exclude") == EXCLUDE_FIELDS:
                        return MockResponse(FILTER_SPECIFIC_EXCLUDE_DATA)
                    else:
                        return MockResponse(FILTER_SPECIFIC_DATA)
                else:
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
            url == OnyxClient.ENDPOINTS["update"](DOMAIN, PROJECT, CLIMB_ID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(UPDATE_DATA)

        elif (
            url == OnyxClient.ENDPOINTS["testupdate"](DOMAIN, PROJECT, CLIMB_ID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(TESTUPDATE_DATA)

        elif url == OnyxClient.ENDPOINTS["approve"](DOMAIN, OTHER_USERNAME):
            return MockResponse(APPROVE_DATA)

    elif method == "delete":
        if url == OnyxClient.ENDPOINTS["delete"](DOMAIN, PROJECT, CLIMB_ID):
            return MockResponse(DELETE_DATA)

    return MockResponse(
        {
            "status": "fail",
            "code": 400,
            "messages": {"detail": "Something terrible happened."},
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
            "messages": {"detail": "Something terrible happened."},
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
    def test_connection_error(self, mock_request):
        self.config.domain = BAD_DOMAIN
        with pytest.raises(exceptions.OnyxConnectionError):
            self.client.projects()

        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_request_error(self, mock_request):
        with pytest.raises(exceptions.OnyxRequestError):
            self.client.fields(NOT_PROJECT)

        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_server_error(self, mock_request):
        with pytest.raises(exceptions.OnyxServerError):
            self.client.fields(ERROR_CAUSING_PROJECT)

        self.assertEqual(self.config.token, TOKEN)

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
            with pytest.raises(exceptions.OnyxClientError):
                self.client.fields(empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_choices(self, mock_request):
        self.assertEqual(
            self.client.choices(PROJECT, CHOICE_FIELD), CHOICES_DATA["data"]
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.choices(empty, CHOICE_FIELD)

            with pytest.raises(exceptions.OnyxClientError):
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
            with pytest.raises(exceptions.OnyxClientError):
                self.client.create(empty, CREATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.create(empty, CREATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_get(self, mock_request):
        self.assertEqual(self.client.get(PROJECT, CLIMB_ID), GET_DATA["data"])
        self.assertEqual(
            self.client.get(PROJECT, CLIMB_ID, scope=ADMIN_SCOPE),
            GET_ADMIN_DATA["data"],
        )
        self.assertEqual(
            self.client.get(
                PROJECT, fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME}
            ),
            FILTER_SPECIFIC_DATA["data"][0],
        )
        self.assertEqual(
            self.client.get(
                PROJECT,
                fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME},
                include=INCLUDE_FIELDS,
            ),
            FILTER_SPECIFIC_INCLUDE_DATA["data"][0],
        )
        self.assertEqual(
            self.client.get(
                PROJECT,
                fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME},
                exclude=EXCLUDE_FIELDS,
            ),
            FILTER_SPECIFIC_EXCLUDE_DATA["data"][0],
        )
        self.assertEqual(self.config.token, TOKEN)

        # At least one of CLIMB_ID and fields is required
        with pytest.raises(exceptions.OnyxClientError):
            self.client.get(PROJECT)

        # More than one record returned
        with pytest.raises(exceptions.OnyxClientError):
            self.client.get(
                PROJECT, fields={"sample_id": "sample-123", "run_name": "run-456"}
            )

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(empty, CLIMB_ID)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(PROJECT, empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_filter(self, mock_request):
        self.assertEqual(
            [x for x in self.client.filter(PROJECT)],
            FILTER_PAGE_1_DATA["data"] + FILTER_PAGE_2_DATA["data"],
        )
        self.assertEqual(
            [x for x in self.client.filter(PROJECT, scope=ADMIN_SCOPE)],
            FILTER_PAGE_1_ADMIN_DATA["data"] + FILTER_PAGE_2_ADMIN_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT, fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME}
                )
            ],
            FILTER_SPECIFIC_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME},
                    include=INCLUDE_FIELDS,
                )
            ],
            FILTER_SPECIFIC_INCLUDE_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME},
                    exclude=EXCLUDE_FIELDS,
                )
            ],
            FILTER_SPECIFIC_EXCLUDE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                [x for x in self.client.filter(empty)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_query(self, mock_request):
        self.assertEqual(
            [x for x in self.client.query(PROJECT)],
            QUERY_PAGE_1_DATA["data"] + QUERY_PAGE_2_DATA["data"],
        )
        self.assertEqual(
            [x for x in self.client.query(PROJECT, scope=ADMIN_SCOPE)],
            QUERY_PAGE_1_ADMIN_DATA["data"] + QUERY_PAGE_2_ADMIN_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.query(
                    PROJECT,
                    query=OnyxField(sample_id=SAMPLE_ID) & OnyxField(run_name=RUN_NAME),
                )
            ],
            FILTER_SPECIFIC_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.query(
                    PROJECT,
                    query=OnyxField(sample_id=SAMPLE_ID) & OnyxField(run_name=RUN_NAME),
                    include=INCLUDE_FIELDS,
                )
            ],
            FILTER_SPECIFIC_INCLUDE_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.query(
                    PROJECT,
                    query=OnyxField(sample_id=SAMPLE_ID) & OnyxField(run_name=RUN_NAME),
                    exclude=EXCLUDE_FIELDS,
                )
            ],
            FILTER_SPECIFIC_EXCLUDE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                [x for x in self.client.query(empty)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_update(self, mock_request):
        self.assertEqual(
            self.client.update(PROJECT, CLIMB_ID, UPDATE_FIELDS), UPDATE_DATA["data"]
        )
        self.assertEqual(
            self.client.update(PROJECT, CLIMB_ID, UPDATE_FIELDS, test=True),
            TESTUPDATE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(empty, CLIMB_ID, UPDATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(empty, CLIMB_ID, UPDATE_FIELDS, test=True)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_delete(self, mock_request):
        self.assertEqual(self.client.delete(PROJECT, CLIMB_ID), DELETE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for empty in ["", " ", None]:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.delete(empty, CLIMB_ID)

            with pytest.raises(exceptions.OnyxClientError):
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

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(CSV_CREATE_EMPTY_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(TSV_CREATE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_create(
                PROJECT,
                io.StringIO(CSV_CREATE_MULTI_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
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

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_EMPTY_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_MULTI_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_MULTI_FILE),
                delimiter="\t",
            )

        # Testing lack of CLIMB_ID for update
        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_SINGLE_MISSING_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(CSV_UPDATE_MULTI_MISSING_FILE),
                multiline=True,
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_update(
                PROJECT,
                io.StringIO(TSV_UPDATE_SINGLE_MISSING_FILE),
                delimiter="\t",
            )

        with pytest.raises(exceptions.OnyxClientError):
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

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_EMPTY_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(TSV_DELETE_EMPTY_FILE),
                delimiter="\t",
            )

        with pytest.raises(exceptions.OnyxClientError):
            self.client.csv_delete(
                PROJECT,
                io.StringIO(CSV_DELETE_MULTI_FILE),
            )

        with pytest.raises(exceptions.OnyxClientError):
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
            with pytest.raises(exceptions.OnyxClientError):
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
            with pytest.raises(exceptions.OnyxClientError):
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
