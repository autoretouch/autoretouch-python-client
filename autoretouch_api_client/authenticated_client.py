import json
import time
import webbrowser
from datetime import datetime
from json.decoder import JSONDecodeError
from typing import Optional, List, Dict
from uuid import UUID

from autoretouch_api_client.client import AutoretouchClient, DEFAULT_USER_AGENT, DEFAULT_CONFIG
from autoretouch_api_client.model import ApiConfig, Organization, Workflow, Page, WorkflowExecution, Credentials, \
    DeviceCodeResponse, AccessTokenResponse


class AutoretouchClientAuthenticated:
    def __init__(self, credentials_path: str, user_agent: str = DEFAULT_USER_AGENT, api_config: ApiConfig = DEFAULT_CONFIG):
        self.api = AutoretouchClient(user_agent=user_agent, api_config=api_config)

        self.CREDENTIALS_PATH = credentials_path
        self.credentials = self._create_or_get_credentials()
        self._refresh_credentials_if_expired()

    def get_api_status(self) -> int:
        return self.api.get_api_status()

    def get_api_status_current(self) -> int:
        return self.api.get_api_status_current()

    def get_organizations(self) -> List[Organization]:
        self._refresh_credentials_if_expired()
        return self.api.get_organizations(self.credentials.access_token)

    def get_workflows(self, organization_id: UUID) -> List[Workflow]:
        self._refresh_credentials_if_expired()
        return self.api.get_workflows(self.credentials.access_token, organization_id)

    def get_workflow_executions(self, organization_id: UUID, workflow_id: UUID) -> Page:
        self._refresh_credentials_if_expired()
        return self.api.get_workflow_executions(self.credentials.access_token, organization_id, workflow_id)

    def upload_image(self, organization_id: UUID, filepath: str) -> str:
        self._refresh_credentials_if_expired()
        return self.api.upload_image(self.credentials.access_token, organization_id, filepath)

    def download_image(self, organization_id: UUID, content_hash: str, output_filename: str) -> bytes:
        self._refresh_credentials_if_expired()
        return self.api.download_image(self.credentials.access_token, organization_id, content_hash, output_filename)

    def create_workflow_execution_for_image_reference(
            self, workflow_id: UUID, workflow_version_id: Optional[UUID], organization_id: UUID,
            image_content_hash: str, image_name: str, mimetype: str, labels: Dict[str, str]) -> UUID:
        self._refresh_credentials_if_expired()
        return self.api.create_workflow_execution_for_image_reference(
            self.credentials.access_token, workflow_id, workflow_version_id, organization_id,
            image_content_hash, image_name, mimetype, labels)

    def create_workflow_execution_for_image_file(
            self, workflow_id: UUID, workflow_version_id: Optional[UUID], organization_id: UUID,
            filepath: str, labels: Dict[str, str]) -> UUID:
        self._refresh_credentials_if_expired()
        return self.api.create_workflow_execution_for_image_file(
            self.credentials.access_token, workflow_id, workflow_version_id, organization_id, filepath, labels)

    def get_workflow_execution_details(self, organization_id: UUID, workflow_execution_id: UUID) -> WorkflowExecution:
        self._refresh_credentials_if_expired()
        return self.api.get_workflow_execution_details(self.credentials.access_token, organization_id, workflow_execution_id)

    def get_workflow_execution_status_blocking(self, organization_id: UUID, workflow_execution_id: UUID) -> str:
        self._refresh_credentials_if_expired()
        return self.api.get_workflow_execution_status_blocking(self.credentials.access_token, organization_id, workflow_execution_id)

    def download_workflow_execution_result_blocking(self, organization_id: UUID, workflow_execution_id: UUID) -> bytes:
        self._refresh_credentials_if_expired()
        return self.api.download_workflow_execution_result_blocking(self.credentials.access_token, organization_id, workflow_execution_id)

    def download_workflow_execution_result(self, organization_id: UUID, result_path: str) -> bytes:
        self._refresh_credentials_if_expired()
        return self.api.download_workflow_execution_result(self.credentials.access_token, organization_id, result_path)

    def retry_workflow_execution(self, organization_id: UUID, workflow_execution_id: UUID) -> int:
        self._refresh_credentials_if_expired()
        return self.api.retry_workflow_execution(self.credentials.access_token, organization_id, workflow_execution_id)

    def send_feedback(self, organization_id: UUID, workflow_execution_id: UUID, thumbs_up: bool, expected_images_content_hashes: List[str] = []):
        self._refresh_credentials_if_expired()
        return self.api.send_feedback(self.credentials.access_token, organization_id, workflow_execution_id, thumbs_up, expected_images_content_hashes)

    def revoke_refresh_token(self) -> int:
        return self.api.revoke_refresh_token(self.credentials.refresh_token)

    def _create_or_get_credentials(self) -> Credentials:
        try:
            with open(self.CREDENTIALS_PATH, "r") as credentials_file:
                return Credentials(**json.load(credentials_file))
        except (FileNotFoundError, JSONDecodeError):
            device_code_response = self.api.get_device_code()
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
                return self.api.get_access_and_refresh_token(device_code_response.device_code)
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
            refresh_response = self.api.get_refreshed_access_token(refresh_token=self.credentials.refresh_token)
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
            expires=AutoretouchClientAuthenticated.__get_expiration_isostring(access_token_response.expires_in)
        )

    @staticmethod
    def __get_expiration_isostring(expires_in: int) -> str:
        now = int(datetime.utcnow().timestamp())
        expiration_timestamp = now + expires_in
        return datetime.fromtimestamp(expiration_timestamp).isoformat()