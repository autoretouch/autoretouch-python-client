import json
from datetime import datetime
from json.decoder import JSONDecodeError
from typing import Optional, List, Dict
from uuid import UUID

from autoretouch_api_client.client import AutoretouchClient, DEFAULT_USER_AGENT, DEFAULT_API_CONFIG
from autoretouch_api_client.device_authentication import authenticate_device_and_get_refresh_token
from autoretouch_api_client.model import ApiConfig, Organization, Workflow, Page, WorkflowExecution, Credentials, \
    AccessTokenResponse


class AutoretouchClientAuthenticated:
    def __init__(self,
                 refresh_token: str,
                 user_agent: str = DEFAULT_USER_AGENT,
                 api_config: ApiConfig = DEFAULT_API_CONFIG):
        self.api = AutoretouchClient(user_agent=user_agent, api_config=api_config)
        refresh_response = self.api.get_refreshed_access_token(refresh_token=refresh_token)
        self.credentials = self.__access_token_response_to_credentials(refresh_response)

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

    def _refresh_credentials_if_expired(self):
        if not self.credentials.access_token or self.__token_expired(self.credentials.expires):
            print("access token expired, refreshing ...")
            self._refresh_credentials()

    def _refresh_credentials(self):
        refresh_response = self.api.get_refreshed_access_token(refresh_token=self.credentials.refresh_token)
        self.credentials = self.__access_token_response_to_credentials(refresh_response)

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


class NoCredentialsOrRefreshTokenError(RuntimeError):
    def __init__(self):
        super().__init__("Credentials file not found or could be read. Specify a refresh token.")


class AutoretouchClientAuthenticatedPersistent(AutoretouchClientAuthenticated):
    def __init__(self,
                 credentials_path: str,
                 refresh_token: Optional[str],
                 user_agent: str = DEFAULT_USER_AGENT,
                 api_config: ApiConfig = DEFAULT_API_CONFIG):
        self.credentials_path = credentials_path
        if not refresh_token:
            refresh_token = self.__read_credentials().refresh_token
        super().__init__(refresh_token, user_agent, api_config)
        self.__save_credentials(self.credentials)

    # override
    def _refresh_credentials(self):
        super()._refresh_credentials()
        self.__save_credentials(self.credentials)

    def __read_credentials(self) -> Credentials:
        try:
            with open(self.credentials_path, "r") as credentials_file:
                return Credentials(**json.load(credentials_file))
        except (FileNotFoundError, JSONDecodeError):
            raise NoCredentialsOrRefreshTokenError()

    def __save_credentials(self, credentials: Credentials):
        with open(self.credentials_path, "w") as credentials_file:
            json.dump(credentials, credentials_file, default=lambda o: o.__dict__, indent=4)


def authenticate_device_and_get_client(user_agent: str = DEFAULT_USER_AGENT,
                                       api_config: ApiConfig = DEFAULT_API_CONFIG):
    refresh_token = authenticate_device_and_get_refresh_token(user_agent, api_config)
    return AutoretouchClientAuthenticated(refresh_token, user_agent, api_config)


def authenticate_device_and_get_client_with_persistence(credentials_path: str,
                                                        user_agent: str = DEFAULT_USER_AGENT,
                                                        api_config: ApiConfig = DEFAULT_API_CONFIG):
    try:
        return AutoretouchClientAuthenticatedPersistent(credentials_path=credentials_path, refresh_token=None,
                                                        user_agent=user_agent, api_config=api_config)
    except NoCredentialsOrRefreshTokenError:
        refresh_token = authenticate_device_and_get_refresh_token(user_agent, api_config)
        return AutoretouchClientAuthenticatedPersistent(credentials_path=credentials_path, refresh_token=refresh_token,
                                                        user_agent=user_agent, api_config=api_config)
