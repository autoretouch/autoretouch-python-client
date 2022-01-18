import time
import webbrowser

from autoretouch_api_client.client import AutoretouchClient, DEFAULT_USER_AGENT, DEFAULT_API_CONFIG
from autoretouch_api_client.model import ApiConfig, DeviceCodeResponse, AccessTokenResponse


class _DeviceAuthentication:
    def __init__(self, user_agent: str, api_config: ApiConfig):
        self.api = AutoretouchClient(user_agent=user_agent, api_config=api_config)

    def authenticate_and_get_refresh_token(self) -> str:
        device_code_response = self.api.get_device_code()
        self.__open_browser_for_verification(device_code_response)
        access_token_response = self.__wait_for_user_confirmation(device_code_response)
        return access_token_response.refresh_token

    @staticmethod
    def __open_browser_for_verification(device_code_response: DeviceCodeResponse):
        print(f"Open verification url {device_code_response.verification_uri_complete} in the browser "
              f"and confirm the user code '{device_code_response.user_code}'.")
        try:
            webbrowser.open(device_code_response.verification_uri_complete)
        except:
            print("Opening web browser failed")

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


def authenticate_device_and_get_refresh_token(user_agent: str = DEFAULT_USER_AGENT,
                                              api_config: ApiConfig = DEFAULT_API_CONFIG):
    return _DeviceAuthentication(user_agent, api_config).authenticate_and_get_refresh_token()
