# It seems Fedora 35 changed the value of NAME in /etc/os-release.
# That results in this file getting imported by check_versions.main(),
# instead of fedora.py.
from .fedora import info_command, parse_info
