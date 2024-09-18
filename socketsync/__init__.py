import logging


__author__ = 'socket.dev'
__version__ = '1.0.9'
__all__ = [
    "log",
    "__version__",
    "columns",
    "default_headers"
]

log = logging.getLogger("socketdev")
log.addHandler(logging.NullHandler())

columns = [
    "key",
    "report_id",
    "owner",
    "repo",
    "branch",
    "pkg_type",
    "pkg_name",
    "pkg_version",
    "category",
    "title",
    "severity",
    "pr",
    "commit",
    "created_at",
    "action"
]

default_headers = {
    'User-Agent': f'SocketSIEMTool/{__version__}',
    "accept": "application/json",
    'Content-Type': "application/json"
}