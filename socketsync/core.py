from datetime import datetime
import logging
import sys
import requests
import base64
import json
from socketsync.exceptions import (
    APIFailure, APIKeyMissing, APIAccessDenied, APIInsufficientQuota, APIResourceNotFound, APICloudflareError
)
from socketsync.issues import AllIssues
from socketsync.licenses import Licenses
from socketsync import __version__, default_headers
from socketsync.classes import (
    Report,
    IssueRecord,
    Package,
    Alert,
    Purl
)

global encoded_key
api_url = "https://api.socket.dev/v0"
timeout = 30
full_scan_path = ""
repository_path = ""
all_issues = AllIssues()
org_id = None
org_slug = None
all_new_alerts = False
default_branch_names = [
        "master",
        "main"
    ]
default_only = False
security_policy = {}
licenses = Licenses()
date_format = "%Y-%m-%d %H:%M"
socket_date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

log = logging.getLogger("socketdev")
log.addHandler(logging.NullHandler())


def encode_key(token: str) -> None:
    """
    encode_key takes passed token string and does a base64 encoding. It sets this as a global variable
    :param token: str of the Socket API Security Token
    :return:
    """
    global encoded_key
    encoded_key = base64.b64encode(token.encode()).decode('ascii')


def do_request(
        path: str,
        headers: dict = None,
        payload: [dict, str] = None,
        files: list = None,
        method: str = "GET",
) -> requests.request:
    """
    do_requests is the shared function for making HTTP calls

    :param path: Required path for the request
    :param headers: Optional dictionary of headers. If not set will use a default set
    :param payload: Optional dictionary or string of the payload to pass
    :param files: Optional list of files to upload
    :param method: Optional method to use, defaults to GET
    :return:
    """
    if encoded_key is None or encoded_key == "":
        raise APIKeyMissing

    if headers is None:
        headers = default_headers
        headers['Authorization'] = f"Basic {encoded_key}"
    url = f"{api_url}/{path}"
    response = requests.request(
        method.upper(),
        url,
        headers=headers,
        data=payload,
        files=files,
        timeout=timeout
    )
    if response.status_code <= 399:
        return response
    elif response.status_code == 400:
        print(f"url={url}")
        print(f"payload={payload}")
        print(f"files={files}")
        error = {
            "msg": "bad request",
            "error": response.text
        }
        raise APIFailure(error)
    elif response.status_code == 401:
        raise APIAccessDenied("Unauthorized")
    elif response.status_code == 403:
        raise APIInsufficientQuota("Insufficient max_quota for API method")
    elif response.status_code == 404:
        raise APIResourceNotFound(f"Path not found {path}")
    elif response.status_code == 429:
        raise APIInsufficientQuota("Insufficient quota for API route")
    elif response.status_code == 524:
        raise APICloudflareError(response.text)
    else:
        msg = {
            "status_code": response.status_code,
            "error": response.text,
            "UnexpectedError": "There was an unexpected error using the API"
        }
        raise APIFailure(msg)


class Core:
    api_key: str
    base_api_url: str
    request_timeout: int
    reports: list
    plugins: dict
    default_branches: list
    start_date: str
    default_branch_only: bool
    report_id: str

    def __init__(
            self,
            api_key: str,
            base_api_url=None,
            request_timeout=None,
            enable_all_alerts=False,
            start_date: str = None,
            default_branches: list = None,
            default_branch_only: bool = False,
            report_id: str = None
    ):
        self.report_id = report_id
        self.default_branches = default_branches
        if self.default_branches is not None:
            global default_branch_names
            default_branch_names = self.default_branches
        self.default_branch_only = default_branch_only
        global default_only
        default_only = self.default_branch_only
        self.api_key = api_key + ":"
        encode_key(self.api_key)
        self.start_date = start_date
        self.socket_date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.base_api_url = base_api_url
        if self.base_api_url is not None:
            Core.set_api_url(self.base_api_url)
        self.request_timeout = request_timeout
        if self.request_timeout is not None:
            Core.set_timeout(self.request_timeout)
        if enable_all_alerts:
            global all_new_alerts
            all_new_alerts = True
        self.plugins = {}
        Core.set_org_vars()

    @staticmethod
    def set_org_vars() -> None:
        """
        Sets the main shared global variables
        :return:
        """
        global org_id, org_slug, full_scan_path, repository_path, security_policy
        org_id, org_slug = Core.get_org_id_slug()
        base_path = f"orgs/{org_slug}"
        full_scan_path = f"{base_path}/full-scans"
        repository_path = f"{base_path}/repos"
        security_policy = Core.get_security_policy()

    @staticmethod
    def set_api_url(base_url: str):
        """
        Set the global API URl if provided
        :param base_url:
        :return:
        """
        global api_url
        api_url = base_url

    @staticmethod
    def set_timeout(request_timeout: int):
        """
        Set the global Requests timeout
        :param request_timeout:
        :return:
        """
        global timeout
        timeout = request_timeout

    @staticmethod
    def get_org_id_slug() -> (str, str):
        """
        Gets the Org ID and Org Slug for the API Token
        :return:
        """
        path = "organizations"
        response = do_request(path)
        data = response.json()
        organizations = data.get("organizations")
        new_org_id = None
        new_org_slug = None
        if len(organizations) == 1:
            for key in organizations:
                new_org_id = key
                new_org_slug = organizations[key].get('slug')
        return new_org_id, new_org_slug

    @staticmethod
    def get_reports() -> dict:
        path = "report/list"
        results = do_request(path)
        try:
            reports = results.json()
            return reports
        except Exception as error:
            log.error("Failed to get report list json")
            log.error(error)
            sys.exit(2)

    @staticmethod
    def get_sbom_data(report_id: str) -> list:
        path = f"sbom/view/{report_id}"
        response = do_request(path)
        results = []
        try:
            data = response.text
            data.strip('"')
            data.strip()
            for line in data.split("\n"):
                if line != '"' and line != "" and line is not None:
                    item = json.loads(line)
                    results.append(item)
        except Exception as error:
            log.debug(f"Failed to retrieve report for {report_id}")
            log.debug(error)
        return results

    @staticmethod
    def get_security_policy() -> dict:
        """
        Get the Security policy and determine the effective Org security policy
        :return:
        """
        path = "settings"
        payload = [
            {
                "organization": org_id
            }
        ]
        response = do_request(path, payload=json.dumps(payload), method="POST")
        data = response.json()
        defaults = data.get("defaults")
        default_rules = defaults.get("issueRules")
        entries = data.get("entries")
        org_rules = {}
        for org_set in entries:
            settings = org_set.get("settings")
            if settings is not None:
                org_details = settings.get("organization")
                org_rules = org_details.get("issueRules")
        for default in default_rules:
            if default not in org_rules:
                action = default_rules[default]["action"]
                org_rules[default] = {
                    "action": action
                }
        return org_rules

    @staticmethod
    def get_latest_default_branch(reports: list) -> list:
        latest = {}
        all_reports = []
        for report in reports:
            report: Report
            if report.branch in default_branch_names and report.repo not in latest:
                latest[report.repo] = report
            if report.branch in default_branch_names:
                old_report: Report
                old_report = latest[report.repo]
                old_created_at = datetime.strptime(old_report.created_at, socket_date_format)
                created_at = datetime.strptime(report.created_at, socket_date_format)
                if created_at > old_created_at:
                    latest[report.repo] = report
        for repo_name in latest:
            report = latest[repo_name]
            all_reports.append(report)
        return all_reports

    @staticmethod
    def create_reports_list(raw_reports: dict) -> list:
        reports = []
        for raw_report in raw_reports:
            report = Report(**raw_report)
            reports.append(report)
        return reports

    def get_issues(self) -> list:
        raw_reports = Core.get_reports()
        reports = Core.create_reports_list(raw_reports)
        from_time = datetime.strptime(self.start_date, date_format)
        issues = []
        if self.report_id is not None:
            Core.handle_single_report(reports, self.report_id, issues)
        else:
            Core.handle_reports(reports, from_time, issues)
        return issues

    @staticmethod
    def handle_single_report(reports: list, report_id: str, issues: list) -> list:
        report_data = None
        for report_raw in reports:
            report = Report(**report_raw)
            if report.id == report_id:
                report_data = report
        if report_data is None:
            log.error(f"Unable to find report {report_id}")
        else:
            sbom = Core.get_sbom_data(report_data.id)
            packages = Core.create_sbom_dict(sbom)
            for package_id in packages:
                package: Package
                package = packages[package_id]
                issues = Core.create_issue_alerts(package, issues, packages, report_data)
        return issues

    @staticmethod
    def handle_reports(reports: list, from_time: datetime, issues: list) -> list:
        if default_only:
            reports = Core.get_latest_default_branch(reports)
        for report in reports:
            report: Report
            created_at = datetime.strptime(report.created_at, socket_date_format)
            if from_time is None or (created_at >= from_time):
                sbom = Core.get_sbom_data(report.id)
                packages = Core.create_sbom_dict(sbom)
                for package_id in packages:
                    package: Package
                    package = packages[package_id]
                    issues = Core.create_issue_alerts(package, issues, packages, report)
        return issues

    @staticmethod
    def create_issue_alerts(package: Package, alerts: list, packages: dict, report: Report) -> list:
        """
        Create the Issue Alerts from the package and base alert data.
        :param package: Package - Current package that is being looked at for Alerts
        :param alerts: Dict - All found Issue Alerts across all packages
        :param packages: Dict - All packages detected in the SBOM and needed to find top level packages
        :param report: Report - Report object
        :return:
        """
        for item in package.alerts:
            alert = Alert(**item)
            try:
                props = getattr(all_issues, alert.type)
            except AttributeError:
                # log.warning(f"Unable to get issue type props: {alert.type}")
                props = None
            if props is not None:
                description = props.description
                title = props.title
                suggestion = props.suggestion
                next_step_title = props.nextStepTitle
            else:
                description = ''
                title = None
                suggestion = ''
                next_step_title = ''
            introduced_by = Core.get_source_data(package, packages)
            pr = ""
            if report.pull_requests is not None:
                for pr_number in report.pull_requests:
                    pr += f"{pr_number};"
                pr = pr.strip(";")
            is_error = Core.is_error(alert)
            issue_alert = IssueRecord(
                owner=report.owner,
                repo=report.repo,
                report_id=report.id,
                pr=pr,
                commit=report.commit,
                created_at=report.created_at,
                pkg_type=package.type,
                pkg_name=package.name,
                pkg_version=package.version,
                pkg_id=package.id,
                type=alert.type,
                severity=alert.severity,
                category=alert.category,
                key=alert.key,
                props=alert.props,
                description=description,
                title=title,
                suggestion=suggestion,
                next_step_title=next_step_title,
                introduced_by=introduced_by,
                is_error=is_error
            )
            if (not all_new_alerts and is_error) or all_new_alerts:
                alerts.append(issue_alert)
        return alerts

    @staticmethod
    def is_error(alert: Alert):
        """
        Compare the current alert against the Security Policy to determine if it should be included. Can be overridden
        with all_new_alerts Global setting if desired to return all alerts and not just the error category from the
        security policy.
        :param alert:
        :return:
        """
        if all_new_alerts or (alert.type in security_policy and security_policy[alert.type]['action'] == "error"):
            return True
        else:
            return False

    @staticmethod
    def get_source_data(package: Package, packages: dict) -> list:
        """
        Creates the properties for source data of the source manifest file(s) and top level packages.
        :param package: Package - Current package being evaluated
        :param packages: Dict - All packages, used to determine top level package information for transitive packages
        :return:
        """
        introduced_by = []
        if package.direct:
            manifests = ""
            for manifest_data in package.manifestFiles:
                manifest_file = manifest_data.get("file")
                manifests += f"{manifest_file};"
            manifests = manifests.rstrip(";")
            source = ("direct", manifests)
            introduced_by.append(source)
        else:
            for top_id in package.topLevelAncestors:
                top_package: Package
                top_package = packages[top_id]
                manifests = ""
                top_purl = f"{top_package.type}/{top_package.name}@{top_package.version}"
                for manifest_data in top_package.manifestFiles:
                    manifest_file = manifest_data.get("file")
                    manifests += f"{manifest_file};"
                manifests = manifests.rstrip(";")
                source = (top_purl, manifests)
                introduced_by.append(source)
        return introduced_by

    @staticmethod
    def create_purl(package_id: str, packages: dict) -> (Purl, Package):
        """
        Creates the extended PURL data to use in the added or removed package details. Primarily used for outputting
        data in the results for detections.
        :param package_id: Str - Package ID of the package to create the PURL data
        :param packages: dict - All packages to use for look up from transitive packages
        :return:
        """
        package: Package
        package = packages[package_id]
        introduced_by = Core.get_source_data(package, packages)
        purl = Purl(
            id=package.id,
            name=package.name,
            version=package.version,
            ecosystem=package.type,
            direct=package.direct,
            introduced_by=introduced_by,
            author=package.author or [],
            size=package.size,
            transitives=package.transitives
        )
        return purl, package

    @staticmethod
    def create_sbom_dict(sbom: list) -> dict:
        """
        Converts the SBOM Artifacts from the FulLScan into a Dictionary for parsing
        :param sbom: list - Raw artifacts for the SBOM
        :return:
        """
        packages = {}
        top_level_count = {}
        for item in sbom:
            package = Package(**item)
            if package.id in packages:
                print("Duplicate package?")
            else:
                package = Core.get_license_details(package)
                packages[package.id] = package
                for top_id in package.topLevelAncestors:
                    if top_id not in top_level_count:
                        top_level_count[top_id] = 1
                    else:
                        top_level_count[top_id] += 1
        if len(top_level_count) > 0:
            for package_id in top_level_count:
                packages[package_id].transitives = top_level_count[package_id]
        return packages

    @staticmethod
    def get_license_details(package: Package) -> Package:
        license_raw = package.license
        license_str = Licenses.make_python_safe(license_raw)
        if license_str is not None and hasattr(licenses, license_str):
            license_obj = getattr(licenses, license_str)
            package.license_text = license_obj.licenseText
        return package

