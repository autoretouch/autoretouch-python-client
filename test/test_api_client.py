
from unittest import TestCase, skip

from autoretouch_api_client.client import get_api_status, get_device_code, get_access_and_refresh_token, \
    get_api_status_current, get_organizations, get_workflows, upload_image, \
    create_workflow_execution_for_image_reference
from test.auth import create_or_get_credentials


class HealthApiTestCase(TestCase):
    def test_health(self):
        self.assertEqual(get_api_status(), 200)

    def test_health_versioned(self):
        self.assertEqual(get_api_status_current(), 200)


class AuthorizedApiTestCase(TestCase):
    access_token = create_or_get_credentials()

    def test_workflow_execution(self):
        organizations = get_organizations(self.access_token)
        organization = organizations[0]
        self.assertIsNotNone(organization)
        workflows = get_workflows(self.access_token)
        workflow = workflows[0]
        self.assertIsNotNone(workflow)

        image_content_hash = upload_image(self.access_token,
                                          "my_image.jpg", "image/jpeg", organization.id, "../assets/input_image.jpeg")
        self.assertIsNotNone(image_content_hash)

        workflow_execution_id = create_workflow_execution_for_image_reference(
            self.access_token, workflow.id, workflow.version, organization.id,
            image_content_hash, "my_image.jpg", "image/jpeg", {})
        self.assertIsNotNone(workflow_execution_id)
