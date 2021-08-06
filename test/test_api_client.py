
from unittest import TestCase, skip
from uuid import UUID
from assertpy import assert_that

from autoretouch_api_client.client import get_api_status, get_device_code, get_access_and_refresh_token, \
    get_api_status_current, get_organizations, get_workflows, upload_image, \
    create_workflow_execution_for_image_reference, create_workflow_execution_for_image_file, \
    get_workflow_execution_details
from test.auth import create_or_get_credentials


class HealthApiIntegrationTest(TestCase):
    def test_health(self):
        self.assertEqual(get_api_status(), 200)

    def test_health_versioned(self):
        self.assertEqual(get_api_status_current(), 200)





class AuthorizedApiIntegrationTest(TestCase):
    access_token = create_or_get_credentials()

    def test_workflow_execution(self):
        organizations = get_organizations(self.access_token)
        organization = organizations[0]
        self.assertIsNotNone(organization)
        workflows = get_workflows(self.access_token, organization.id)
        workflow = workflows[0]
        self.assertIsNotNone(workflow)

        # Upload image file first, start workflow execution with content hash

        image_content_hash = upload_image(self.access_token, organization.id, "../assets/input_image.jpeg")
        self.assertIsNotNone(image_content_hash)
        self.assertEqual(image_content_hash, "8bcac2125bd98cd96ba75667b9a8832024970ac05bf4123f864bb63bcfefbcf7")

        workflow_execution_id = create_workflow_execution_for_image_file(
            self.access_token, workflow.id, workflow.version, organization.id,
            "../assets/input_image.jpeg", {"myLabel": "myValue"})
        self.assertIsNotNone(workflow_execution_id)

        # Start workflow execution directly for image file

        workflow_execution_id = create_workflow_execution_for_image_reference(
            self.access_token, workflow.id, workflow.version, organization.id,
            image_content_hash, "my_image.jpg", "image/jpeg", {"myLabel": "myValue"})
        self.assertIsNotNone(workflow_execution_id)

        execution_details = get_workflow_execution_details(self.access_token, organization.id, workflow_execution_id)
        assert_that(execution_details.workflow).is_equal_to(workflow.id)
        assert_that(execution_details.workflowVersion).is_equal_to(workflow.version)
        assert_that(execution_details.organizationId).is_equal_to(organization.id)
        assert_that(execution_details.inputContentHash).is_equal_to(image_content_hash)
        assert_that(execution_details.inputFileName).is_equal_to("my_image.jpg")
        assert_that(execution_details.labels).is_equal_to({"myLabel": "myValue"})



