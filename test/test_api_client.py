from unittest import TestCase, skip

from autoretouch_api_client.client import get_api_status, get_device_code, get_access_and_refresh_token, \
    get_api_status_current, get_organizations, get_workflows


class HealthApiTestCase(TestCase):
    def test_health(self):
        self.assertEqual(get_api_status(), 200)

    def test_health_versioned(self):
        self.assertEqual(get_api_status_current(), 200)


class AuthFlowTestCase(TestCase):
    @skip("Run this manually to get an access token file for the AuthorizedApiTestCase")
    def test_auth_flow(self):
        device_code, user_code, verification_url = get_device_code()
        self.assertIsNotNone(device_code)
        self.assertIsNotNone(user_code)
        self.assertIsNotNone(verification_url)
        # Stop here. Open verification_url in the browser and confirm the device code.
        access_token, refresh_token, _ = get_access_and_refresh_token(device_code)
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        with open("../tmp/access_token.txt", "w") as access_token_file:
            access_token_file.write(access_token)


class AuthorizedApiTestCase(TestCase):
    with open("../tmp/access_token.txt", "r") as access_token_file:
        access_token = access_token_file.read()

    def test_workflow_execution(self):
        organizations = get_organizations(self.access_token)
        organization = organizations[0]
        self.assertIsNotNone(organization)
        workflows = get_workflows(self.access_token)
        workflow = workflows[0]
        self.assertIsNotNone(workflow)


