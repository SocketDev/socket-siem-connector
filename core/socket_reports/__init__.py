import logging
from core.tools import Tools
from core.socketdev import SocketDev
from core.socketdev.exceptions import APIFailure
from core.sqlite import SqliteDB
from core.socket_reports.classes import Report, IssueRecord
import random
from typing import Union
from core import columns
from datetime import datetime


socket: SocketDev


class Reports:
    org: str
    column_names: list
    api_key: str
    owner: str

    def __init__(self, org: str, api_key: str, start_date: str = None):
        self.base_url = f"https://socket.dev/dashboard/org/gh/{org}/reports?"
        self.log = logging.getLogger('socket_reports')
        self.log.addHandler(logging.NullHandler())
        self.column_names = columns
        self.start_date = start_date
        self.owner = org
        self.date_format = "%Y-%m-%d"
        self.socket_date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.db = SqliteDB(column_names=self.column_names)
        global socket
        socket = SocketDev(
            token=api_key
        )

    def check_if_reports_exist(self, reports: list) -> list:
        new_reports = []
        for report in reports:
            report_exists = self.db.check_for_report(report)
            if not report_exists:
                new_reports.append(report)
        return new_reports

    def get_report_list(self) -> list:
        data = socket.report.list()
        reports = []
        for report in data:
            socket_report = Report(**report)
            socket_report.owner = self.owner
            reports.append(socket_report)
        result = self.check_if_reports_exist(reports)
        return result

    def get_issues(self):
        report_list = self.get_report_list()
        issues = []
        for report in report_list:
            report: Report
            collect_report = self.check_collect_status(report)
            if collect_report:
                print(f"Processing report {report.id}")
                issue_data, processed = self.process_report(
                    report,
                    issues
                )
                if processed:
                    self.update_report_state(report)
        return issues

    def check_collect_status(self, report: Report) -> bool:
        collect_report = False
        if self.start_date is not None:
            start_date = datetime.strptime(self.start_date, self.date_format)
            created_at = datetime.strptime(
                report.created_at,
                self.socket_date_format
            )
            if created_at >= start_date:
                collect_report = True
        else:
            collect_report = True
        return collect_report

    @staticmethod
    def pull_report(
            record_id: str,
            report_url,
            max_retry=1
    ):
        retry = 0
        report_json = None
        while retry != max_retry:
            try:
                report_json = socket.report.view(record_id)
            except APIFailure:
                print(f"Failed to pull report {report_url}")
            retry += 1
        return report_json

    @staticmethod
    def create_github_urls(record: Report) -> (Union[str, None], Union[str, None]):
        pr_url = ""
        commit_urls = ""
        github_base = f"https://github.com/{record.owner}/{record.repo}"
        for pr in record.pull_requests:
            pr_url += f"{github_base}/pull/{pr}\n"
            commit_urls += f"{github_base}/pull/{pr}/commits/{record.commit}\n"
        commit_urls = commit_urls.strip()
        pr_url = pr_url.strip()
        if commit_urls == "":
            commit_urls = None
        if pr_url == "":
            pr_url = None
        return pr_url, commit_urls

    @staticmethod
    def get_detected_packages(packages: list, locations: list):
        for item in locations:
            pkg_type = item.get("type")
            item_value = item.get("value")
            if item_value is not None:
                pkg_name = item_value.get("package")
                pkg_version = item_value.get("version")
                pkg_data = (pkg_type, pkg_name, pkg_version)
                if pkg_data not in packages:
                    packages.append(pkg_data)
        return packages

    @staticmethod
    def process_issues(
            record: Report,
            issue: dict,
            records: list,
            pr_urls: str,
            commit_urls: str
    ) -> list:
        issue_type = issue.get("type")
        values = issue.get("value")
        locations = values.get("locations")
        issue_severity = values.get("severity")
        issue_category = values.get("category")
        detected_pkgs = Reports.get_detected_packages(list(), locations)
        for package in detected_pkgs:
            (pkg_type, pkg_name, pkg_version) = package
            issue_id_values = [
                record.id,
                record.owner,
                record.repo,
                record.branch,
                pkg_type,
                pkg_name,
                pkg_version,
                issue_type,
                issue_severity,
                issue_category,
                pr_urls,
                record.commit,
                commit_urls,
                record.created_at,
                str(random.randint(0, 5000))
            ]
            issue_id_str = ":".join(issue_id_values)
            issue_id = Tools.generate_uuid_from_string(issue_id_str)
            record_result = IssueRecord(
                id=issue_id,
                report_id=record.id,
                owner=record.owner,
                repo=record.repo,
                branch=record.branch,
                pkg_type=pkg_type,
                pkg_name=pkg_name,
                pkg_version=pkg_version,
                issue_category=issue_category,
                issue_type=issue_type,
                issue_severity=issue_severity,
                pr_url=pr_urls,
                commit=record.commit,
                commit_url=commit_urls,
                created_at=record.created_at.strip(" (Coordinated Universal Time)")
            )
            records.append(record_result)

        return records

    @staticmethod
    def process_report(
            record: Report,
            records: list
    ) -> (list, bool):
        report_json = Reports.pull_report(
            record.id,
            record.url
        )
        if report_json is None:
            return records, False
        issues = report_json.get("issues")
        pr_urls, commit_urls = Reports.create_github_urls(record)
        for issue in issues:
            records = Reports.process_issues(
                pr_urls=pr_urls,
                commit_urls=commit_urls,
                record=record,
                records=records,
                issue=issue
            )
        return records, True

    def update_report_state(self, report: Report, processed: bool = True) -> None:
        self.db.update_report_state(report, processed)
