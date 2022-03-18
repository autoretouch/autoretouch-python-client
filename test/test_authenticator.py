from unittest import TestCase, skip
from assertpy import assert_that
import os

from autoretouch_api_client.client import AutoRetouchAPIClient
from test.api_config_dev import CONFIG_DEV

USER_AGENT = "Python-Unit-Test-0.0.1"


class RevokeAuthenticationIntegrationTest(TestCase):
    def test_authenticate_from_file(self):
        pass

    def test_authenticate_with_device_flow(self):
        pass

    def test_should_persist_new_credentials(self):
        pass

    def test_should_refresh_expired_token(self):
        pass

    def test_revoke_authentication(self):
        credentials_path = "../tmp/other-credentials.json"
        client = AutoRetouchAPIClient(api_config=CONFIG_DEV, credentials_path=credentials_path, user_agent=USER_AGENT)

        under_test = client.auth

        assert_that(under_test.credentials.refresh_token).is_not_empty()
        assert_that(under_test.credentials.access_token).is_not_empty()

        assert_that(client.get_organizations()).is_not_empty()

        under_test.revoke_refresh_token()

        assert_that(client.get_organizations).raises(RuntimeError)

        os.remove(credentials_path)
