import json


class IssueRecord:
    id: str
    owner: str
    repo: str
    branch: str
    pkg_type: str
    pkg_name: str
    pkg_version: str
    issue_category: str
    issue_type: str
    issue_severity: str
    pr_url: str
    commit: str
    created_at: str
    commit_url: str

    def __init__(self, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

        if hasattr(self, "created_at"):
            self.created_at = self.created_at.strip(" (Coordinated Universal Time)")

    def __str__(self):
        return json.dumps(self.__dict__)


class Report:
    branch: str
    commit: str
    id: str
    pull_requests: list
    url: str
    repo: str
    processed: bool
    owner: str
    created_at: str

    def __init__(self, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
        if not hasattr(self, "processed"):
            self.processed = False
        if hasattr(self, "pull_requests"):
            self.pull_requests = json.loads(str(self.pull_requests))

    def __str__(self):
        return json.dumps(self.__dict__)
