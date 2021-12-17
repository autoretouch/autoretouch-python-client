from enum import Enum
from typing import List, Dict, Optional
from uuid import UUID


class ApiConfig:
    def __init__(self, BASE_API_URL: str, BASE_API_URL_CURRENT: str, CLIENT_ID: str, SCOPE: str, AUDIENCE: str, AUTH_DOMAIN: str):
        self.BASE_API_URL = BASE_API_URL
        self.BASE_API_URL_CURRENT = BASE_API_URL_CURRENT
        self.CLIENT_ID = CLIENT_ID
        self.SCOPE = SCOPE
        self.AUDIENCE = AUDIENCE
        self.AUTH_DOMAIN = AUTH_DOMAIN


class DeviceCodeResponse:
    def __init__(self, device_code: str, user_code: str, verification_uri_complete: str, expires_in: int, interval: int, **kwargs):
        self.device_code = device_code
        self.user_code = user_code
        self.verification_uri_complete = verification_uri_complete
        self.expires_in = expires_in
        self.interval = interval


class AccessTokenResponse:
    def __init__(self, access_token: str, refresh_token: str, scope: str, expires_in: int, token_type: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.expires_in = expires_in
        self.token_type = token_type


class Credentials:
    def __init__(self, access_token: str, refresh_token: str, scope: str, expires: str, token_type: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.expires = expires
        self.token_type = token_type


class Page:
    def __init__(self, entries: List, total: int):
        self.entries = entries
        self.total = total


class Organization:
    def __init__(self, **kwargs):
        self.id: UUID = UUID(kwargs.get("id"))
        self.version: UUID = UUID(kwargs.get("version"))
        self.name: str = kwargs.get("name")
        self.members: List = kwargs.get("members")

    def __repr__(self):
        return f"Organization {self.__dict__}"


class Workflow:
    def __init__(self, **kwargs):
        self.id: UUID = UUID(kwargs.get("id"))
        self.version: UUID = UUID(kwargs.get("version"))
        self.name: str = kwargs.get("name")
        self.date: str = kwargs.get("date")
        self.author: Dict = kwargs.get("author")
        self.workflowComponents: List = kwargs.get("workflowComponents")
        self.executionPrice: int = kwargs.get("executionPrice")

    def __repr__(self):
        return f"Workflow {self.__dict__}"


class WorkflowExecution:
    def __init__(self, **kwargs):
        self.id: UUID = UUID(kwargs.get("id"))
        self.workflow: UUID = UUID(kwargs.get("workflow"))
        self.workflowVersion: UUID = UUID(kwargs.get("workflowVersion"))
        self.workflowName: str = kwargs.get("workflowName")
        self.organizationId: UUID = UUID(kwargs.get("organizationId"))
        self.status: str = kwargs.get("status")
        self.userId: str = kwargs.get("userId")
        self.createdAt: str = kwargs.get("createdAt")
        self.startedAt: Optional[str] = kwargs.get("startedAt")
        self.finishedAt: Optional[str] = kwargs.get("finishedAt")
        self.inputFileName: str = kwargs.get("inputFileName")
        self.inputContentHash: str = kwargs.get("inputContentHash")
        self.resultContentHash: Optional[str] = kwargs.get("resultContentHash")
        self.resultContentType: Optional[str] = kwargs.get("resultContentType")
        self.resultFileName: Optional[str] = kwargs.get("resultFileName")
        self.resultPath: Optional[str] = kwargs.get("resultPath")
        self.labels: Dict[str, str] = kwargs.get("labels")
        self.chargedCredits: int = kwargs.get("chargedCredits")

    def __repr__(self):
        return f"Workflow Execution {self.__dict__}"
