"""Check the available versions of various packages on the current system."""

from importlib import import_module
import json
from pathlib import Path
import shlex
from subprocess import check_output
import sys


def run(cmd):
    """Print the command being run, runs it, and prints its output."""
    print('$', cmd)
    args = shlex.split(cmd)
    output = check_output(args).decode().strip()
    print(output)
    print()
    return output


def main(_argv):
    """Entrypoint for the script."""
    packages = ['python3', 'ruby', 'clang', 'gcc']

    # Detect the operating system name/description.
    if sys.platform.startswith('freebsd'):
        os_name = 'FreeBSD'
        os_desc = run('uname -sr')
    else: # Assume everything else is Linux.
        # Treat /etc/os-release as a key/value pair of strings,
        # with optional quotes on the value side.
        os_release = {k: v[1:-1] if v[0] == '"' else v for (k, v) in [line.split("=") for line in Path("/etc/os-release").read_text().splitlines()]}
        os_name = os_release['NAME'].replace(' GNU/Linux', '')
        os_version = os_release.get('VERSION_ID', '')
        os_desc = '{} {}'.format(os_name, os_version).strip()

    os_id = os_name.lower().replace(' ', '_')
    os_filename_id = os_desc.lower().replace(' ', '_')
    module_name = '.output_parsers.{}'.format(os_id)

    # E.g.,
    # - If os_name is 'openSUSE Leap', module is .check_versions.opensuse_leap.
    # - If os_name is 'ArchLinux', module is .check_versions.archlinux.
    # etc.
    module = import_module(module_name, package='check_versions')

    output = run(module.info_command(packages))
    print()
    print('OS name: {}'.format(os_name))
    print('OS desc: {}'.format(os_desc))
    # print("Parsed output:")
    parsed_output = module.parse_info(output)
    data = {
        'name': os_name,
        'description': os_desc,
        'results': parsed_output,
    }
    # print(parsed_output)
    print()
    Path('source').mkdir(exist_ok=True)
    filename = 'source/{}.json'.format(os_filename_id)
    print("Saving data to:", filename)
    Path(filename).write_text(json.dumps(data))
    print("File contents:")
    print(Path(filename).read_text())
