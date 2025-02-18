import json
import hashlib
import hmac
import base64
import requests
from datetime import datetime, timezone

from socketsync.classes import IssueRecord

default_log_type = 'SocketSiemConnector'


class Sentinel:
    def __init__(self, workspace_id: str, shared_key: str):
        """
        Initializes the Microsoft Sentinel client with credentials and HTTP source URL.

        :param workspace_id: The Microsoft Sentinel Customer ID
        :param shared_key: The Microsoft Sentinel Shared Key
        :param log_type: The Microsoft Sentinel Log Type
        """
        self.workspace_id = workspace_id
        self.shared_key = shared_key
        self.uri = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

    def _generate_signature(self, content_length: int, date: str) -> str:
        """
        Generates the HMAC SHA256 signature required for authentication.

        :param content_length: Length of the request body
        :param date: Current date in RFC 1123 format
        :return: Authorization signature string
        """
        method = 'POST'
        content_type = 'application/json'
        resource = '/api/logs'
        x_headers = f"x-ms-date:{date}"
        string_to_hash = f"{method}\n{content_length}\n{content_type}\n{x_headers}\n{resource}"
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")

        decoded_key = base64.b64decode(self.shared_key)
        hashed_string = hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(hashed_string).decode()

        return f"SharedKey {self.workspace_id}:{signature}"

    def send_events(self, events: list, log_type: str = default_log_type) -> list:
        """
        Sends a single event to Microsoft Sentinel.

        :param events: Dictionary representing the event data
        :param log_type:
        :return: Response from the Sentinel API
        """
        errors = []
        for event in events:
            response = self.send_event(event, log_type)
            if response["status_code"] != 200:
                errors.append(response)
        return errors

    def send_event(self, event_data: dict, log_type: str = default_log_type) -> dict:
        """
        Sends a batch of events to a logging endpoint. This function serializes a
        list of events into JSON format, computes the necessary authorization
        headers, and sends them via an HTTP POST request to the configured logging
        endpoint.

        :param event_data: An event that is serialized to JSON
            and sent to the logging endpoint.
        :type event_data: dict
        :param log_type: The type of log under which the events should be
            categorized. Defaults to the class's `default_log_type`.
        :type log_type: str, optional
        :return: A dictionary with the HTTP response status code and response text
            from the logging endpoint.
        :rtype: dict
        """
        body = json.dumps(Sentinel.transform_socket_alerts(event_data))
        content_length = len(body)
        rfc1123date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        authorization = self._generate_signature(content_length, rfc1123date)

        headers = {
            "Content-Type": "application/json",
            "Authorization": authorization,
            "Log-Type": log_type,
            "x-ms-date": rfc1123date
        }

        response = requests.post(self.uri, data=body, headers=headers)
        return {
            "status_code": response.status_code,
            "response_text": response.text
        }

    @staticmethod
    def transform_socket_alerts(event: IssueRecord) -> dict:
        """Transforms a Gosec security event into the correct Sentinel schema."""
        status = "Unknown"
        if event.action.lower() == 'block' or event.action.lower() == 'fail':
            status = "Fail"
        if event.action.lower() == 'warn':
            status = "Warning"
        new_event = {
            "TimeGenerated": event.created_at,
            "SourceComputerId": "socket-siem-connector",
            "Computer": "socket-siem-connector",
            "StartTime": event.created_at,
            "EndTime": event.created_at,
            "OperationStatus": status,
        }
        return {**new_event, **event.__dict__}
