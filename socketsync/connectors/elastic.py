import json
from elasticsearch import Elasticsearch
from socketsync.classes import IssueRecord


class Elastic:
    def __init__(self, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
        self.es = self.load_client()

    def __str__(self):
        return json.dumps(self.__dict__)

    def load_client(self) -> Elasticsearch:
        es = Elasticsearch(**self.__dict__)
        return es

    def add_document(self, issue: IssueRecord, index: str):
        issue_json = json.loads(str(issue))
        self.es.index(
            index=index,
            id=issue.id,
            document=issue_json
        )
