import json
import os
import mimetypes
from uuid import UUID

import requests

from typing import Dict, List, Optional

from autoretouch_api_client.model import (
    ApiConfig, Organization, Page, Workflow, DeviceCodeResponse, AccessTokenResponse, WorkflowExecution)


DEFAULT_CONFIG = ApiConfig(
    BASE_API_URL="https://api.autoretouch.com",
    BASE_API_URL_CURRENT="https://api.autoretouch.com/v1",
    CLIENT_ID="V8EkfbxtBi93cAySTVWAecEum4d6pt4J",
    SCOPE="offline_access",
    AUDIENCE="https://api.autoretouch.com",
    AUTH_DOMAIN="https://auth.autoretouch.com"
)
DEFAULT_USER_AGENT = "samplePythonApiClient"


class AutoretouchClient:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, api_config: ApiConfig = DEFAULT_CONFIG):
        self.USER_AGENT = user_agent
        self.API_CONFIG = api_config

    def get_api_status(self) -> int:
        return requests.get(f"{self.API_CONFIG.BASE_API_URL}/health").status_code

    def get_api_status_current(self, ) -> int:
        return requests.get(f"{self.API_CONFIG.BASE_API_URL_CURRENT}/health").status_code

    def get_device_code(self) -> DeviceCodeResponse:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/device/code"
        payload = f"client_id={self.API_CONFIG.CLIENT_ID}&scope={self.API_CONFIG.SCOPE}&audience={self.API_CONFIG.AUDIENCE}"
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return DeviceCodeResponse(**response.json())

    def get_access_and_refresh_token(self, device_code: str) -> AccessTokenResponse:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/token"
        payload = f"grant_type=urn:ietf:params:oauth:grant-type:device_code" \
                  f"&device_code={device_code}" \
                  f"&client_id={self.API_CONFIG.CLIENT_ID}"
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return AccessTokenResponse(**response.json())

    def get_refreshed_access_token(self, refresh_token: str) -> AccessTokenResponse:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/token"
        payload = f"grant_type=refresh_token" \
                  f"&refresh_token={refresh_token}" \
                  f"&client_id={self.API_CONFIG.CLIENT_ID}"
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return AccessTokenResponse(**response.json(), refresh_token=refresh_token)

    def revoke_refresh_token(self, refresh_token: str) -> int:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/revoke"
        payload = {
            "client_id": self.API_CONFIG.CLIENT_ID,
            "token": refresh_token
        }
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/json"}
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)
        return response.status_code

    def get_organizations(self, access_token: str) -> List[Organization]:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/organization?limit=50&offset=0"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        organizations = [Organization(**entry) for entry in page.entries]
        return organizations

    def get_workflows(self, access_token: str, organization_id: UUID) -> List[Workflow]:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow?limit=50&offset=0&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        workflows = [Workflow(**entry) for entry in page.entries]
        return workflows

    def get_workflow_executions(self, access_token: str, organization_id: UUID, workflow_id: UUID) -> Page:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution?workflow={workflow_id}&limit=50&offset=0&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        page.entries = [WorkflowExecution(**entry) for entry in page.entries]
        return page

    def upload_image(self, access_token: str, organization_id: UUID, filepath: str) -> str:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/upload?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        with open(filepath, 'rb') as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [('file', (filename, file, mimetype))]
            response = requests.post(url=url, headers=headers, files=files)
        self.__assert_response_ok(response)
        return response.content.decode(response.encoding)

    def download_image(self, access_token: str, organization_id: UUID, content_hash: str, output_filename: str) -> bytes:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/image/{content_hash}/{output_filename}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def create_workflow_execution_for_image_reference(
            self, access_token: str, workflow_id: UUID, workflow_version_id: Optional[UUID], organization_id: UUID,
            image_content_hash: str, image_name: str, mimetype: str, labels: Dict[str, str]) -> UUID:
        version_str = f"&version={workflow_version_id}" if workflow_version_id else ""
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/create" \
              f"?workflow={workflow_id}" \
              f"{version_str}" \
              f"&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "image": {
                "name": image_name,
                "contentHash": image_content_hash,
                "contentType": mimetype
            },
            "labels": labels
        }

        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)
        return UUID(response.content.decode(response.encoding))

    def create_workflow_execution_for_image_file(
            self, access_token: str, workflow_id: UUID, workflow_version_id: Optional[UUID], organization_id: UUID,
            filepath: str, labels: Dict[str, str]) -> UUID:
        labels_encoded = "".join([f"&label[{key}]={value}" for key, value in labels.items()])
        version_str = f"&version={workflow_version_id}" if workflow_version_id else ""
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/create" \
              f"?workflow={workflow_id}" \
              f"{version_str}" \
              f"&organization={organization_id}" \
              f"{labels_encoded}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        with open(filepath, 'rb') as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [('file', (filename, file, mimetype))]
            response = requests.post(url=url, headers=headers, files=files)
        self.__assert_response_ok(response)
        return UUID(response.content.decode(response.encoding))

    def get_workflow_execution_details(self, access_token: str, organization_id: UUID, workflow_execution_id: UUID) -> WorkflowExecution:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return WorkflowExecution(**response.json())

    def get_workflow_execution_status_blocking(self, access_token: str, organization_id: UUID, workflow_execution_id: UUID) -> str:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/status?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "text/event-stream"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        # TODO: decode event stream format
        return response.content.decode(response.encoding)

    def download_workflow_execution_result_blocking(self, access_token: str, organization_id: UUID, workflow_execution_id: UUID) -> bytes:
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/result/default?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def download_workflow_execution_result(self, access_token: str, organization_id: UUID, result_path: str) -> bytes:
        assert result_path.startswith("/image/")
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}{result_path}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def send_feedback(self, access_token: str, organization_id: UUID, workflow_execution_id: UUID, thumbs_up: bool, expected_images_content_hashes: List[str] = []):
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/feedback?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "thumbsUp": thumbs_up,
            "expectedImages": expected_images_content_hashes
        }
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)

    @staticmethod
    def __assert_response_ok(response):
        if response.status_code != 200 and response.status_code != 201:
            raise RuntimeError(f"API responded with Status Code {response.status_code}, reason: {response.reason}")
