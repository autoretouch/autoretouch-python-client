from unittest import TestCase
from assertpy import assert_that

from autoretouch_api_client.client import AutoretouchClient
from test.api_config_dev import CONFIG_DEV


class HealthApiIntegrationTest(TestCase):
    def setUp(self) -> None:
        self.client = AutoretouchClient(api_config=CONFIG_DEV, user_agent="Sample-Python-Unit-Test-0.0.1")

    def test_health(self):
        assert_that(self.client.get_api_status()).is_equal_to(200)

    def test_health_versioned(self):
        assert_that(self.client.get_api_status_current()).is_equal_to(200)
