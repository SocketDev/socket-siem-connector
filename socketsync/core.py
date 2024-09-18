import json
from datetime import datetime, timezone, timedelta
import logging
from socketdev import socketdev
from socketsync.issues import AllIssues
from socketsync.licenses import Licenses
from socketsync.classes import (
    Report,
    IssueRecord,
    Package,
    Alert,
    Purl
)

global encoded_key
global socket
global org_id
global report_from_time
global actions
socket: socketdev
org_id: str
org_slug: str
report_from_time: int
actions: list[str]
timeout = 30
full_scan_path = ""
repository_path = ""
all_issues = AllIssues()
licenses = Licenses()
all_new_alerts = False
default_branch_names = [
        "master",
        "main"
    ]
default_only = False
security_policy = {}
date_format = "%Y-%m-%d %H:%M"
socket_date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

log = logging.getLogger("socketdev")
log.addHandler(logging.NullHandler())

__all__ = [
    "Core",
    "log"
]


class Core:
    api_key: str
    request_timeout: int
    reports: list
    plugins: dict
    default_branches: list
    start_date: str
    default_branch_only: bool
    report_id: str
    from_time: int
    actions_override: list[str]
    enable_all_alerts: bool
    properties: list

    def __init__(
            self,
            api_key: str,
            base_api_url=None,
            request_timeout=None,
            enable_all_alerts=False,
            start_date: str = None,
            default_branches: list = None,
            default_branch_only: bool = False,
            report_id: str = None,
            from_time: int = 300,
            actions_override: list = None,
            properties: list = None
    ):
        self.actions_override = actions_override
        global actions
        actions = self.actions_override
        self.api_key = api_key
        self.report_id = report_id
        self.default_branches = default_branches
        self.from_time = from_time
        self.properties = properties
        if self.default_branches is not None:
            global default_branch_names
            default_branch_names = self.default_branches
        self.default_branch_only = default_branch_only
        global default_only
        default_only = self.default_branch_only
        self.start_date = start_date
        global report_from_time
        if self.start_date is not None:
            suggested_method = (
                "Suggested Replacement: from_time = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())"
            )
            log.warning("start_date has been deprecated in favor of from_time and will be removed")
            log.warning(suggested_method)
            start_time = datetime.strptime(self.start_date, date_format)
            end_time = datetime.now(timezone.utc)
            diff = (end_time - start_time).total_seconds()
            report_from_time = diff
        else:
            report_from_time = from_time
        self.socket_date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.base_api_url = base_api_url
        self.request_timeout = request_timeout
        if self.request_timeout is not None:
            Core.set_timeout(self.request_timeout)
        if enable_all_alerts:
            global all_new_alerts
            all_new_alerts = True
        self.plugins = {}
        global socket
        socket = socketdev(token=self.api_key, timeout=timeout)
        Core.set_org_vars()

    @staticmethod
    def set_org_vars() -> None:
        """
        Sets the main shared global variables
        :return:
        """
        log.debug("Getting Organization Configuration")
        global org_id, org_slug, full_scan_path, repository_path, security_policy
        org_id, org_slug = Core.get_org_id_slug()
        base_path = f"orgs/{org_slug}"
        full_scan_path = f"{base_path}/full-scans"
        repository_path = f"{base_path}/repos"
        security_policy = Core.get_security_policy()
        output = {
            "org_id": org_id,
            "base_path": base_path,
            "full_scan_path": full_scan_path,
            "repository_path": repository_path,
            "security_policy": security_policy
        }
        log.debug(f"Org Settings: {json.dumps(output)}")

    @staticmethod
    def set_timeout(request_timeout: int):
        """
        Set the global Requests timeout
        :param request_timeout:
        :return:
        """
        log.debug(f"Setting API request timeout to {request_timeout} seconds")
        global timeout
        timeout = request_timeout
        socketdev.set_timeout(timeout)

    @staticmethod
    def get_org_id_slug() -> (str, str):
        """
        Gets the Org ID and Org Slug for the API Token
        :return:
        """
        organizations = socket.org.get()
        orgs = organizations.get("organizations")
        new_org_id = None
        new_org_slug = None
        if orgs is not None and len(orgs) == 1:
            for key in orgs:
                new_org_id = key
                new_org_slug = orgs[key].get('slug')
        return new_org_id, new_org_slug

    @staticmethod
    def get_security_policy() -> dict:
        """
        Get the Security policy and determine the effective Org security policy
        :return:
        """
        data = socket.settings.get(org_id)
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
        log.debug("Looking for latest default branches")
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
    def create_reports_list(raw_reports: dict, report_id: str = None) -> list:
        reports = []
        commits = []
        for raw_report in raw_reports:
            report = Report(**raw_report)
            if report_id is not None and report_id == report.id:
                reports.append(report)
            elif report_id is None:
                if report.commit not in commits or report.commit is None or report.commit == "":
                    reports.append(report)
                    commits.append(report.commit)
                else:
                    reports.append(report)
        return reports

    def get_issues(self) -> list:
        issues = []
        if self.report_id is not None:
            all_time = (datetime.now(timezone.utc) - timedelta(days=1825)).timestamp()
            raw_reports = socket.report.list(int(all_time))
        else:
            raw_reports = socket.report.list(int(report_from_time))
        reports = Core.create_reports_list(raw_reports, self.report_id)
        log.debug(f"Found {len(reports)} Socket Scans")
        Core.handle_reports(reports, issues)
        return issues

    @staticmethod
    def handle_reports(reports: list, issues: list) -> list:
        if default_only:
            reports = Core.get_latest_default_branch(reports)
        for report in reports:
            report: Report
            log.debug(f"Getting results for scan id {report.id}")
            sbom = socket.sbom.view(report.id)
            packages = socket.sbom.create_packages_dict(sbom)
            log.debug(f"Finding issues in {report.id}")
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
                is_error=is_error,
                direct=package.direct
            )
            if alert.type in security_policy:
                action = security_policy[alert.type]['action']
                setattr(issue_alert, action, True)
                setattr(issue_alert, "action", action)
            if (not all_new_alerts and actions is None and (issue_alert.error or issue_alert.warn)) or all_new_alerts:
                log.debug(f"Found issue {issue_alert.title} for scan {report.id}")
                if issue_alert not in alerts:
                    alerts.append(issue_alert)
            elif actions is not None:
                for override in actions:
                    if issue_alert.action == override.lower():
                        log.debug(f"Found issue {issue_alert.title} for scan {report.id}")
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
                log.debug(f"Duplicate package id found: {package.id}")
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

