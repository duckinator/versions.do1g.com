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
    if is_linux():
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
