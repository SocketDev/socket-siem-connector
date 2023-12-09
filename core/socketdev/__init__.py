import logging
import requests
import base64
from core.socketdev.dependencies import Dependencies
from core.socketdev.npm import NPM
from core.socketdev.openapi import OpenAPI
from core.socketdev.org import Orgs
from core.socketdev.quota import Quota
from core.socketdev.report import Report
from core.socketdev.repositories import Repositories
from core.socketdev.settings import Settings
from core.socketdev.socket_classes import Response
from core.socketdev.exceptions import APIKeyMissing, APIFailure, APIAccessDenied, APIInsufficientQuota, APIResourceNotFound


__author__ = 'socket.dev'
__version__ = '0.0.1'
__all__ = [
    "SocketDev",
]


global encoded_key
api_url = "https://api.socket.dev/v0"
timeout = 30
log = logging.getLogger("socketdev")
log.addHandler(logging.NullHandler())


def encode_key(token: str):
    global encoded_key
    encoded_key = base64.b64encode(token.encode()).decode('ascii')


def do_request(
        path: str,
        headers: dict = None,
        payload: [dict, str] = None,
        files: list = None,
        method: str = "GET",
):
    if encoded_key is None or encoded_key == "":
        raise APIKeyMissing

    if headers is None:
        headers = {
            'Authorization': f"Basic {encoded_key}",
            'User-Agent': 'SocketPythonScript/0.0.1',
            "accept": "application/json"
        }
    url = f"{api_url}/{path}"
    try:
        response = requests.request(
            method.upper(),
            url,
            headers=headers,
            data=payload,
            files=files,
            timeout=timeout
        )
        if response.status_code >= 400:
            raise APIFailure("Bad Request")
        elif response.status_code == 401:
            raise APIAccessDenied("Unauthorized")
        elif response.status_code == 403:
            raise APIInsufficientQuota("Insufficient max_quota for API method")
        elif response.status_code == 404:
            raise APIResourceNotFound(f"Path not found {path}")
        elif response.status_code == 429:
            raise APIInsufficientQuota("Insufficient quota for API route")
    except Exception as error:
        result = Response(
            text=f"{error}",
            error=True,
            status_code=500,
            url=url
        )
        raise APIFailure(result)
    return response


class SocketDev:
    token: str
    base_api_url: str
    request_timeout: int
    dependencies: Dependencies
    npm: NPM
    openapi: OpenAPI
    org: Orgs
    quota: Quota
    report: Report
    repositories: Repositories
    settings: Settings

    def __init__(self, token: str, base_api_url=None, request_timeout=None):
        self.token = token + ":"
        encode_key(self.token)
        self.base_api_url = base_api_url
        if self.base_api_url is not None:
            SocketDev.set_api_url(self.base_api_url)
        self.request_timeout = request_timeout
        if self.request_timeout is not None:
            SocketDev.set_timeout(self.request_timeout)
        self.dependencies = Dependencies()
        self.npm = NPM()
        self.openapi = OpenAPI()
        self.org = Orgs()
        self.quota = Quota()
        self.report = Report()
        self.repositories = Repositories()
        self.settings = Settings()

    @staticmethod
    def set_api_url(base_url: str):
        global api_url
        api_url = base_url

    @staticmethod
    def set_timeout(request_timeout: int):
        global timeout
        timeout = request_timeout
