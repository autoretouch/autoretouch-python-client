import json
import os.path
import time
import webbrowser
from datetime import datetime
from typing import Optional
import logging

from api_client.model import Credentials, DeviceCodeResponse

__all__ = [
    "Authenticator"
]


def _open_browser_for_verification(device_code_response: DeviceCodeResponse):
    logging.info(
        f"Open verification url {device_code_response.verification_uri_complete} in the browser "
        f"and confirm the user code '{device_code_response.user_code}'."
    )
    try:
        webbrowser.open(device_code_response.verification_uri_complete)
    except Exception as e:
        logging.error("Failed to open the browser. Exception was :")
        logging.error(str(e))


def _poll_credentials_while_user_confirm(
    api: "AutoRetouchAPIClient", device_code_response: DeviceCodeResponse
) -> Credentials:
    seconds_waited = 0
    logging.info("Waiting for user confirmation...")
    while seconds_waited < device_code_response.expires_in:
        try:
            return api.get_credentials_from_device_code(
                device_code_response.device_code
            )
        except:
            seconds_waited += device_code_response.interval
            time.sleep(device_code_response.interval)
    raise RuntimeError(f"Device Code not confirmed after {seconds_waited} seconds")


class Authenticator:
    def __init__(
        self,
        api: "AutoRetouchAPIClient",
        credentials_path: Optional[str] = None,
        refresh_token: Optional[str] = None,
        save_credentials: bool = True,
    ):
        self.api: "AutoRetouchAPIClient" = api
        self.credentials_path: str = credentials_path
        self.refresh_token: str = refresh_token
        self.save_credentials: bool = save_credentials
        self.credentials: Optional[Credentials] = None

    def authenticate(self):
        if self.refresh_token is not None:
            self.credentials = self.api.get_credentials_from_refresh_token(
                self.refresh_token
            )
        elif self.credentials_path is not None and os.path.isfile(self.credentials_path):
            self.credentials = self._read_credentials_file()
            self.refresh_credentials()
        else:
            device_code_response = self.api.get_device_code()
            _open_browser_for_verification(device_code_response)
            self.credentials = _poll_credentials_while_user_confirm(
                self.api, device_code_response
            )
        if self.save_credentials:
            if not self.credentials_path:
                self.credentials_path = AR_CREDENTIALS
            self._save_credentials()
        logging.info("Login was successful")
        return self

    @property
    def access_token(self):
        return self.credentials.access_token

    @property
    def token_expired(self) -> bool:
        now = int(datetime.utcnow().timestamp())
        return now + 30 > self.credentials.expires_at

    def refresh_credentials(self):
        self.credentials = self.api.get_credentials_from_refresh_token(
            refresh_token=self.credentials.refresh_token
        )
        return self

    def revoke_refresh_token(self) -> int:
        return self.api.revoke_refresh_token(self.credentials.refresh_token)

    def _refresh_credentials_if_expired(self):
        if not self.credentials.access_token or self.token_expired:
            logging.info("access token expired, refreshing ...")
            self.refresh_credentials()

    def _read_credentials_file(self) -> Credentials:
        with open(self.credentials_path, "r") as credentials_file:
            return Credentials(**json.load(credentials_file))

    def _save_credentials(self):
        if not os.path.exists(os.path.dirname(self.credentials_path)):
            os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
        with open(self.credentials_path, "w") as credentials_file:
            json.dump(
                self.credentials,
                credentials_file,
                default=lambda o: o.__dict__,
                indent=4,
            )
