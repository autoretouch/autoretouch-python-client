import time
from typing import Tuple, Dict
from unittest import TestCase
from uuid import UUID
from assertpy import assert_that

from autoretouch_api_client.client import (
    get_api_status, get_api_status_current, get_organizations, get_workflows,
    upload_image, create_workflow_execution_for_image_reference, create_workflow_execution_for_image_file,
    get_workflow_execution_details, download_workflow_execution_result_blocking, download_workflow_execution_result,
    download_image, get_workflow_executions)
from autoretouch_api_client.model import Organization, Workflow, WorkflowExecution
from test.auth import create_or_get_credentials


class HealthApiIntegrationTest(TestCase):
    def test_health(self):
        self.assertEqual(get_api_status(), 200)

    def test_health_versioned(self):
        self.assertEqual(get_api_status_current(), 200)


class AuthorizedApiIntegrationTest(TestCase):
    access_token = create_or_get_credentials()

    # Warning! This integration test runs real workflow executions in your autoretouch account which will cost money.

    def test_upload_image_then_start_workflow_execution(self):
        organization, workflow = self.__get_organization_and_workflow()

        input_image_content_hash = upload_image(self.access_token, organization.id, "../assets/input_image.jpeg")
        self.assertIsNotNone(input_image_content_hash)
        self.assertEqual(input_image_content_hash, "8bcac2125bd98cd96ba75667b9a8832024970ac05bf4123f864bb63bcfefbcf7")

        workflow_execution_id = create_workflow_execution_for_image_reference(
            self.access_token, workflow.id, workflow.version, organization.id,
            input_image_content_hash, "input_image.jpeg", "image/jpeg", {"myLabel": "myValue"})
        self.assertIsNotNone(workflow_execution_id)

        self.__assert_execution_has_started(organization, workflow, workflow_execution_id, input_image_content_hash, "input_image.jpeg", {"myLabel": "myValue"})
        self.__assert_workflow_executions_contain_execution(organization, workflow, workflow_execution_id)

        self.__wait_for_execution_to_complete(organization, workflow_execution_id)
        workflow_execution_completed = self.__get_completed_execution_and_assert_fields(organization, workflow, workflow_execution_id, input_image_content_hash, "input_image.jpeg", {"myLabel": "myValue"})

        self.__download_result_and_assert_equal(organization, workflow_execution_completed)


    def test_start_workflow_execution_immediately_and_wait(self):
        organization, workflow = self.__get_organization_and_workflow()

        workflow_execution_id = create_workflow_execution_for_image_file(
            self.access_token, workflow.id, workflow.version, organization.id,
            "../assets/input_image.jpeg", {"myLabel": "myValue"})
        self.assertIsNotNone(workflow_execution_id)

        input_image_content_hash = "8bcac2125bd98cd96ba75667b9a8832024970ac05bf4123f864bb63bcfefbcf7"
        self.__assert_execution_has_started(organization, workflow, workflow_execution_id, input_image_content_hash, "input_image.jpeg", {"myLabel": "myValue"})
        self.__assert_workflow_executions_contain_execution(organization, workflow, workflow_execution_id)

        result_bytes = download_workflow_execution_result_blocking(self.access_token, organization.id, workflow_execution_id)
        assert_that(len(result_bytes)).is_greater_than(0)
        workflow_execution_completed = self.__get_completed_execution_and_assert_fields(organization, workflow, workflow_execution_id, input_image_content_hash, "input_image.jpeg", {"myLabel": "myValue"})

        self.__download_result_and_assert_equal(organization, workflow_execution_completed)

    def __get_organization_and_workflow(self) -> Tuple[Organization, Workflow]:
        organizations = get_organizations(self.access_token)
        organization = organizations[0]
        self.assertIsNotNone(organization)
        workflows = get_workflows(self.access_token, organization.id)
        workflow = workflows[0]
        self.assertIsNotNone(workflow)
        return organization, workflow

    def __assert_execution_has_started(self, organization: Organization, workflow: Workflow, workflow_execution_id: UUID,
                                       input_image_content_hash: str, input_image_name: str, labels: Dict[str, str]):
        execution_details = get_workflow_execution_details(self.access_token, organization.id, workflow_execution_id)
        assert_that(execution_details.workflow).is_equal_to(workflow.id)
        assert_that(execution_details.workflowVersion).is_equal_to(workflow.version)
        assert_that(execution_details.organizationId).is_equal_to(organization.id)
        assert_that(execution_details.inputContentHash).is_equal_to(input_image_content_hash)
        assert_that(execution_details.inputFileName).is_equal_to(input_image_name)
        assert_that(execution_details.labels).is_equal_to(labels)
        assert_that(["CREATED", "ACTIVE"]).contains(execution_details.status)

    def __assert_workflow_executions_contain_execution(self, organization: Organization, workflow: Workflow, workflow_execution_id: UUID):
        workflow_executions = get_workflow_executions(self.access_token, organization.id, workflow.id)
        assert_that(len(workflow_executions.entries)).is_greater_than(0)
        assert_that(workflow_executions.total).is_greater_than(0)
        assert_that([entry.id for entry in workflow_executions.entries]).contains(workflow_execution_id)

    def __wait_for_execution_to_complete(self, organization: Organization, workflow_execution_id: UUID):
        timeout = 10
        interval = 1
        seconds_waited = 0
        while seconds_waited < timeout:
            execution_details = get_workflow_execution_details(self.access_token, organization.id, workflow_execution_id)
            if execution_details.status == "COMPLETED":
                return
            elif execution_details.status == "FAILED" or execution_details.status == "PAYMENT_REQUIRED":
                raise RuntimeError(f"Workflow Execution ended in error state {execution_details.status}")
            seconds_waited += interval
            time.sleep(1)
        raise RuntimeError(f"Workflow Execution did not complete in {timeout} seconds")

    def __get_completed_execution_and_assert_fields(self, organization: Organization, workflow: Workflow, workflow_execution_id: UUID,
                                                    input_image_content_hash: str, input_image_name: str, labels: Dict[str, str]) -> WorkflowExecution:
        execution_details_completed = get_workflow_execution_details(self.access_token, organization.id,
                                                                     workflow_execution_id)
        assert_that(execution_details_completed.workflow).is_equal_to(workflow.id)
        assert_that(execution_details_completed.workflowVersion).is_equal_to(workflow.version)
        assert_that(execution_details_completed.organizationId).is_equal_to(organization.id)
        assert_that(execution_details_completed.inputContentHash).is_equal_to(input_image_content_hash)
        assert_that(execution_details_completed.inputFileName).is_equal_to(input_image_name)
        assert_that(execution_details_completed.labels).is_equal_to(labels)
        assert_that(execution_details_completed.status).is_equal_to("COMPLETED")
        assert_that(execution_details_completed.chargedCredits).is_greater_than_or_equal_to(10)
        assert_that(execution_details_completed.resultContentHash).is_not_empty()
        assert_that(execution_details_completed.resultContentType).is_not_empty()
        assert_that(execution_details_completed.resultFileName).is_not_empty()
        assert_that(execution_details_completed.resultPath).starts_with("/image/")
        return execution_details_completed

    def __download_result_and_assert_equal(self, organization: Organization, workflow_execution: WorkflowExecution):
        result_bytes = download_workflow_execution_result_blocking(self.access_token, organization.id, workflow_execution.id)
        assert_that(len(result_bytes)).is_greater_than(0)

        result_bytes_2 = download_workflow_execution_result(self.access_token, organization.id, workflow_execution.resultPath)
        assert_that(len(result_bytes_2)).is_greater_than(0)
        assert_that(result_bytes_2).is_equal_to(result_bytes)

        result_bytes_3 = download_image(self.access_token, organization.id, workflow_execution.resultContentHash, workflow_execution.resultFileName)
        assert_that(len(result_bytes_3)).is_greater_than(0)
        assert_that(result_bytes_3).is_equal_to(result_bytes)
