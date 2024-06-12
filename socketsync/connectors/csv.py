import json
import csv
from socketsync.classes import IssueRecord
from socketsync import columns as default_columns


class CSV:
    file: str
    columns: list

    def __init__(self, file: str, columns: list = None):
        self.file = file
        self.columns = columns
        if self.columns is None:
            self.columns = default_columns

    def write_csv(self, data: list):
        with open(self.file, 'w', newline='') as file:
            writer = csv.writer(file)
            if self.columns is not None:
                writer.writerow(self.columns)
            for issue in data:
                writer.writerow(self.create_row(issue))

    def create_row(self, issue: IssueRecord) -> tuple:
        row = ()
        if self.columns is not None:
            for column in self.columns:
                value = getattr(issue, column)
                row += (value,)
        else:
            data = json.loads(str(issue))
            for value in data:
                row += (value,)
        return row
