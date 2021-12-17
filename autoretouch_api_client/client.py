import json
import os
import mimetypes
import time
import webbrowser
from datetime import datetime
from json.decoder import JSONDecodeError
from uuid import UUID

import requests

from typing import Dict, List

from autoretouch_api_client.model import (
    ApiConfig, Organization, Page, Workflow, DeviceCodeResponse, AccessTokenResponse, WorkflowExecution, Credentials)


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
    def __init__(self, credentials_path: str, user_agent: str = DEFAULT_USER_AGENT, api_config: ApiConfig = DEFAULT_CONFIG):
        self.CREDENTIALS_PATH = credentials_path
        self.USER_AGENT = user_agent
        self.API_CONFIG = api_config

        self.credentials = self._create_or_get_credentials()
        self._refresh_credentials_if_expired()

    def get_api_status(self) -> int:
        return requests.get(f"{self.API_CONFIG.BASE_API_URL}/health").status_code

    def get_api_status_current(self, ) -> int:
        return requests.get(f"{self.API_CONFIG.BASE_API_URL_CURRENT}/health").status_code

    def get_organizations(self) -> List[Organization]:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/organization?limit=50&offset=0"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        organizations = [Organization(**entry) for entry in page.entries]
        return organizations

    def get_workflows(self, organization_id: UUID) -> List[Workflow]:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow?limit=50&offset=0&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        workflows = [Workflow(**entry) for entry in page.entries]
        return workflows

    def get_workflow_executions(self, organization_id: UUID, workflow_id: UUID) -> Page:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution?workflow={workflow_id}&limit=50&offset=0&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        page.entries = [WorkflowExecution(**entry) for entry in page.entries]
        return page

    def upload_image(self, organization_id: UUID, filepath: str) -> str:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/upload?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        with open(filepath, 'rb') as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [('file', (filename, file, mimetype))]
            response = requests.post(url=url, headers=headers, files=files)
        self.__assert_response_ok(response)
        return response.content.decode(response.encoding)

    def download_image(self, organization_id: UUID, content_hash: str, output_filename: str) -> bytes:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/image/{content_hash}/{output_filename}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def create_workflow_execution_for_image_reference(
            self, workflow_id: UUID, workflow_version_id: UUID, organization_id: UUID,
            image_content_hash: str, image_name: str, mimetype: str, labels: Dict[str, str]) -> UUID:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/create" \
              f"?workflow={workflow_id}" \
              f"&version={workflow_version_id}" \
              f"&organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "application/json"}
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
            self, workflow_id: UUID, workflow_version_id: UUID, organization_id: UUID,
            filepath: str, labels: Dict[str, str]) -> UUID:
        self._refresh_credentials_if_expired()
        labels_encoded = "".join([f"&label[{key}]={value}" for key, value in labels.items()])
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/create" \
              f"?workflow={workflow_id}" \
              f"&version={workflow_version_id}" \
              f"&organization={organization_id}" \
              f"{labels_encoded}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        with open(filepath, 'rb') as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [('file', (filename, file, mimetype))]
            response = requests.post(url=url, headers=headers, files=files)
        self.__assert_response_ok(response)
        return UUID(response.content.decode(response.encoding))

    def get_workflow_execution_details(self, organization_id: UUID, workflow_execution_id: UUID) -> WorkflowExecution:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return WorkflowExecution(**response.json())

    def get_workflow_execution_status_blocking(self, organization_id: UUID, workflow_execution_id: UUID) -> str:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/status?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "text/event-stream"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        # TODO: decode event stream format
        return response.content.decode(response.encoding)

    def download_workflow_execution_result_blocking(self, organization_id: UUID, workflow_execution_id: UUID) -> bytes:
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/result/default?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def download_workflow_execution_result(self, organization_id: UUID, result_path: str) -> bytes:
        self._refresh_credentials_if_expired()
        assert result_path.startswith("/image/")
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}{result_path}?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return response.content

    def send_feedback(self, organization_id: UUID, workflow_execution_id: UUID, thumbs_up: bool, expected_images_content_hashes: List[str] = []):
        self._refresh_credentials_if_expired()
        url = f"{self.API_CONFIG.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/feedback?organization={organization_id}"
        headers = {"User-Agent": self.USER_AGENT, "Authorization": f"Bearer {self.credentials.access_token}", "Content-Type": "application/json"}
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

    # Auth API

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

    def get_refreshed_access_token(self) -> AccessTokenResponse:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/token"
        payload = f"grant_type=refresh_token" \
                  f"&refresh_token={self.credentials.refresh_token}" \
                  f"&client_id={self.API_CONFIG.CLIENT_ID}"
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return AccessTokenResponse(**response.json(), refresh_token=self.credentials.refresh_token)

    def revoke_refresh_token(self) -> int:
        url = f"{self.API_CONFIG.AUTH_DOMAIN}/oauth/revoke"
        payload = {
            "client_id": self.API_CONFIG.CLIENT_ID,
            "token": self.credentials.refresh_token
        }
        headers = {"User-Agent": self.USER_AGENT, "Content-Type": "application/json"}
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)
        return response.status_code

    # Auth Logic

    def _create_or_get_credentials(self) -> Credentials:
        try:
            with open(self.CREDENTIALS_PATH, "r") as credentials_file:
                return Credentials(**json.load(credentials_file))
        except (FileNotFoundError, JSONDecodeError):
            device_code_response = self.get_device_code()
            self.__open_browser_for_verification(device_code_response)
            access_token_response = self.__wait_for_user_confirmation(device_code_response)
            credentials = self.__access_token_response_to_credentials(access_token_response)
            self.__save_credentials(credentials, self.CREDENTIALS_PATH)
            return credentials

    @staticmethod
    def __save_credentials(credentials: Credentials, credentials_path: str):
        with open(credentials_path, "w") as credentials_file:
            json.dump(credentials, credentials_file, default=lambda o: o.__dict__, indent=4)

    def __wait_for_user_confirmation(self, device_code_response: DeviceCodeResponse) -> AccessTokenResponse:
        seconds_waited = 0
        while seconds_waited < device_code_response.expires_in:
            print("Waiting for user confirmation...")
            try:
                return self.get_access_and_refresh_token(device_code_response.device_code)
            except:
                seconds_waited += device_code_response.interval
                time.sleep(device_code_response.interval)
        raise RuntimeError(f"Device Code not confirmed after {seconds_waited} seconds")

    @staticmethod
    def __open_browser_for_verification(device_code_response: DeviceCodeResponse):
        print(f"Open verification url {device_code_response.verification_uri_complete} in the browser "
              f"and confirm the user code '{device_code_response.user_code}'.")
        try:
            webbrowser.open(device_code_response.verification_uri_complete)
        except:
            print("Opening web browser failed")

    def _refresh_credentials_if_expired(self):
        if self.__token_expired(self.credentials.expires):
            print("access token expired, refreshing ...")
            refresh_response = self.get_refreshed_access_token()
            credentials = self.__access_token_response_to_credentials(refresh_response)
            self.__save_credentials(credentials, self.CREDENTIALS_PATH)
            self.credentials = credentials

    @staticmethod
    def __token_expired(expiration_isostring: str) -> bool:
        expiration_timestamp = datetime.fromisoformat(expiration_isostring).timestamp()
        now = int(datetime.utcnow().timestamp())
        return now + 30 > expiration_timestamp

    @staticmethod
    def __access_token_response_to_credentials(access_token_response: AccessTokenResponse) -> Credentials:
        return Credentials(
            access_token=access_token_response.access_token,
            refresh_token=access_token_response.refresh_token,
            scope=access_token_response.scope,
            token_type=access_token_response.token_type,
            expires=AutoretouchClient.__get_expiration_isostring(access_token_response.expires_in)
        )

    @staticmethod
    def __get_expiration_isostring(expires_in: int) -> str:
        now = int(datetime.utcnow().timestamp())
        expiration_timestamp = now + expires_in
        return datetime.fromtimestamp(expiration_timestamp).isoformat()
