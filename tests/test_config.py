import pytest
from onyx import OnyxConfig
from onyx.exceptions import OnyxConfigError


domain = "https://onyx.domain"
token = "token"
username = "username"
password = "password"


def test_config_ok():
    config = OnyxConfig(
        domain=domain,
        token=token,
        username=username,
        password=password,
    )
    assert config.domain == domain
    assert config.token == token
    assert config.username == username
    assert config.password == password


def test_config_token_ok():
    config = OnyxConfig(
        domain=domain,
        token=token,
    )
    assert config.domain == domain
    assert config.token == token


def test_config_username_password_ok():
    config = OnyxConfig(
        domain=domain,
        username=username,
        password=password,
    )
    assert config.domain == domain
    assert config.username == username
    assert config.password == password


def test_config_empty_domain_fail():
    # TODO: Handle " "
    for empty in ["", None]:
        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=empty,
                token=token,
                username=username,
                password=password,
            )

        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=empty,
                token=token,
            )

        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=empty,
                username=username,
                password=password,
            )


def test_config_empty_auth_fail():
    # TODO: Handle " "
    for empty in ["", None]:
        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=domain,
                token=empty,
                username=empty,
                password=empty,
            )

        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=domain,
                token=empty,
                username=username,
                password=empty,
            )

        with pytest.raises(OnyxConfigError):
            OnyxConfig(
                domain=domain,
                token=empty,
                username=username,
                password=empty,
            )
