from functools import lru_cache as memoize
from pathlib import Path
from subprocess import check_output
import sys

def run(*args):
    return check_output(args).decode().strip()

def is_linux():
    return run('uname', '-s') == 'Linux'

def is_freebsd():
    return run('uname', '-s') == 'FreeBSD'

def os_release():
    os_info = dict([x.split('=', 1) for x in Path('/etc/os-release').read_text().strip().split('\n')])
    for k in os_info.keys():
        if os_info[k].startswith('"') and os_info[k].endswith('"'):
            os_info[k] = os_info[k][1:-1]
    return os_info

def main(argv):
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
        os_version = os_release().get('VERSION_ID', '')

        if os_version:
            os_desc = '{} {}'.format(os_name, os_version)
        else:
            os_desc = os_name
    elif is_freebsd():
        os_name = 'FreeBSD'
        os_desc = run('uname', '-sr')

    print('OS name: {}'.format(os_name))
    print('OS desc: {}'.format(os_desc))
