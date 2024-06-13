import json
from google.cloud import bigquery


class BigQuery:
    client: bigquery.Client
    table: str

    def __init__(self, table: str):
        try:
            self.client = bigquery.Client()
        except EnvironmentError:
            print(
                "Google Project not set try setting with 'gcloud config set project'"
            )
            exit(1)
        self.table = table

    def add_dataset(self, issues: list, streaming=True):
        if streaming:
            result = self.add_streaming(issues)
        else:
            result = self.add_query(issues)
        return result

    def add_streaming(self, issues: list):
        table_rows = []
        for issue in issues:
            issue_json = json.loads(str(issue))
            table_rows.append(issue_json)
        try:
            errors = self.client.insert_rows_json(self.table, table_rows)
            return errors
        except Exception as error:
            print(error)
            exit(1)

    def add_query(self, issues: list):
        columns = []
        values = []
        for issue in issues:
            issue_json = json.loads(str(issue))
            if len(columns) == 0:
                for key in issue_json.keys():
                    columns.append(key)
            row = []
            for key in issue_json:
                row.append(issue_json[key])
            values.append(row)
        column_str = ", ".join(columns)
        query = f"""
        INSERT INTO `{self.table}` ({column_str}) VALUES 
        """
        for value in values:
            value_str = ""
            for item in value:
                value_str += f"'{item}', "
            value_str = value_str.rstrip(", ")
            query += f"({value_str}),"
        query = query.rstrip(",")
        try:
            results = self.client.query(query)
            return results
        except Exception as error:
            print(error)
            exit(1)
