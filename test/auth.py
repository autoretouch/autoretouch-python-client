import json
import time
import datetime
import webbrowser
from typing import Dict

from autoretouch_api_client.client import get_device_code, get_access_and_refresh_token, refresh_access_token
from autoretouch_api_client.model import DeviceCodeResponse, AccessTokenResponse


def create_or_get_credentials() -> str:
    try:
        with open("../tmp/credentials.json", "r") as credentials_file:
            credentials = json.load(credentials_file)
        if __token_expired(credentials["expires"]):
            refresh_response = refresh_access_token(credentials["refresh_token"])
            credentials = __to_dict(refresh_response)
            with open("../tmp/credentials.json", "w") as credentials_file:
                json.dump(credentials, credentials_file, indent=4)
        return credentials["access_token"]
    except FileNotFoundError:
        access_token_response = __create_credentials()
        credentials = __to_dict(access_token_response)
        with open("../tmp/credentials.json", "w") as credentials_file:
            json.dump(credentials, credentials_file, indent=4)
        return credentials["access_token"]


def __create_credentials() -> AccessTokenResponse:
    device_code_response = get_device_code()
    print(f"Open verification_url in the browser and confirm the user code '{device_code_response.user_code}'.")
    __open_browser_for_verification(device_code_response)
    return __wait_for_user_confirmation(device_code_response)


def __to_dict(access_token_response: AccessTokenResponse) -> Dict:
    return {
        "access_token": access_token_response.access_token,
        "refresh_token": access_token_response.refresh_token,
        "scope": access_token_response.scope,
        "token_type": access_token_response.token_type,
        "expires": __get_expiration_isostring(access_token_response.expires_in)
    }


def __open_browser_for_verification(device_code_response: DeviceCodeResponse):
    try:
        webbrowser.open(device_code_response.verification_uri_complete)
    except:
        print("Opening web browser failed")


def __wait_for_user_confirmation(device_code_response: DeviceCodeResponse) -> AccessTokenResponse:
    seconds_waited = 0
    while seconds_waited < device_code_response.expires_in:
        print("Waiting for user confirmation...")
        try:
            return get_access_and_refresh_token(device_code_response.device_code)
        except:
            seconds_waited += device_code_response.interval
            time.sleep(device_code_response.interval)
    raise RuntimeError(f"Device Code not confirmed after {seconds_waited} seconds")


def __get_expiration_isostring(expires_in: int) -> str:
    now = int(datetime.datetime.utcnow().timestamp())
    expiration_timestamp = now + expires_in
    return datetime.datetime.fromtimestamp(expiration_timestamp).isoformat()


def __token_expired(expiration_isostring: str) -> bool:
    expiration_timestamp = datetime.datetime.fromisoformat(expiration_isostring).timestamp()
    now = int(datetime.datetime.utcnow().timestamp())
    return now + 30 > expiration_timestamp
