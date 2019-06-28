#!/usr/bin/env python3

import datetime
from pathlib import Path
from subprocess import check_output, check_call

distro_containers = {
    'ArchLinux': 'archlinux/base:latest',

    'Debian 9': 'debian:9',
    'Debian 10': 'debian:buster',

    'Fedora 29': 'fedora:29',
    'Fedora 30': 'fedora:30',

    #'OpenSUSE Leap 15.0': 'opensuse/leap:15.0',
    #'OpenSUSE Leap 15.1': 'opensuse/leap:15.1',

    'Ubuntu 18.04': 'ubuntu:18.04',
    'Ubuntu 19.04': 'ubuntu:19.04',
}

# TODO: FreeBSD, OpenBSD, DragonFly BSD

packages = ['python3', 'ruby', 'clang', 'gcc']
package_managers = {
    'archlinux': 'pacman',
    'debian': 'apt',
    'fedora': 'dnf',
    'opensuse': 'zypper',
    'ubuntu': 'apt',
}

def normalize_version(version):
    if ':' in version:
        version = version.split(':')[1]
    if '-' in version:
        version = version.split('-')[0]
    return version

def package_info_command(pkgman, packages):
    if pkgman == 'apt':
        return 'apt-get update && apt-cache show {}'.format(' '.join(packages))
    if pkgman == 'dnf':
        packages = list(map(lambda x: x + '.x86_64', packages))
        return 'dnf info --color=false {}'.format(' '.join(packages))
    if pkgman == 'pacman':
        # ArchLinux calls their python 3.x package 'python', not 'python3'.
        # Unlike basically everything else I've ever encountered.
        if 'python3' in packages:
            packages[packages.index('python3')] = 'python'
        return 'pacman -Syi --noprogressbar {}'.format(' '.join(packages))
    if pkgman == 'zypper':
        return 'zypper info {}'.format(' '.join(packages))

    raise Exception("Unknown package manager: {}".format(pkgman))

def parse_apt_dnf_zypper_chunk(chunk):
    lines = chunk.split("\n")

    chunk_info = {}
    for line in lines:
        if not ':' in line:
            continue
        parts = line.split(':', 1)
        name = parts[0].strip()
        value = parts[1].strip()
        chunk_info[name] = value
    return chunk_info

def parse_apt_dnf_zypper_info_common(output):
    chunks = output.strip().split("\n\n")

    package_info = {}
    for chunk in chunks:
        print("chunk='", chunk, "'")

        data = parse_apt_dnf_zypper_chunk(chunk)
        #print("DATA=", data, "---")
        name = data.get('Package', data.get('Name'))
        version = normalize_version(data['Version'])
        package_info[name] = version
        print('package_info[{}] = {}'.format(name, version))
    return package_info


# raw `apt show <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def parse_apt_info(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n ", ' ')
    return parse_apt_dnf_zypper_info_common(output)

# raw `dnf info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def parse_dnf_info(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n             : ", ' ')
    return parse_apt_dnf_zypper_info_common(output)

# raw `pacman -Syi <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def parse_pacman_info(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n                  ", ' ')

    # Remove ":: <...>" and "downloading <repo name>..." lines.
    valid = lambda x: not x.startswith(":: ") and not x.startswith("downloading ")
    output = "\n".join(filter(valid, output.split("\n")))

    return parse_apt_dnf_zypper_info_common(output)

# raw `zypper info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def parse_zypper_info(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n    ", ' ')
    return parse_apt_dnf_zypper_info_common(output)

def parse_info(pkgman, output):
    return {
        'apt': parse_apt_info,
        'dnf': parse_dnf_info,
        'pacman': parse_pacman_info,
        'zypper': parse_zypper_info,
    }[pkgman](output)


def docker_snippet(image_and_tag):
    # <image name>:<tag> => <image name>
    image = image_and_tag.split(':')[0].split('/')[0]
    setup_snippet = package_info_command(package_managers[image], packages)
    return "printf -- '--START--\\n' && " + setup_snippet + " && printf -- '\\n--END--'"

def docker_run(image, command):
    full_command = ['docker', 'run', '--rm', '-t', image, 'sh', '-c', command]
    #return check_call(full_command)
    return check_output(full_command).decode()

def docker_get_info(image):
    pkgman = package_managers[image.split(':')[0].split('/')[0]]
    command = docker_snippet(image)
    raw_output = docker_run(image, command).replace('\r', '')
    info_output = raw_output.split("--START--\n")[1].split("\n--END--")[0]
    return parse_info(pkgman, info_output)

def get_info():
    os_info = {}
    for os_name in distro_containers.keys():
        os_info[os_name] = {}
        image = distro_containers[os_name]
        print("Fetching information for {}.".format(image))
        package_info = docker_get_info(image)
        for name in package_info.keys():
            os_info[os_name][name] = package_info[name]
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
