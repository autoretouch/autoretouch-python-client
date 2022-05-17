import json
import os
import mimetypes
from io import BytesIO
from time import sleep
from uuid import UUID
import requests
from typing import Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

from api_client.authenticator import Authenticator
from api_client.model import (
    ApiConfig,
    Organization,
    Page,
    Workflow,
    DeviceCodeResponse,
    WorkflowExecution,
    Credentials,
)

__all__ = ["AutoRetouchAPIClient", "DEFAULT_API_CONFIG"]

DEFAULT_API_CONFIG = ApiConfig(
    BASE_API_URL="https://api.autoretouch.com",
    BASE_API_URL_CURRENT="https://api.autoretouch.com/v1",
    CLIENT_ID="V8EkfbxtBi93cAySTVWAecEum4d6pt4J",
    SCOPE="offline_access",
    AUDIENCE="https://api.autoretouch.com",
    AUTH_DOMAIN="https://auth.autoretouch.com",
)
AR_CREDENTIALS = os.environ.get(
    "AUTORETOUCH_CREDENTIALS_PATH",
    os.path.join(os.path.expanduser("~"), ".config", "autoretouch-credentials.json")
)
AR_REFRESH_TOKEN = os.environ.get(
    "AUTORETOUCH_REFRESH_TOKEN", None
)
DEFAULT_USER_AGENT = "Autoretouch-Python-Api-Client-0.0.1"

T = TypeVar("T", bound=Callable)


def authenticated(endpoint: T):
    """decorator to ensure that the client is authenticated before it calls an endpoint"""

    @wraps(endpoint)
    def wrapper(*args, **kwargs):
        auth: Authenticator = args[0].auth
        if auth.credentials is None:
            auth.authenticate()
        elif auth.token_expired:
            auth.refresh_credentials()
        return endpoint(*args, **kwargs)

    return wrapper


class AutoRetouchAPIClient:
    """
    autoRetouch API client

    :param organization_id:
    :param api_config:
    :param credentials_path: optional path to a .json credential file
    :param refresh_token: optional refresh_token for requesting up-to-dates access_token
    :param user_agent:
    :param save_credentials: whether the credentials should be saved. Default: True
    """
    def __init__(
            self,
            organization_id: Optional[Union[str, UUID]] = None,
            api_config: ApiConfig = DEFAULT_API_CONFIG,
            credentials_path: Optional[str] = AR_CREDENTIALS,
            refresh_token: Optional[str] = AR_REFRESH_TOKEN,
            user_agent: str = DEFAULT_USER_AGENT,
            save_credentials: bool = True,
    ):
        self.api_config = api_config
        self.user_agent = user_agent
        self.auth = Authenticator(
            self, credentials_path, refresh_token, save_credentials
        )
        self.organization_id = organization_id

    @property
    def base_headers(self) -> dict:
        return {
            "User-Agent": self.user_agent,
            "Authorization": f"Bearer {self.auth.credentials.access_token}",
        }

    def get_api_status(self) -> int:
        return requests.get(f"{self.api_config.BASE_API_URL}/health").status_code

    # ****** AUTH ENDPOINTS ******

    def get_device_code(self) -> DeviceCodeResponse:
        url = f"{self.api_config.AUTH_DOMAIN}/oauth/device/code"
        payload = f"client_id={self.api_config.CLIENT_ID}&scope={self.api_config.SCOPE}&audience={self.api_config.AUDIENCE}"
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return DeviceCodeResponse.from_dict(response.json())

    def get_credentials_from_device_code(self, device_code: str) -> Credentials:
        url = f"{self.api_config.AUTH_DOMAIN}/oauth/token"
        payload = (
            f"grant_type=urn:ietf:params:oauth:grant-type:device_code"
            f"&device_code={device_code}"
            f"&client_id={self.api_config.CLIENT_ID}"
        )
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return Credentials(**response.json())

    def get_credentials_from_refresh_token(self, refresh_token: str) -> Credentials:
        url = f"{self.api_config.AUTH_DOMAIN}/oauth/token"
        payload = (
            f"grant_type=refresh_token"
            f"&refresh_token={refresh_token}"
            f"&client_id={self.api_config.CLIENT_ID}"
        )
        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url=url, headers=headers, data=payload)
        self.__assert_response_ok(response)
        return Credentials(refresh_token=refresh_token, **response.json())

    def revoke_refresh_token(self, refresh_token: str) -> int:
        url = f"{self.api_config.AUTH_DOMAIN}/oauth/revoke"
        payload = {"client_id": self.api_config.CLIENT_ID, "token": refresh_token}
        headers = {"User-Agent": self.user_agent, "Content-Type": "application/json"}
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)
        return response.status_code

    def login(self):
        self.auth.authenticate()
        return self

    def logout(self):
        self.auth.revoke_refresh_token()
        return self

    # ****** API ******

    @authenticated
    def get_organizations(self) -> List[Organization]:
        url = f"{self.api_config.BASE_API_URL_CURRENT}/organization?limit=50&offset=0"
        headers = {**self.base_headers, "Content-Type": "application/json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        organizations = [Organization.from_dict(entry) for entry in page.entries]
        return organizations

    @authenticated
    def get_workflows(self, organization_id: Optional[UUID] = None) -> List[Workflow]:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow?limit=50&offset=0&organization={organization_id}"
        headers = {**self.base_headers, "Content-Type": "application/json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        workflows = [Workflow.from_dict(entry) for entry in page.entries]
        return workflows

    @authenticated
    def get_workflow_executions(
            self, workflow_id: UUID, organization_id: Optional[UUID] = None
    ) -> Page:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution?workflow={workflow_id}&limit=50&offset=0&organization={organization_id}"
        response = requests.get(url=url, headers=self.base_headers)
        self.__assert_response_ok(response)
        page = Page(**response.json())
        page.entries = [WorkflowExecution.from_dict(entry) for entry in page.entries]
        return page

    @authenticated
    def upload_image(
            self, image_path: str, organization_id: Optional[UUID] = None
    ) -> str:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/upload?organization={organization_id}"
        with open(image_path, "rb") as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [("file", (filename, file, mimetype))]
            response = requests.post(url=url, headers=self.base_headers, files=files)
        self.__assert_response_ok(response)
        return response.content.decode(response.encoding)

    @authenticated
    def upload_image_from_bytes(
            self,
            image_content: bytes,
            image_name: str,
            mimetype: Optional[str] = None,
            organization_id: Optional[UUID] = None,
    ) -> str:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/upload?organization={organization_id}"
        if not mimetype:
            mimetype, _ = mimetypes.guess_type(image_name)
        with BytesIO(image_content) as file:
            files = [("file", (image_name, file, mimetype))]
            response = requests.post(url=url, headers=self.base_headers, files=files)
        self.__assert_response_ok(response)
        return response.content.decode(response.encoding)

    @authenticated
    def create_workflow_execution_for_image_file(
            self,
            workflow_id: UUID,
            image_path: str,
            labels: Optional[Dict[str, str]] = None,
            workflow_version_id: Optional[UUID] = None,
            organization_id: Optional[UUID] = None,
    ) -> UUID:
        organization_id = self._get_organization_id(organization_id)
        labels = labels or {}
        labels_encoded = "".join(
            [f"&label[{key}]={value}" for key, value in labels.items()]
        )
        version_str = f"&version={workflow_version_id}" if workflow_version_id else ""
        url = (
            f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/create"
            f"?workflow={workflow_id}"
            f"{version_str}"
            f"&organization={organization_id}"
            f"{labels_encoded}"
        )
        with open(image_path, "rb") as file:
            filename = os.path.basename(file.name)
            mimetype, _ = mimetypes.guess_type(file.name)
            files = [("file", (filename, file, mimetype))]
            response = requests.post(url=url, headers=self.base_headers, files=files)
        self.__assert_response_ok(response)
        return UUID(response.content.decode(response.encoding))

    @authenticated
    def create_workflow_execution_for_image_reference(
            self,
            workflow_id: UUID,
            image_content_hash: str,
            image_name: str,
            labels: Optional[Dict[str, str]] = None,
            workflow_version_id: Optional[UUID] = None,
            organization_id: Optional[UUID] = None,
    ) -> UUID:
        organization_id = self._get_organization_id(organization_id)
        version_str = f"&version={workflow_version_id}" if workflow_version_id else ""
        url = (
            f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/create"
            f"?workflow={workflow_id}"
            f"{version_str}"
            f"&organization={organization_id}"
        )
        headers = {**self.base_headers, "Content-Type": "application/json"}
        mimetype, _ = mimetypes.guess_type(image_name)
        payload = {
            "image": {
                "name": image_name,
                "contentHash": image_content_hash,
                "contentType": mimetype,
            },
            **({"labels": labels} if labels else {}),
        }

        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)
        return UUID(response.content.decode(response.encoding))

    @authenticated
    def get_workflow_execution_details(
            self, workflow_execution_id: UUID, organization_id: Optional[UUID] = None
    ) -> WorkflowExecution:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}?organization={organization_id}"
        headers = {**self.base_headers, "Content-Type": "application/json"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        return WorkflowExecution.from_dict(response.json())

    @authenticated
    def get_workflow_execution_status_blocking(
            self, workflow_execution_id: UUID, organization_id: Optional[UUID] = None
    ) -> str:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/status?organization={organization_id}"
        headers = {**self.base_headers, "Content-Type": "text/event-stream"}
        response = requests.get(url=url, headers=headers)
        self.__assert_response_ok(response)
        # TODO: decode event stream format
        return response.content.decode(response.encoding)

    @authenticated
    def download_image(
            self,
            image_content_hash: str,
            image_name: str,
            organization_id: Optional[UUID] = None,
    ) -> bytes:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/image/{image_content_hash}/{image_name}?organization={organization_id}"
        response = requests.get(url=url, headers=self.base_headers)
        self.__assert_response_ok(response)
        return response.content

    @authenticated
    def download_result_blocking(
            self, workflow_execution_id: UUID, organization_id: Optional[UUID] = None
    ) -> bytes:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/result/default?organization={organization_id}"
        response = requests.get(url=url, headers=self.base_headers)
        self.__assert_response_ok(response)
        return response.content

    @authenticated
    def download_result(
            self, result_path: str, organization_id: Optional[UUID] = None
    ) -> bytes:
        assert result_path.startswith("/image/")
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}{result_path}?organization={organization_id}"
        response = requests.get(url=url, headers=self.base_headers)
        self.__assert_response_ok(response)
        return response.content

    @authenticated
    def retry_workflow_execution(
            self, workflow_execution_id: UUID, organization_id: Optional[UUID] = None
    ) -> int:
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/retry?organization={organization_id}"
        headers = {**self.base_headers, "Content-Type": "application/json"}
        return requests.post(url=url, headers=headers, data={}).status_code

    # ****** HIGH-LEVEL METHODS ******

    @authenticated
    def send_feedback(
            self,
            workflow_execution_id: UUID,
            thumbs_up: bool,
            expected_images_content_hashes: List[str] = [],
            organization_id: Optional[UUID] = None,
    ):
        organization_id = self._get_organization_id(organization_id)
        url = f"{self.api_config.BASE_API_URL_CURRENT}/workflow/execution/{workflow_execution_id}/feedback?organization={organization_id}"
        headers = {**self.base_headers, "Content-Type": "application/json"}
        payload = {
            "thumbsUp": thumbs_up,
            "expectedImages": expected_images_content_hashes,
        }
        response = requests.post(url=url, headers=headers, data=json.dumps(payload))
        self.__assert_response_ok(response)

    def process_image(
            self, image_path: str, workflow_id: UUID, output_dir: str
    ) -> bool:
        """upload image, start workflow, download result to `output_dir`"""
        execution_id = self.create_workflow_execution_for_image_file(
            workflow_id, image_path
        )
        while True:
            execution = self.get_workflow_execution_details(execution_id)
            if execution.status in ("COMPLETED", "FAILED"):
                break
            else:
                sleep(2.0)
        if execution.status == "FAILED":
            return False
        result = self.download_result(execution.resultPath)
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, os.path.split(image_path)[-1]), "wb") as f:
            f.write(result)
        return True

    # ****** HELPERS ******

    def process_batch(self, workflow_id: Union[str, UUID], image_dir: str, target_dir: str):
        """apply a workflow to a directory of images and download the results to `target_dir`"""
        image_paths = [
            *filter(
                lambda f: os.path.splitext(f)[-1] in {".jpeg", ".jpg", ".png"},
                os.listdir(image_dir),
            )
        ]
        executor = ThreadPoolExecutor(max_workers=min(200, len(image_paths)))
        futures_to_images = {}
        for path in image_paths:
            path = os.path.join(image_dir, path)
            future = executor.submit(
                self.process_image, self, path, workflow_id, target_dir
            )
            futures_to_images[future] = path
        for future in as_completed(futures_to_images):
            path = futures_to_images[future]
            success = future.result()
            if success:
                print(f"Processed {path} successfully")
            else:
                print(f"Execution failed for {path}")

    @staticmethod
    def __assert_response_ok(response):
        if response.status_code != 200 and response.status_code != 201:
            raise RuntimeError(
                f"API responded with Status Code {response.status_code}, reason: {response.reason}"
            )

    def _get_organization_id(self, passed_in_value):
        value = self.organization_id or passed_in_value
        if value is None:
            raise ValueError(
                "Expected `organization_id` to not be None."
                " Either set the client instance attribute "
                "or passed it as kwarg when calling a client's method."
            )
        return value
