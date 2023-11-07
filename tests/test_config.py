import pytest
from unittest import TestCase
from onyx import OnyxConfig
from onyx.exceptions import OnyxConfigError


DOMAIN = "https://onyx.domain"
TOKEN = "token"
USERNAME = "username"
PASSWORD = "password"


class OnyxConfigTestCase(TestCase):
    def test_init(self):
        config = OnyxConfig(
            domain=DOMAIN,
            token=TOKEN,
            username=USERNAME,
            password=PASSWORD,
        )
        self.assertEqual(config.domain, DOMAIN)
        self.assertEqual(config.token, TOKEN)
        self.assertEqual(config.username, USERNAME)
        self.assertEqual(config.password, PASSWORD)

        config = OnyxConfig(
            domain=DOMAIN,
            token=TOKEN,
        )
        self.assertEqual(config.domain, DOMAIN)
        self.assertEqual(config.token, TOKEN)

        config = OnyxConfig(
            domain=DOMAIN,
            username=USERNAME,
            password=PASSWORD,
        )
        self.assertEqual(config.domain, DOMAIN)
        self.assertEqual(config.username, USERNAME)
        self.assertEqual(config.password, PASSWORD)

        # TODO: Handle " "
        for empty in ["", None]:
            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=empty,
                    token=TOKEN,
                    username=USERNAME,
                    password=PASSWORD,
                )

            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=empty,
                    token=TOKEN,
                )

            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=empty,
                    username=USERNAME,
                    password=PASSWORD,
                )

            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=DOMAIN,
                    token=empty,
                    username=empty,
                    password=empty,
                )

            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=DOMAIN,
                    token=empty,
                    username=USERNAME,
                    password=empty,
                )

            with pytest.raises(OnyxConfigError):
                OnyxConfig(
                    domain=DOMAIN,
                    token=empty,
                    username=empty,
                    password=PASSWORD,
                )
