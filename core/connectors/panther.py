import json
import requests


class Panther:
    token: str
    url: str
    timeout: int

    def __init__(self, url: str, token: str = None, timeout: int = 10):
        self.token = token
        self.url = url
        self.timeout = timeout

    def do_request(
            self,
            headers: dict = None,
            payload: [dict, str] = None,
            method: str = "GET",
    ):

        if headers is None:
            headers = {
                'User-Agent': 'SocketPythonScript/0.0.1',
                "accept": "application/json",
                'Content-Type': "application/json"
            }
            if self.token is not None:
                headers['Authorization'] = f"Bearer {self.token}"
        response = requests.request(
            method.upper(),
            self.url,
            headers=headers,
            data=payload,
            timeout=self.timeout
        )
        if response.status_code != 200:
            print("Failed to post data")
            print(response.text)
            result = None
        else:
            result = response.text
        return result

    def send(self, payload: str, headers: dict = None):
        response = self.do_request(
            method="POST",
            payload=payload,
            headers=headers
        )
        return response

