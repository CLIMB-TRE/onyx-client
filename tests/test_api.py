import requests
import pytest
from unittest import TestCase, mock
from onyx import OnyxConfig, OnyxClient
from onyx.exceptions import OnyxClientError


DOMAIN = "https://onyx.domain"
TOKEN = "token"
EXPIRY = "expiry"
USERNAME = "username"
PASSWORD = "password"
EMAIL = "email"
SITE = "site"

OTHER_USERNAME = "other_username"
OTHER_EMAIL = "other_email"

PROJECT = "project"
CID = "C-0123456789"
CHOICE_FIELD = "choice_field"

PROJECT_DATA = [
    {
        "project": PROJECT,
        "action": "view",
        "scope": "base",
    }
]
FIELDS_DATA = {
    "version": "0.1.0",
    "fields": {
        "cid": {
            "type": "text",
            "required": True,
            "description": "Unique identifier for a project. Set by Onyx.",
        }
    },
}
FIELDS_ADMIN_DATA = {
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
}
CHOICES_DATA = [
    "choice_1",
    "choice_2",
    "choice_3",
]
CREATE_FIELDS = {
    "field_1": "value_1",
    "field_2": "value_2",
}
CREATE_DATA = {
    "cid": CID,
}
TESTCREATE_DATA = {
    "cid": None,
}
UPDATE_FIELDS = {
    "field_3": "value_3",
}
UPDATE_DATA = {
    "cid": CID,
}
TESTUPDATE_DATA = {
    "cid": CID,
}
LOGIN_DATA = {
    "token": TOKEN,
    "expiry": EXPIRY,
}
LOGOUT_DATA = None
LOGOUTALL_DATA = None
PROFILE_DATA = {
    "username": USERNAME,
    "email": EMAIL,
    "site": SITE,
}
WAITING_DATA = [
    {
        "username": OTHER_USERNAME,
        "email": OTHER_EMAIL,
        "site": SITE,
    }
]
SITE_USERS_DATA = [
    {
        "username": USERNAME,
        "email": EMAIL,
        "site": SITE,
    }
]
ALL_USERS_DATA = [
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
]
APPROVE_DATA = {
    "username": OTHER_USERNAME,
    "is_approved": True,
}


class MockResponse:
    def __init__(self, data, status_code):
        self.status_code = status_code
        if self.status_code < 400:
            self.ok = True
            self.data = {
                "status": "success",
                "code": status_code,
                "data": data,
            }
        elif 400 <= self.status_code < 500:
            self.ok = False
            self.data = {
                "status": "fail",
                "code": status_code,
                "messages": data,
            }
        else:
            self.ok = False
            self.data = {
                "status": "error",
                "code": status_code,
                "messages": data,
            }

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
    if method == "post":
        if (
            url == OnyxClient.ENDPOINTS["create"](DOMAIN, PROJECT)
            and json == CREATE_FIELDS
        ):
            return MockResponse(CREATE_DATA, 201)

        elif (
            url == OnyxClient.ENDPOINTS["testcreate"](DOMAIN, PROJECT)
            and json == CREATE_FIELDS
        ):
            return MockResponse(TESTCREATE_DATA, 201)

        elif url == OnyxClient.ENDPOINTS["login"](DOMAIN) and auth == (
            USERNAME,
            PASSWORD,
        ):
            return MockResponse(LOGIN_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["logout"](DOMAIN):
            return MockResponse(LOGOUT_DATA, 204)

        elif url == OnyxClient.ENDPOINTS["logoutall"](DOMAIN):
            return MockResponse(LOGOUTALL_DATA, 204)

    elif method == "get":
        if url == OnyxClient.ENDPOINTS["projects"](DOMAIN):
            return MockResponse(PROJECT_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, PROJECT):
            if params == {"scope": None}:
                return MockResponse(FIELDS_DATA, 200)

            elif params == {"scope": "admin"}:
                return MockResponse(FIELDS_ADMIN_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["choices"](DOMAIN, PROJECT, CHOICE_FIELD):
            return MockResponse(CHOICES_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["profile"](DOMAIN):
            return MockResponse(PROFILE_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["waiting"](DOMAIN):
            return MockResponse(WAITING_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["siteusers"](DOMAIN):
            return MockResponse(SITE_USERS_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["allusers"](DOMAIN):
            return MockResponse(ALL_USERS_DATA, 200)

    elif method == "patch":
        if (
            url == OnyxClient.ENDPOINTS["update"](DOMAIN, PROJECT, CID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(UPDATE_DATA, 200)

        elif (
            url == OnyxClient.ENDPOINTS["testupdate"](DOMAIN, PROJECT, CID)
            and json == UPDATE_FIELDS
        ):
            return MockResponse(TESTUPDATE_DATA, 200)

        elif url == OnyxClient.ENDPOINTS["approve"](DOMAIN, OTHER_USERNAME):
            return MockResponse(
                APPROVE_DATA,
                200,
            )

    return MockResponse(
        {"detail": "Something bad happened."},
        400,
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
        self.assertEqual(self.client.projects(), PROJECT_DATA)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_fields(self, mock_request):
        self.assertEqual(self.client.fields(PROJECT), FIELDS_DATA)
        self.assertEqual(self.client.fields(PROJECT, scope="admin"), FIELDS_ADMIN_DATA)

        for empty_project in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.fields(empty_project)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_choices(self, mock_request):
        self.assertEqual(self.client.choices(PROJECT, CHOICE_FIELD), CHOICES_DATA)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.choices(empty, CHOICE_FIELD)

            with pytest.raises(OnyxClientError):
                self.client.choices(PROJECT, empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_create(self, mock_request):
        self.assertEqual(self.client.create(PROJECT, CREATE_FIELDS), CREATE_DATA)
        self.assertEqual(
            self.client.create(PROJECT, CREATE_FIELDS, test=True), TESTCREATE_DATA
        )

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.create(empty, CREATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.create(empty, CREATE_FIELDS, test=True)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_update(self, mock_request):
        self.assertEqual(self.client.update(PROJECT, CID, UPDATE_FIELDS), UPDATE_DATA)
        self.assertEqual(
            self.client.update(PROJECT, CID, UPDATE_FIELDS, test=True), TESTUPDATE_DATA
        )

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.update(empty, CID, UPDATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.update(empty, CID, UPDATE_FIELDS, test=True)

            with pytest.raises(OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS)

            with pytest.raises(OnyxClientError):
                self.client.update(PROJECT, empty, UPDATE_FIELDS, test=True)

    def test_register(self):
        pass  # TODO

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_login(self, mock_request):
        self.assertEqual(self.client.login(), LOGIN_DATA)
        self.assertEqual(self.config.token, TOKEN)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logout(self, mock_request):
        self.assertEqual(self.client.logout(), LOGOUT_DATA)
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_logoutall(self, mock_request):
        self.assertEqual(self.client.logoutall(), LOGOUTALL_DATA)
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_profile(self, mock_request):
        self.assertEqual(self.client.profile(), PROFILE_DATA)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_approve(self, mock_request):
        self.assertEqual(self.client.approve(OTHER_USERNAME), APPROVE_DATA)

        for empty in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.approve(empty)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_waiting(self, mock_request):
        self.assertEqual(self.client.waiting(), WAITING_DATA)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_site_users(self, mock_request):
        self.assertEqual(self.client.site_users(), SITE_USERS_DATA)

    @mock.patch("onyx.OnyxClient._request_handler", side_effect=mock_request)
    def test_all_users(self, mock_request):
        self.assertEqual(self.client.all_users(), ALL_USERS_DATA)
