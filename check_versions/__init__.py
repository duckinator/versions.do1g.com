"""Check the available versions of various packages on the current system."""

from functools import lru_cache as memoize
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


def is_linux():
    """Return True if the system is running Linux; False otherwise."""
    return sys.platform.startswith('linux')


def is_freebsd():
    """Return True if the system is running FreeBSD; False otherwise."""
    return sys.platform.startswith('freebsd')


@memoize()
def os_release():
    """Return a dict containing a normalized version of /etc/os-release."""
    lines = Path('/etc/os-release').read_text().strip().split('\n')
    os_info = dict([x.split('=', 1) for x in lines])
    for key, val in os_info.items():
        if val.startswith('"') and val.endswith('"'):
            os_info[key] = val[1:-1]
    return os_info


def main(_argv):
    """Entrypoint for the script."""
    packages = ['python3', 'ruby', 'clang', 'gcc']

    # Detect the operating system name/description.
    if (is_linux() and
            Path('/etc/arch-release').exists() and
            not Path('/etc/arch-release').read_text()):
        # If /etc/arch-release exists and is empty, it's probably ArchLinux.
        # If /etc/arch-release exists and isn't empty, it's probably
        # Manjaro -- which gets handled using the normal os_release() approach.
        # If another Arch-based system without /etc/os-release is found,
        # we'll need to revisit this.
        #
        # TODO: See if there's an Arch package that provides /etc/os-release
        #       so we can remove this obnoxious special case.
        os_name = 'ArchLinux'
        os_desc = os_name
    elif is_linux():
        os_name = os_release()['NAME']

        # Keeping name length reasonable is more important than GNU's ego.
        os_name = os_name.replace(' GNU/Linux', '')

        os_version = os_release().get('VERSION_ID', '')

        if os_version:
            os_desc = '{} {}'.format(os_name, os_version)
        else:
            os_desc = os_name
    elif is_freebsd():
        os_name = 'FreeBSD'
        os_desc = run('uname -sr')

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
