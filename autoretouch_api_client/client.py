import json
from uuid import UUID

import requests

from typing import Tuple, Dict, List

from autoretouch_api_client.model import (
    ApiConfig, Organization, Page, Workflow, DeviceCodeResponse, AccessTokenResponse)

configDev = ApiConfig(
    BASE_API_URL="https://api.dev.autoretouch.com",
    BASE_API_URL_CURRENT="https://api.dev.autoretouch.com/v1",
    CLIENT_ID="DtLZblh4cfQdNc1iNXNV2JXy4zFL6qCM",
    SCOPE="offline_access",
    AUDIENCE="https://api.dev.autoretouch.com/",
    AUTH_DOMAIN="https://dev-autoretouch.eu.auth0.com"
)
configProd = ApiConfig(
    BASE_API_URL="https://api.autoretouch.com",
    BASE_API_URL_CURRENT="https://api.autoretouch.com/v1",
    CLIENT_ID="V8EkfbxtBi93cAySTVWAecEum4d6pt4J",
    SCOPE="offline_access",
    AUDIENCE="https://api.autoretouch.com",
    AUTH_DOMAIN="https://auth.autoretouch.com"
)
apiConfig = configDev


def get_api_status() -> int:
    return requests.get(f"{apiConfig.BASE_API_URL}/health").status_code


def get_api_status_current() -> int:
    return requests.get(f"{apiConfig.BASE_API_URL_CURRENT}/health").status_code


def get_device_code() -> DeviceCodeResponse:
    url = f"{apiConfig.AUTH_DOMAIN}/oauth/device/code"
    payload = f"client_id={apiConfig.CLIENT_ID}&scope={apiConfig.SCOPE}&audience={apiConfig.AUDIENCE}"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(url=url, headers=headers, data=payload)
    assert response.status_code == 200
    return DeviceCodeResponse(**response.json())


def get_access_and_refresh_token(device_code: str) -> AccessTokenResponse:
    url = f"{apiConfig.AUTH_DOMAIN}/oauth/token"
    payload = f"grant_type=urn:ietf:params:oauth:grant-type:device_code" \
              f"&device_code={device_code}" \
              f"&client_id={apiConfig.CLIENT_ID}"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(url=url, headers=headers, data=payload)
    assert response.status_code == 200
    return AccessTokenResponse(**response.json())


def refresh_access_token(refresh_token: str) -> AccessTokenResponse:
    url = f"{apiConfig.AUTH_DOMAIN}/oauth/token"
    payload = f"grant_type=refresh_token" \
              f"&refresh_token={refresh_token}" \
              f"&client_id={apiConfig.CLIENT_ID}"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(url=url, headers=headers, data=payload)
    assert response.status_code == 200
    return AccessTokenResponse(**response.json(), refresh_token=refresh_token)


def revoke_access_token(refresh_token: str) -> str:
    pass  # TODO


def get_organizations(access_token: str) -> List[Organization]:
    url = f"{apiConfig.BASE_API_URL_CURRENT}/organization?limit=50&offset=0"
    headers = {"Authorization": f"Bearer {access_token}", "content-type": "json"}
    response = requests.get(url=url, headers=headers)
    assert response.status_code == 200
    page = Page(**response.json())
    organizations = [Organization(**entry) for entry in page.entries]
    return organizations


def get_workflows(access_token: str) -> List[Workflow]:
    url = f"{apiConfig.BASE_API_URL_CURRENT}/workflow?limit=50&offset=0"
    headers = {"Authorization": f"Bearer {access_token}", "content-type": "json"}
    response = requests.get(url=url, headers=headers)
    assert response.status_code == 200
    page = Page(**response.json())
    workflows = [Workflow(**entry) for entry in page.entries]
    return workflows


def upload_image(access_token: str, filename: str, mimetype: str, organization_id: UUID, filepath: str) -> str:
    url = f"{apiConfig.BASE_API_URL_CURRENT}/upload?organization={organization_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    files = [('file', (filename, open(filepath, 'rb'), mimetype))]

    response = requests.post(url=url, headers=headers, files=files)
    assert response.status_code == 201
    return response.content.decode(response.encoding)


def create_workflow_execution_for_image_reference(
        access_token: str, workflow_id: UUID, workflow_version_id: UUID, organization_id: UUID,
        image_content_hash: str, image_name: str, mimetype: str, labels: Dict[str, str]) -> str:
    url = f"{apiConfig.BASE_API_URL_CURRENT}/workflow/execution/create" \
          f"?workflow={workflow_id}" \
          f"&version={workflow_version_id}" \
          f"&organization={organization_id}"
    headers = {"Authorization": f"Bearer {access_token}", "content-type": "application/json"}
    payload = {
        "image": {
            "name": image_name,
            "contentHash": image_content_hash,
            "contentType": mimetype
        },
        #"labels": labels
    }

    response = requests.post(url=url, headers=headers, data=json.dumps(payload))
    assert response.status_code == 201
    return response.content.decode(response.encoding)
