import requests
import pytest
from unittest import TestCase, mock
from onyx import OnyxConfig, OnyxClient
from onyx.exceptions import OnyxClientError


DOMAIN = "https://onyx.domain"
TOKEN = "token"
USERNAME = "username"
PASSWORD = "password"
EMAIL = "email"
SITE = "site"

OTHER_USERNAME = "other_username"
OTHER_EMAIL = "other_email"

PROJECT = "project"


def mocked_onyx_request(**kwargs):
    class MockResponse:
        def __init__(self, data, status_code):
            self.data = data
            self.status_code = status_code

            if self.status_code >= 400:
                self.ok = False
            else:
                self.ok = True

        def json(self):
            return self.data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(
                    "Something bad happened.",
                    response=self,  #  type: ignore
                )

    method = kwargs.pop("method", None)
    url = kwargs.pop("url", None)
    params = kwargs.pop("params", None)

    if method == "post":
        if url == OnyxClient.ENDPOINTS["logout"](DOMAIN):
            return MockResponse(
                {},
                204,
            )
        elif url == OnyxClient.ENDPOINTS["logoutall"](DOMAIN):
            return MockResponse(
                {},
                204,
            )
    elif method == "get":
        if url == OnyxClient.ENDPOINTS["projects"](DOMAIN):
            return MockResponse(
                {
                    "status": "success",
                    "data": [
                        {
                            "project": PROJECT,
                            "action": "view",
                            "scope": "base",
                        }
                    ],
                },
                200,
            )
        elif url == OnyxClient.ENDPOINTS["fields"](DOMAIN, PROJECT):
            if params == {"scope": None}:
                return MockResponse(
                    {
                        "status": "success",
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
                    },
                    200,
                )
            elif params == {"scope": "admin"}:
                return MockResponse(
                    {
                        "status": "success",
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
                    },
                    200,
                )

        elif url == OnyxClient.ENDPOINTS["profile"](DOMAIN):
            return MockResponse(
                {
                    "status": "success",
                    "data": {
                        "username": USERNAME,
                        "email": EMAIL,
                        "site": SITE,
                    },
                },
                200,
            )
        elif url == OnyxClient.ENDPOINTS["waiting"](DOMAIN):
            return MockResponse(
                {
                    "status": "success",
                    "data": [
                        {
                            "username": OTHER_USERNAME,
                            "email": OTHER_EMAIL,
                            "site": SITE,
                        }
                    ],
                },
                200,
            )
        elif url == OnyxClient.ENDPOINTS["siteusers"](DOMAIN):
            return MockResponse(
                {
                    "status": "success",
                    "data": [
                        {
                            "username": USERNAME,
                            "email": EMAIL,
                            "site": SITE,
                        }
                    ],
                },
                200,
            )
        elif url == OnyxClient.ENDPOINTS["allusers"](DOMAIN):
            return MockResponse(
                {
                    "status": "success",
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
                },
                200,
            )

    elif method == "patch":
        if url == OnyxClient.ENDPOINTS["approve"](DOMAIN, OTHER_USERNAME):
            return MockResponse(
                {
                    "status": "success",
                    "data": {
                        "username": OTHER_USERNAME,
                        "is_approved": True,
                    },
                },
                200,
            )

    return MockResponse(
        {
            "status": "fail",
            "messages": {
                "detail": "Something bad happened.",
            },
        },
        400,
    )


class OnyxClientTestCase(TestCase):
    def setUp(self) -> None:
        self.config = OnyxConfig(
            domain=DOMAIN,
            token=TOKEN,
            username=USERNAME,
            password=PASSWORD,
        )
        self.client = OnyxClient(self.config)

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_projects(self, mock_request):
        self.assertEqual(
            self.client.projects(),
            [
                {
                    "project": PROJECT,
                    "action": "view",
                    "scope": "base",
                }
            ],
        )

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_fields(self, mock_request):
        self.assertEqual(
            self.client.fields(PROJECT),
            {
                "version": "0.1.0",
                "fields": {
                    "cid": {
                        "type": "text",
                        "required": True,
                        "description": "Unique identifier for a project. Set by Onyx.",
                    }
                },
            },
        )
        self.assertEqual(
            self.client.fields(PROJECT, scope="admin"),
            {
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
        )

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_logout(self, mock_request):
        self.assertEqual(self.client.logout(), None)
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_logoutall(self, mock_request):
        self.assertEqual(self.client.logoutall(), None)
        self.assertEqual(self.config.token, None)

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_profile(self, mock_request):
        self.assertEqual(
            self.client.profile(), {"username": USERNAME, "email": EMAIL, "site": SITE}
        )

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_approve(self, mock_request):
        self.assertEqual(
            self.client.approve(OTHER_USERNAME),
            {"username": OTHER_USERNAME, "is_approved": True},
        )

        for empty_username in ["", " ", None]:
            with pytest.raises(OnyxClientError):
                self.client.approve(empty_username)

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_waiting(self, mock_request):
        self.assertEqual(
            self.client.waiting(),
            [{"username": OTHER_USERNAME, "email": OTHER_EMAIL, "site": SITE}],
        )

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_site_users(self, mock_request):
        self.assertEqual(
            self.client.site_users(),
            [{"username": USERNAME, "email": EMAIL, "site": SITE}],
        )

    @mock.patch("onyx.OnyxClient._request", side_effect=mocked_onyx_request)
    def test_all_users(self, mock_request):
        self.assertEqual(
            self.client.all_users(),
            [
                {"username": USERNAME, "email": EMAIL, "site": SITE},
                {"username": OTHER_USERNAME, "email": OTHER_EMAIL, "site": SITE},
            ],
        )
