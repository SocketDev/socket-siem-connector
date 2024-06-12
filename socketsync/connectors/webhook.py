import json
import urllib.parse

import requests
import urllib


class Webhook:
    headers: dict
    method: str
    params: dict
    auth_headers: dict
    timeout: int
    url: str

    def __init__(
            self,
            url: str,
            headers: dict = None,
            auth_headers: dict = None,
            method: str = "POST",
            params: dict = None,
            timeout: int = 10
    ):
        self.headers = headers
        self.auth_headers = auth_headers
        self.method = method
        self.params = params
        self.timeout = timeout
        self.url = url

    def send(self, payload: dict):
        headers = self.get_headers()
        url = self.create_url(self.url, self.params)
        data = json.dumps(payload)
        response = requests.request(
            self.method.upper(),
            url,
            headers=headers,
            data=data,
            timeout=self.timeout
        )
        if response.status_code != 200:
            print("Failed to post data")
            print(response.text)
            result = None
        else:
            result = response.text
        return result

    @staticmethod
    def create_url(url: str, params: dict) -> str:
        if params is not None:
            query_params = urllib.parse.urlencode(params)
            url = f"{url}?{query_params}"
        return url

    def get_headers(self):
        headers = {
            'User-Agent': 'SocketPythonScript/0.0.1',
            "accept": "application/json",
            'Content-Type': "application/json"
        }
        if self.headers is None and self.auth_headers is not None:
            for name in self.auth_headers:
                headers[name] = self.auth_headers[name]
        elif self.headers is not None:
            headers = self.headers
        return headers
