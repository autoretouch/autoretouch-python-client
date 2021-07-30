import requests

from typing import Tuple, Dict, List

from autoretouch_api_client.model import ApiConfig, Organization, Page, Workflow

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


def get_device_code() -> Tuple[str, str, str]:
    payload = f"client_id={apiConfig.CLIENT_ID}&scope={apiConfig.SCOPE}&audience={apiConfig.AUDIENCE}"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(f"{apiConfig.AUTH_DOMAIN}/oauth/device/code", headers=headers, data=payload)
    assert response.status_code == 200
    device_code = response.json().get("device_code")
    user_code = response.json().get("user_code")
    verification_url = response.json().get("verification_uri_complete")
    return device_code, user_code, verification_url


def get_access_and_refresh_token(device_code: str) -> Tuple[str, str, int]:
    payload = f"grant_type=urn:ietf:params:oauth:grant-type:device_code" \
              f"&device_code={device_code}" \
              f"&client_id={apiConfig.CLIENT_ID}"
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(f"{apiConfig.AUTH_DOMAIN}/oauth/token", headers=headers, data=payload)
    assert response.status_code == 200
    return response.json().get("access_token"), response.json().get("refresh_token"), response.json().get("expires_in")


def refresh_access_token(refresh_token: str) -> str:
    pass


def revoke_access_token(refresh_token: str) -> str:
    pass


def get_organizations(access_token: str) -> List[Organization]:
    headers = {"Authorization": f"Bearer {access_token}", "content-type": "json"}
    response = requests.get(f"{apiConfig.BASE_API_URL_CURRENT}/organization?limit=50&offset=0", headers=headers)
    assert response.status_code == 200
    page = Page(**response.json())
    organizations = [Organization(**entry) for entry in page.entries]
    return organizations


def get_workflows(access_token: str) -> List[Workflow]:
    headers = {"Authorization": f"Bearer {access_token}", "content-type": "json"}
    response = requests.get(f"{apiConfig.BASE_API_URL_CURRENT}/workflow?limit=50&offset=0", headers=headers)
    assert response.status_code == 200
    page = Page(**response.json())
    workflows = [Workflow(**entry) for entry in page.entries]
    return workflows
