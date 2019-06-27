#!/usr/bin/env python3

import datetime
from pathlib import Path
import textwrap
from subprocess import check_output, check_call

distro_containers = {
    'ArchLinux': 'archlinux/base:latest',

    'Debian 9 (Stretch)': 'debian:9',
    'Debian 10 (Buster)': 'debian:buster',

    'Fedora 29': 'fedora:29',
    'Fedora 30': 'fedora:30',

    'OpenSUSE Leap 15.0': 'opensuse/leap:15.0',
    'OpenSUSE Leap 15.1': 'opensuse/leap:15.1',

    'Ubuntu 18.04 LTS': 'ubuntu:18.04',
    'Ubuntu 19.04': 'ubuntu:19.04',
}

# TODO: FreeBSD, OpenBSD, DragonFly BSD

docker_setup_snippets = {
    'archlinux': 'pacman --noconfirm -Sy python3 ruby clang gcc',
    'debian': 'apt update && apt install -y python3 ruby clang gcc',
    'fedora': 'dnf install -y python3 ruby clang gcc',
    'opensuse': 'zypper install -y python3 ruby clang gcc',
}
docker_setup_snippets['ubuntu'] = docker_setup_snippets['debian']

test_snippet = """
    printf -- '-- START --\n' &&
    printf -- '\n-- package=python3\n' &&
    python3 --version &&
    printf -- '\n-- package=ruby\n' &&
    ruby --version &&
    printf -- '\n-- package=clang\n' &&
    clang --version &&
    printf -- '\n-- package=gcc\n' &&
    gcc --version &&
    printf -- '\n-- END --\n'
"""

def get_package_version(name, info):
    info = info.strip().split('\n')[0]

    # Python <version>
    if name == 'python3':
        return info.split(' ')[1]

    # Ruby <version>p<...>
    if name == 'ruby':
        return info.split(' ')[1].split('p')[0]

    # clang version <version>
    # clang version <version>-<???>
    if name == 'clang':
        return info.split(' ')[2].split('-')[0]

    # gcc (<???>) <version>
    if name == 'gcc':
        return info.split(')')[1].split(' ')[1]

    return 'UNKNOWN'

def parse_package_info(raw_package_info):
    package_info = {}
    for data in raw_package_info:
        #print(data)
        name = data[0]
        info = data[1]
        package_info[name] = get_package_version(name, info)
    return package_info

def docker_snippet(image_and_tag):
    # <image name>:<tag> => <image name>
    image = image_and_tag.split(':')[0].split('/')[0]
    return docker_setup_snippets[image] + ' && ' + test_snippet

def docker_run(image, command):
    full_command = ['docker', 'run', '--rm', '-t', image, 'sh', '-c', command]
    #return check_call(full_command)
    return check_output(full_command).decode()

def docker_get_info(image):
    command = docker_snippet(image)
    raw_output = docker_run(image, command).replace('\r', '')
    all_packages = raw_output.split('-- START --')[1].split('-- END --')[0].split('\n-- package=')
    raw_package_info = list(map(lambda x: x.strip().split('\n', 1), all_packages))
    if raw_package_info[0] == ['']:
        raw_package_info.pop(0)
    package_info = parse_package_info(raw_package_info)
    return package_info

def get_info():
    os_info = {}
    for os_name in distro_containers.keys():
        print("Fetching {} information... ".format(os_name), end='', flush=True)
        os_info[os_name] = {}
        image = distro_containers[os_name]
        package_info = docker_get_info(image)
        for name in package_info.keys():
            os_info[os_name][name] = package_info[name]
        print("Done.")
    return os_info

def main():
    os_info = get_info()
    packages = os_info[list(os_info.keys())[0]].keys()

    date = datetime.datetime.utcnow().strftime('%b %d, %Y at %H:%M UTC')

    src = Path(__file__).resolve().parent
    site = src.parent / '_site'

    template = src / 'index.html.template'
    output = site / 'index.html'

    template_text= template.read_text()
    template_text = template_text.replace('{{ date }}', date)
    template_parts = template_text.split('{{ table }}')

    with open(str(output), 'w') as f:
        f.write(template_parts[0])

        f.write("<table>\n")
        f.write("  <tr class='header'>\n")
        f.write("    <th>Operating System</td>\n")
        for package in packages:
            f.write("    <th>{}</th>\n".format(package))
        f.write("  </tr>\n")
        for os_name in os_info.keys():
            f.write("  <tr>\n")
            f.write("    <td>{}</td>\n".format(os_name))
            print("{}:".format(os_name))
            package_info = os_info[os_name]
            for name in package_info.keys():
                version = package_info[name]
                f.write("    <td>{}</td>\n".format(version))
                print("  {} = {}".format(name, version))
            f.write("  </tr>\n")
            print("")
        f.write("</table>\n")

        f.write(template_parts[1])

main()
