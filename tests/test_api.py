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
OTHER_SITE = "other_site"
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
TYPES_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "type": "text",
            "description": "A text field.",
            "lookups": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
            ],
        },
        {
            "type": "choice",
            "description": "A choice field.",
            "lookups": [
                "exact",
                "iexact",
            ],
        },
    ],
}
LOOKUPS_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "lookup": "exact",
            "description": "Exact match.",
            "types": [
                "text",
                "choice",
            ],
        },
        {
            "lookup": "iexact",
            "description": "Case-insensitive exact match.",
            "types": [
                "text",
                "choice",
            ],
        },
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
        {
            "eng": {
                "description": "England",
                "is_active": True,
            },
            "ni": {
                "description": "N. Ireland",
                "is_active": True,
            },
            "scot": {
                "description": "Scotland",
                "is_active": True,
            },
            "wales": {
                "description": "Wales",
                "is_active": True,
            },
        }
    ],
}
CLIMB_ID = "C-0123456789"
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
PUBLISHED_DATE_RANGE = ["2023-01-01", "2024-01-01"]
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
UNKNOWN_FIELD = "haha"
NONE_FIELD = "field-that-has-none-values"
FILTER_NONE_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            NONE_FIELD: None,
        }
    ],
}
FILTER_NONE_IN_DATA = {
    "status": "success",
    "code": 200,
    "next": None,
    "previous": None,
    "data": [
        {
            "climb_id": CLIMB_ID,
            NONE_FIELD: None,
        },
        {
            "climb_id": CLIMB_ID,
            NONE_FIELD: "not-none",
        },
    ],
}
FILTER_UNKNOWN_FIELD_DATA = {
    "status": "fail",
    "code": 400,
    "messages": {UNKNOWN_FIELD: ["This field is unknown."]},
}
FILTER_ERROR_CAUSING_PROJECT_DATA = {
    "status": "fail",
    "code": 500,
    "messages": {
        "detail": "Internal server error. Deary me...",
    },
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
HISTORY_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "climb_id": CLIMB_ID,
        "history": [
            {
                "username": USERNAME,
                "timestamp": "2024-01-01T12:00:00Z",
                "action": "add",
            },
            {
                "username": USERNAME,
                "timestamp": "2024-01-01T12:00:01Z",
                "action": "change",
                "changes": [],
            },
        ],
    },
}
IDENTIFY_FIELD = "sample_id"
IDENTIFY_VALUE = "sample-123"
IDENTIFY_FIELDS = {"value": IDENTIFY_VALUE}
IDENTIFY_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "project": PROJECT,
        "site": SITE,
        "field": IDENTIFY_FIELD,
        "value": IDENTIFY_VALUE,
        "identifier": "S-1234567890",
    },
}
IDENTIFY_OTHER_SITE_FIELDS = {"value": IDENTIFY_VALUE, "site": OTHER_SITE}
IDENTIFY_OTHER_SITE_DATA = {
    "status": "success",
    "code": 200,
    "data": {
        "project": PROJECT,
        "site": OTHER_SITE,
        "field": IDENTIFY_FIELD,
        "value": IDENTIFY_VALUE,
        "identifier": "S-0987654321",
    },
}
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
ACTIVITY_DATA = {
    "status": "success",
    "code": 200,
    "data": [
        {
            "date": "2023-01-01T00:00:00.000000Z",
            "address": "127.0.0.1",
            "endpoint": "/projects/project/",
            "method": "POST",
            "status": 400,
            "exec_time": 29,
            "error_messages": 'b\'{"status":"fail","code":400,"messages":{"site":["Select a valid choice."]}}\'',
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
    ],
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
INVALID_DOMAIN_ARGUMENTS = ["", " ", None]
INVALID_ARGUMENTS = INVALID_DOMAIN_ARGUMENTS + ["/", "?", "/?"]
PROJECT_ENDPOINT_CLASHES = ["types", "lookups"]
CLIMB_ID_ENDPOINT_CLASHES = [
    "test",
    "query",
    "fields",
    "choices",
    "history",
    "identify",
]


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
            if json == QUERY_SPECIFIC_BODY:
                if params.get("include") == INCLUDE_FIELDS:
                    return MockResponse(FILTER_SPECIFIC_INCLUDE_DATA)
                elif params.get("exclude") == EXCLUDE_FIELDS:
                    return MockResponse(FILTER_SPECIFIC_EXCLUDE_DATA)
                else:
                    return MockResponse(FILTER_SPECIFIC_DATA)
            else:
                return MockResponse(QUERY_PAGE_1_DATA)

        elif url == QUERY_PAGE_2_URL:
            return MockResponse(QUERY_PAGE_2_DATA)

        elif url == OnyxClient.ENDPOINTS["logout"](DOMAIN):
            return MockResponse(LOGOUT_DATA)

        elif url == OnyxClient.ENDPOINTS["logoutall"](DOMAIN):
            return MockResponse(LOGOUTALL_DATA)

        elif url == OnyxClient.ENDPOINTS["identify"](DOMAIN, PROJECT, IDENTIFY_FIELD):
            if json == IDENTIFY_FIELDS:
                return MockResponse(IDENTIFY_DATA)

            elif json == IDENTIFY_OTHER_SITE_FIELDS:
                return MockResponse(IDENTIFY_OTHER_SITE_DATA)

    elif method == "get":
        if url == OnyxClient.ENDPOINTS["projects"](DOMAIN):
            return MockResponse(PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["types"](DOMAIN):
            return MockResponse(TYPES_DATA)

        elif url == OnyxClient.ENDPOINTS["lookups"](DOMAIN):
            return MockResponse(LOOKUPS_DATA)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, PROJECT):
            return MockResponse(FIELDS_DATA)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, NOT_PROJECT):
            return MockResponse(FIELDS_NOT_PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, ERROR_CAUSING_PROJECT):
            return MockResponse(FIELDS_ERROR_CAUSING_PROJECT_DATA)

        elif url == OnyxClient.ENDPOINTS["choices"](DOMAIN, PROJECT, CHOICE_FIELD):
            return MockResponse(CHOICES_DATA)

        elif url == OnyxClient.ENDPOINTS["get"](DOMAIN, PROJECT, CLIMB_ID):
            return MockResponse(GET_DATA)

        elif url == OnyxClient.ENDPOINTS["filter"](DOMAIN, PROJECT):
            if params.get(UNKNOWN_FIELD):
                return MockResponse(FILTER_UNKNOWN_FIELD_DATA)
            elif params.get(NONE_FIELD) == "":
                return MockResponse(FILTER_NONE_DATA)
            elif "" in params.get(f"{NONE_FIELD}__in", []):
                return MockResponse(FILTER_NONE_IN_DATA)
            elif (
                params.get("sample_id") == SAMPLE_ID
                and params.get("run_name") == RUN_NAME
                and params.get("published_date__range")
                == ",".join(PUBLISHED_DATE_RANGE)
            ):
                if params.get("include") == INCLUDE_FIELDS:
                    return MockResponse(FILTER_SPECIFIC_INCLUDE_DATA)
                elif params.get("exclude") == EXCLUDE_FIELDS:
                    return MockResponse(FILTER_SPECIFIC_EXCLUDE_DATA)
                else:
                    return MockResponse(FILTER_SPECIFIC_DATA)
            else:
                return MockResponse(FILTER_PAGE_1_DATA)

        elif url == OnyxClient.ENDPOINTS["filter"](DOMAIN, ERROR_CAUSING_PROJECT):
            return MockResponse(FILTER_ERROR_CAUSING_PROJECT_DATA)

        elif url == FILTER_PAGE_2_URL:
            return MockResponse(FILTER_PAGE_2_DATA)

        elif url == OnyxClient.ENDPOINTS["history"](DOMAIN, PROJECT, CLIMB_ID):
            return MockResponse(HISTORY_DATA)

        elif url == OnyxClient.ENDPOINTS["profile"](DOMAIN):
            return MockResponse(PROFILE_DATA)

        elif url == OnyxClient.ENDPOINTS["activity"](DOMAIN):
            return MockResponse(ACTIVITY_DATA)

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
    def test_context_manager(self, mock_request):
        """
        Test that the OnyxClient can be used as a context manager.
        """

        with OnyxClient(self.config) as client:
            self.assertIsInstance(client._session, requests.Session)
            self.assertEqual(
                client._request_handler, client._session.request  #  type: ignore
            )

        self.assertEqual(client._request_handler, requests.request)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_connection_error(self, mock_request):
        """
        Test that the OnyxClient raises an OnyxConnectionError when a connection error occurs.
        """

        self.config.domain = BAD_DOMAIN

        # Non-generator connection error
        with pytest.raises(exceptions.OnyxConnectionError):
            self.client.projects()

        # Generator connection error
        with pytest.raises(exceptions.OnyxConnectionError):
            [x for x in self.client.filter(PROJECT)]

        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_request_error(self, mock_request):
        """
        Test that the OnyxClient raises an OnyxRequestError when a request error occurs.
        """

        # Non-generator request error
        with pytest.raises(exceptions.OnyxRequestError) as e:
            self.client.fields(NOT_PROJECT)
        self.assertEqual(e.value.response.json(), FIELDS_NOT_PROJECT_DATA)

        # Generator request error
        with pytest.raises(exceptions.OnyxRequestError) as e:
            [x for x in self.client.filter(PROJECT, fields={UNKNOWN_FIELD: "haha"})]
        self.assertEqual(e.value.response.json(), FILTER_UNKNOWN_FIELD_DATA)

        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_server_error(self, mock_request):
        """
        Test that the OnyxClient raises an OnyxServerError when a server error occurs.
        """

        # Non-generator server error
        with pytest.raises(exceptions.OnyxServerError) as e:
            self.client.fields(ERROR_CAUSING_PROJECT)
        self.assertEqual(e.value.response.json(), FIELDS_ERROR_CAUSING_PROJECT_DATA)

        # Generator server error
        with pytest.raises(exceptions.OnyxServerError) as e:
            [x for x in self.client.filter(ERROR_CAUSING_PROJECT)]
        self.assertEqual(e.value.response.json(), FILTER_ERROR_CAUSING_PROJECT_DATA)

        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_projects(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of projects.
        """

        self.assertEqual(self.client.projects(), PROJECT_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_types(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of field types.
        """

        self.assertEqual(self.client.types(), TYPES_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_lookups(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of lookups.
        """

        self.assertEqual(self.client.lookups(), LOOKUPS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_fields(self, mock_request):
        """
        Test that the OnyxClient can retrieve the field specification of a project.
        """

        self.assertEqual(self.client.fields(PROJECT), FIELDS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.fields(invalid)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_choices(self, mock_request):
        """
        Test that the OnyxClient can retrieve the choices of a choice field.
        """

        self.assertEqual(
            self.client.choices(PROJECT, CHOICE_FIELD), CHOICES_DATA["data"]
        )
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.choices(invalid, CHOICE_FIELD)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.choices(PROJECT, invalid)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_get(self, mock_request):
        """
        Test that the OnyxClient can retrieve a record from a project.
        """

        self.assertEqual(self.client.get(PROJECT, CLIMB_ID), GET_DATA["data"])
        self.assertEqual(
            self.client.get(
                PROJECT,
                fields={
                    "sample_id": SAMPLE_ID,
                    "run_name": RUN_NAME,
                    "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                },
            ),
            FILTER_SPECIFIC_DATA["data"][0],
        )
        self.assertEqual(
            self.client.get(
                PROJECT,
                fields={
                    "sample_id": SAMPLE_ID,
                    "run_name": RUN_NAME,
                    "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                },
                include=INCLUDE_FIELDS,
            ),
            FILTER_SPECIFIC_INCLUDE_DATA["data"][0],
        )
        self.assertEqual(
            self.client.get(
                PROJECT,
                fields={
                    "sample_id": SAMPLE_ID,
                    "run_name": RUN_NAME,
                    "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                },
                exclude=EXCLUDE_FIELDS,
            ),
            FILTER_SPECIFIC_EXCLUDE_DATA["data"][0],
        )
        self.assertEqual(self.config.token, TOKEN)

        # Cannot provide both CLIMB_ID and fields
        with pytest.raises(exceptions.OnyxClientError):
            self.client.get(
                PROJECT,
                CLIMB_ID,
                fields={"sample_id": SAMPLE_ID, "run_name": RUN_NAME},
            )

        # At least one of CLIMB_ID and fields is required
        with pytest.raises(exceptions.OnyxClientError):
            self.client.get(PROJECT)

        # More than one record returned
        with pytest.raises(exceptions.OnyxClientError):
            self.client.get(
                PROJECT, fields={"sample_id": "sample-123", "run_name": "run-456"}
            )

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(invalid, CLIMB_ID)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(PROJECT, invalid)

        for clash in PROJECT_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(clash, CLIMB_ID)

        for clash in CLIMB_ID_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(PROJECT, clash)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_filter(self, mock_request):
        """
        Test that the OnyxClient can filter records from a project.
        """

        self.assertEqual(
            [x for x in self.client.filter(PROJECT)],
            FILTER_PAGE_1_DATA["data"] + FILTER_PAGE_2_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    fields={
                        "sample_id": SAMPLE_ID,
                        "run_name": RUN_NAME,
                        "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                    },
                )
            ],
            FILTER_SPECIFIC_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    sample_id=SAMPLE_ID,
                    run_name=RUN_NAME,
                    published_date__range=PUBLISHED_DATE_RANGE,
                )
            ],
            FILTER_SPECIFIC_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    fields={"sample_id": "will-be-overwritten", "run_name": RUN_NAME},
                    sample_id=SAMPLE_ID,
                    published_date__range=PUBLISHED_DATE_RANGE,
                )
            ],
            FILTER_SPECIFIC_DATA["data"],
        )
        self.assertEqual(
            [
                x
                for x in self.client.filter(
                    PROJECT,
                    fields={
                        "sample_id": SAMPLE_ID,
                        "run_name": RUN_NAME,
                        "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                    },
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
                    fields={
                        "sample_id": SAMPLE_ID,
                        "run_name": RUN_NAME,
                        "published_date__range": ",".join(PUBLISHED_DATE_RANGE),
                    },
                    exclude=EXCLUDE_FIELDS,
                )
            ],
            FILTER_SPECIFIC_EXCLUDE_DATA["data"],
        )
        for empty in ["", None]:
            self.assertEqual(
                [
                    x
                    for x in self.client.filter(
                        PROJECT,
                        fields={
                            NONE_FIELD: empty,
                        },
                    )
                ],
                FILTER_NONE_DATA["data"],
            )
            self.assertEqual(
                [
                    x
                    for x in self.client.filter(
                        **{"project": PROJECT, NONE_FIELD: empty},
                    )
                ],
                FILTER_NONE_DATA["data"],
            )
            for type_ in [list, tuple, set]:
                self.assertEqual(
                    [
                        x
                        for x in self.client.filter(
                            PROJECT,
                            fields={
                                f"{NONE_FIELD}__in": type_([empty, "not-empty"]),
                            },
                        )
                    ],
                    FILTER_NONE_IN_DATA["data"],
                )
                self.assertEqual(
                    [
                        x
                        for x in self.client.filter(
                            **{
                                "project": PROJECT,
                                f"{NONE_FIELD}__in": type_([empty, "not-empty"]),
                            },
                        )
                    ],
                    FILTER_NONE_IN_DATA["data"],
                )
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                [x for x in self.client.filter(invalid)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_query(self, mock_request):
        """
        Test that the OnyxClient can query records from a project.
        """

        self.assertEqual(
            [x for x in self.client.query(PROJECT)],
            QUERY_PAGE_1_DATA["data"] + QUERY_PAGE_2_DATA["data"],
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

        with pytest.raises(exceptions.OnyxClientError):
            [
                x
                for x in self.client.query(
                    PROJECT, query="not_a_query_object"  #  type: ignore
                )
            ]

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                [x for x in self.client.query(invalid)]

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_to_csv(self, mock_request):
        """
        Test that the OnyxClient can convert records to CSV.
        """

        pass  # TODO Test to_csv

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_history(self, mock_request):
        """
        Test that the OnyxClient can retrieve the history of a record.
        """

        self.assertEqual(self.client.history(PROJECT, CLIMB_ID), HISTORY_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.history(invalid, CLIMB_ID)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.history(PROJECT, invalid)

        for clash in PROJECT_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(clash, CLIMB_ID)

        for clash in CLIMB_ID_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.history(PROJECT, clash)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_identify(self, mock_request):
        """
        Test that the OnyxClient can identify an anonymised value on a field.
        """

        self.assertEqual(
            self.client.identify(PROJECT, IDENTIFY_FIELD, IDENTIFY_VALUE),
            IDENTIFY_DATA["data"],
        )
        self.assertEqual(
            self.client.identify(
                PROJECT, IDENTIFY_FIELD, IDENTIFY_VALUE, site=OTHER_SITE
            ),
            IDENTIFY_OTHER_SITE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.identify(invalid, IDENTIFY_FIELD, IDENTIFY_VALUE)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.identify(
                    invalid, IDENTIFY_FIELD, IDENTIFY_VALUE, site=OTHER_SITE
                )

            with pytest.raises(exceptions.OnyxClientError):
                self.client.identify(PROJECT, invalid, IDENTIFY_VALUE)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.identify(PROJECT, invalid, IDENTIFY_VALUE, site=OTHER_SITE)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_create(self, mock_request):
        """
        Test that the OnyxClient can create a record in a project.
        """

        self.assertEqual(
            self.client.create(PROJECT, CREATE_FIELDS), CREATE_DATA["data"]
        )
        self.assertEqual(
            self.client.create(PROJECT, CREATE_FIELDS, test=True),
            TESTCREATE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.create(invalid, CREATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.create(invalid, CREATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_update(self, mock_request):
        """
        Test that the OnyxClient can update a record in a project.
        """

        self.assertEqual(
            self.client.update(PROJECT, CLIMB_ID, UPDATE_FIELDS), UPDATE_DATA["data"]
        )
        self.assertEqual(
            self.client.update(PROJECT, CLIMB_ID, UPDATE_FIELDS, test=True),
            TESTUPDATE_DATA["data"],
        )
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(invalid, CLIMB_ID, UPDATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(invalid, CLIMB_ID, UPDATE_FIELDS, test=True)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(PROJECT, invalid, UPDATE_FIELDS)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(PROJECT, invalid, UPDATE_FIELDS, test=True)

        for clash in PROJECT_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.get(clash, CLIMB_ID, UPDATE_FIELDS)

        for clash in CLIMB_ID_ENDPOINT_CLASHES:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.update(PROJECT, clash, UPDATE_FIELDS)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_delete(self, mock_request):
        """
        Test that the OnyxClient can delete a record from a project.
        """

        self.assertEqual(self.client.delete(PROJECT, CLIMB_ID), DELETE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.delete(invalid, CLIMB_ID)

            with pytest.raises(exceptions.OnyxClientError):
                self.client.delete(PROJECT, invalid)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_csv_create(self, mock_request):
        """
        Test that the OnyxClient can create records from a CSV file.
        """

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
        """
        Test that the OnyxClient can update records from a CSV file.
        """

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
        """
        Test that the OnyxClient can delete records from a CSV file.
        """

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
        """
        Test that the OnyxClient can register a new user.
        """

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

        for invalid in INVALID_DOMAIN_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                OnyxClient.register(
                    domain=invalid,
                    first_name=FIRST_NAME,
                    last_name=LAST_NAME,
                    email=EMAIL,
                    site=SITE,
                    password=PASSWORD,
                )

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_login(self, mock_request):
        """
        Test that the OnyxClient can login.
        """

        self.assertEqual(self.client.login(), LOGIN_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logout(self, mock_request):
        """
        Test that the OnyxClient can logout.
        """

        self.assertEqual(self.client.logout(), LOGOUT_DATA["data"])
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logoutall(self, mock_request):
        """
        Test that the OnyxClient can logout from all devices.
        """

        self.assertEqual(self.client.logoutall(), LOGOUTALL_DATA["data"])
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_profile(self, mock_request):
        """
        Test that the OnyxClient can retrieve the user profile.
        """

        self.assertEqual(self.client.profile(), PROFILE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_activity(self, mock_request):
        """
        Test that the OnyxClient can retrieve the user's latest activity.
        """

        self.assertEqual(self.client.activity(), ACTIVITY_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_approve(self, mock_request):
        """
        Test that the OnyxClient can approve a user.
        """

        self.assertEqual(self.client.approve(OTHER_USERNAME), APPROVE_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

        for invalid in INVALID_ARGUMENTS:
            with pytest.raises(exceptions.OnyxClientError):
                self.client.approve(invalid)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_waiting(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of users waiting to be approved.
        """

        self.assertEqual(self.client.waiting(), WAITING_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_site_users(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of users on the site.
        """

        self.assertEqual(self.client.site_users(), SITE_USERS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_all_users(self, mock_request):
        """
        Test that the OnyxClient can retrieve a list of all users.
        """

        self.assertEqual(self.client.all_users(), ALL_USERS_DATA["data"])
        self.assertEqual(self.config.token, TOKEN)
