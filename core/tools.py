from core.socket_reports.classes import IssueRecord
import csv
import json
import uuid
import hashlib


class Tools:

    @staticmethod
    def load_json(source):
        try:
            data = json.loads(source)
            is_error = False
        except Exception as error:
            is_error = True
            data = {
                "msg": f"Failed to process JSON data {source}",
                "error": error
            }
        return data, is_error

    @staticmethod
    def get_row_tuple(record: IssueRecord):
        return (
            record.id,
            record.repo,
            record.branch,
            record.pkg_type,
            record.pkg_name,
            record.pkg_version,
            record.issue_category,
            record.issue_type,
            record.pr_url,
            record.commit
        )

    @staticmethod
    def write_csv(csv_file: str, column_names: list, data: list):
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(column_names)
            for line in data:
                writer.writerow(Tools.get_row_tuple(line))

    @staticmethod
    def write_json(json_file: str, data: list):
        with open(json_file, 'w', newline='') as file:
            json.dump(data, file)

    @staticmethod
    def generate_uuid():
        new_uuid = str(uuid.uuid4())
        return new_uuid

    @staticmethod
    def generate_uuid_from_string(string: str) -> str:
        hex_string = hashlib.md5(string.encode("UTF-8")).hexdigest()
        return str(uuid.UUID(hex=hex_string))
