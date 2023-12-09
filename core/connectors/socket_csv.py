import json
import csv
from core.socket_reports.classes import IssueRecord


class SocketCSV:
    file: str
    columns: list

    def __init__(self, file: str, columns: list = None):
        self.file = file
        self.columns = columns

    def write_csv(self, data: list):
        with open(self.file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.columns)
            for issue in data:
                writer.writerow(self.create_row(issue))

    def create_row(self, issue: IssueRecord) -> tuple:
        row = ()
        for column in self.columns:
            value = getattr(issue, column)
            row += (value,)
        return row
