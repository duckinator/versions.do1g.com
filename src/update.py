#!/usr/bin/env python3

import datetime
from pathlib import Path
from subprocess import check_output, check_call
import docker


distro_containers = {
    'ArchLinux': 'archlinux/base:latest',

    'Debian 9': 'debian:9',
    'Debian 10': 'debian:buster',

    'Fedora 29': 'fedora:29',
    'Fedora 30': 'fedora:30',

    'OpenSUSE Leap 15.0': 'opensuse/leap:15.0',
    'OpenSUSE Leap 15.1': 'opensuse/leap:15.1',

    'Ubuntu 18.04': 'ubuntu:18.04',
    'Ubuntu 19.04': 'ubuntu:19.04',
}

# TODO: FreeBSD, OpenBSD, DragonFly BSD

packages = ['python3', 'ruby', 'clang', 'gcc']

def get_info():
    os_info = {}
    for os_name in distro_containers.keys():
        image = distro_containers[os_name]
        print("Fetching information for {}.".format(image))
        os_info[os_name] = docker.get_info(image, packages)
    return os_info

def copy(src, dest):
    return dest.write_text(src.read_text())

def main():
    os_info = get_info()

    print("Generating output files.")

    packages = os_info[list(os_info.keys())[0]].keys()

    date = datetime.datetime.utcnow().strftime('%b %d, %Y at %H:%M UTC')

    src = Path(__file__).resolve().parent
    site = src.parent / '_site'

    copy(src / 'application.css', site / 'application.css')

    template = src / 'index.html.template'
    output = site / 'index.html'

    template_text= template.read_text()
    template_text = template_text.replace('{{ date }}', date)
    template_parts = template_text.split('{{ table }}')

    with open(str(output), 'w') as f:
        f.write(template_parts[0])

        f.write("<table>\n")
        f.write("  <tr class='header'>\n")
        f.write("    <th>Package</th>\n")
        for os_name in os_info.keys():
            f.write("    <th>{}</th>\n".format(os_name))
        f.write("  </tr>\n")
        for package_name in packages:
            f.write("  <tr id='pkg-{}'>\n".format(package_name))
            f.write("    <th class='left-header'><a href='#pkg-{}'>{}</a></th>\n".format(package_name, package_name))
            for os_name in os_info.keys():
                version = os_info[os_name][package_name]
                f.write("    <td>{}</td>\n".format(version))
            f.write("  </tr>\n")
        f.write("</table>\n")

        f.write(template_parts[1])

main()
