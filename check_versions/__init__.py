"""Check the available versions of various packages on the current system."""

import json
from pathlib import Path
import shlex
from subprocess import check_output
import sys

from . import output_parser

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

    os_filename_id = os_desc.lower().replace(' ', '_')

    distro = output_parser.DISTROS[os_name]()

    output = run(distro.info_command(packages))
    print()
    print('OS name: {}'.format(os_name))
    print('OS desc: {}'.format(os_desc))
    # print("Parsed output:")
    parsed_output = distro.parse_info(output)
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
