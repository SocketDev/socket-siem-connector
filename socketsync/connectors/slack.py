import json
import urllib.parse
import requests
import urllib
from socketsync.classes import IssueRecord
from socketsync import log
from socketsync import default_headers
from slack_sdk.webhook import WebhookClient


class Slack:
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
            method: str = "POST",
            params: dict = None,
            timeout: int = 10
    ):
        self.headers = headers
        if self.headers is None:
            self.headers = default_headers
        else:
            for key in default_headers:
                if key not in headers:
                    headers[key] = default_headers[key]
        self.method = method
        self.params = params
        self.timeout = timeout
        self.url = url

    def send(self, payload: dict):
        url = self.create_url(self.url, self.params)
        webhook = WebhookClient(url)
        blocks = Slack.generate_slack_body(payload)
        try:
            response = webhook.send(blocks=blocks)
            sent = True
        except Exception as error:
            log.error("Unable to send slack webhook")
            log.error(error)
            sent = False
        return sent

    @staticmethod
    def create_url(url: str, params: dict) -> str:
        if params is not None:
            query_params = urllib.parse.urlencode(params)
            url = f"{url}?{query_params}"
        return url

    @staticmethod
    def generate_slack_body(data: dict) -> list:
        issue = IssueRecord(**data)
        slack_title = f"Issue detected in {issue.owner}/{issue.repo}"
        if issue.pr != "0":
            slack_title += f" PR #{issue.pr}"

        title_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": slack_title
            }
        }
        purl = f"{issue.pkg_type}/{issue.pkg_name}@{issue.pkg_version}"
        description = f"*{issue.title}* <{issue.pkg_url}|{purl}>"
        introduced_by = []
        for name, source in issue.introduced_by:
            line = f"{name} in {source}"
            introduced_by.append(line)
        description += f" - introduced_by: {introduced_by}"
        description_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": description
            }

        }
        blocks = [
            title_block,
            description_block
        ]
        return blocks
