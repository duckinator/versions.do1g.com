#!/usr/bin/env python3

import datetime
from pathlib import Path

import docker
import vagrant

# Format is:
#   'Name': [backend_module, 'image name']
operating_systems = {
    # Linux distros

    'ArchLinux': [docker, 'archlinux/base:latest'],

    'Debian 9': [docker, 'debian:9'],
    'Debian 10': [docker, 'debian:buster'],

    'Fedora 29': [docker, 'fedora:29'],
    'Fedora 30': [docker, 'fedora:30'],

    'OpenSUSE Leap 15.0': [docker, 'opensuse/leap:15.0'],
    'OpenSUSE Leap 15.1': [docker, 'opensuse/leap:15.1'],

    'Ubuntu 18.04': [docker, 'ubuntu:18.04'],
    'Ubuntu 19.04': [docker, 'ubuntu:19.04'],

    'DragonFly BSD 5': [vagrant, 'DragonFly BSD 5'],
    'FreeBSD 11': [vagrant, 'FreeBSD 11'],
    'FreeBSD 12': [vagrant, 'FreeBSD 12'],
    #'NetBSD 8': [vagrant, 'NetBSD 8'],
    #'OpenBSD 6': [vagrant, 'OpenBSD 6'],
}

packages = ['python3', 'ruby', 'clang', 'gcc']

def get_info():
    os_info = {}
    for os_name in operating_systems.keys():
        parts = operating_systems[os_name]
        module = parts[0]
        image = parts[1]
        print("Fetching information for {} using {}.".format(image, module.__name__.capitalize()))
        os_info[os_name] = module.get_info(image, packages)
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
                if package_name in os_info[os_name]:
                    version = os_info[os_name][package_name]
                    f.write("    <td>{}</td>\n".format(version))
                else:
                    f.write("    <td>??</td>\n")
            f.write("  </tr>\n")
        f.write("</table>\n")

        f.write(template_parts[1])

main()
