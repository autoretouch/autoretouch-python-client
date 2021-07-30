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


class Page:
    def __init__(self, entries: List, total: int):
        self.entries = entries
        self.total = total


class Organization:
    def __init__(self, **kwargs):
        self.id: UUID = kwargs.get("id")
        self.version: UUID = kwargs.get("version")
        self.name: str = kwargs.get("name")
        self.members: List = kwargs.get("members")

    def __repr__(self):
        return f"Organization {self.__dict__}"


class Workflow:
    def __init__(self, **kwargs):
        self.id: UUID = kwargs.get("id")
        self.version: UUID = kwargs.get("version")
        self.name: str = kwargs.get("name")
        self.date: str = kwargs.get("date")
        self.author: Dict = kwargs.get("author")
        self.workflowComponents: List = kwargs.get("workflowComponents")
        self.executionPrice: int = kwargs.get("executionPrice")

    def __repr__(self):
        return f"Workflow {self.__dict__}"


class WorkflowExecution:
    def __init__(self, **kwargs):
        self.id: UUID = kwargs.get("id")
        self.workflow: UUID = kwargs.get("workflow")
        self.workflowVersion: UUID = kwargs.get("workflowVersion")
        self.workflowName: str = kwargs.get("workflowName")
        self.organizationId: UUID = kwargs.get("organizationId")
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
