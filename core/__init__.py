import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s: %(funcName)s: %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


log = logging.getLogger()
columns = [
    "id",
    "report_id",
    "owner",
    "repo",
    "branch",
    "pkg_type",
    "pkg_name",
    "pkg_version",
    "issue_category",
    "issue_type",
    "issue_severity",
    "pr_url",
    "commit",
    "commit_url",
    "created_at"
]
