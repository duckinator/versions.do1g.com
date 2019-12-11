from functools import lru_cache as memoize
from importlib import import_module
from pathlib import Path
import shlex
from subprocess import check_output
import sys


def run(cmd):
    print('$', cmd)
    args = shlex.split(cmd)
    output = check_output(args).decode().strip()
    print(output)
    print()
    return output


# We memoize() is_linux() to avoid running the same command repeatedly.
@memoize()
def is_linux():
    return run('uname -s') == 'Linux'


# We memoize() is_freebsd() to avoid running the same command repeatedly.
def is_freebsd():
    return run('uname -s') == 'FreeBSD'


def os_release():
    os_info = dict([x.split('=', 1) for x in Path('/etc/os-release').read_text().strip().split('\n')])
    for k in os_info.keys():
        if os_info[k].startswith('"') and os_info[k].endswith('"'):
            os_info[k] = os_info[k][1:-1]
    return os_info


def main(argv):
    packages = ['python3', 'ruby', 'clang', 'gcc']

    # Detect the operating system name/description.
    if is_linux() and Path('/etc/arch-release').exists() and not Path('/etc/arch-release').read_text():
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

    module_part = os_name.lower().replace(' ', '_')
    module_name = '.output_parsers.{}'.format(module_part)

    # E.g.,
    # - If os_name is 'openSUSE Leap', module is .check_versions.opensuse_leap.
    # - If os_name is 'ArchLinux', module is .check_versions.archlinux.
    # etc.
    module = import_module(module_name, package='check_versions')

    setup_cmd = module.setup_command()

    if setup_cmd:
        run(setup_cmd)

    output = run(module.info_command(packages))
    print()
    print('OS name: {}'.format(os_name))
    print('OS desc: {}'.format(os_desc))
    print("Parsed output:")
    print(module.parse_info(output))
