#!/usr/bin/env python3

"""Checkthe available versions of various packages on the current system."""

import json
from pathlib import Path
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

PACKAGES = ['python3', 'ruby', 'clang', 'gcc']

def main():
    """Entrypoint for the script."""
    packages = ['python3', 'ruby', 'clang', 'gcc']

    discover().package_info(packages).save()

def run(cmd):
    """Print the command being run, runs it, and prints its output."""
    print('$', cmd)
    args = shlex.split(cmd)
    output = subprocess.check_output(args).decode().strip()
    print(output)
    print()
    return output


class PackageInfo:
    def __init__(self, os_name, os_desc, package_info):
        self.name = os_name
        self.description = os_desc
        self.package_info = package_info

    def as_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'results': self.package_info,
        }

    def save(self):
        os_filename_id = self.description.lower().replace(' ', '_')
        print()
        Path('source').mkdir(exist_ok=True)
        filename = 'source/{}.json'.format(os_filename_id)
        print("Saving data to:", filename)
        Path(filename).write_text(json.dumps(self.as_dict()))
        print("File contents:")
        print(Path(filename).read_text())
        return filename


class Distro:
    def __init__(self, os_name, os_desc):
        self.os_name = os_name
        self.os_desc = os_desc

    def _normalize_version(self, version):
        if ':' in version:
            version = version.split(':')[1]
        if '-' in version:
            version = version.split('-')[0]
        if '+' in version:
            version = version.split('+')[0]
        if ',' in version:
            version = version.split(',')[0]
        return version

    def parse_chunk(self, chunk):
        lines = chunk.split("\n")

        data = {}
        for line in lines:
            if ':' not in line:
                continue
            parts = line.split(':', 1)
            name = parts[0].strip()
            value = parts[1].strip()
            data[name] = value

        # pacman uses 'Package', apt/dnf/zypper use 'Name'
        name = data.get('Package', data.get('Name'))

        # DAMNIT ARCHLINUX.
        if name == 'python':
            name = 'python3'

        version = self._normalize_version(data['Version'])

        print("{:20} {}".format(name, version))

        return (name, {
            'version': version,
            'via': None,
            })

    def parse_chunks(self, chunks):
        parsed_chunks = [self.parse_chunk(chunk) for chunk in chunks]
        return {name: data for (name, data) in parsed_chunks}

    def parse_info(self, output):
        output = output.replace("\r", "")
        chunks = output.strip().split("\n\n")
        return self.parse_chunks(chunks)

    def package_info(self, packages):
        output = run(self.info_command(packages))
        return PackageInfo(self.os_name, self.os_desc, self.parse_info(output))


class ArchLinux(Distro):
    def info_command(self, packages):
        # ArchLinux calls their python 3.x package 'python', not 'python3'.
        # Unlike basically everything else I've ever encountered.
        if 'python3' in packages:
            packages_copy = packages.copy()
            packages_copy[packages_copy.index('python3')] = 'python'
        return 'pacman -Syi --noprogressbar {}'.format(' '.join(packages_copy))

class Debian(Distro):
    def info_command(self, packages):
        return 'apt-cache show {}'.format(' '.join(packages))

class Fedora(Distro):
    OUTPUT_FORMAT = 'dnf'
    def info_command(self, packages):
        packages = list(map(lambda x: x + '.x86_64', packages))
        return 'dnf info --color=false {}'.format(' '.join(packages))

    def parse_info(self, output):
        output = output.replace("\r", "").replace("\n             : ", ' ')
        return super().parse_info(output)

class OpenSUSE(Distro):
    def info_command(self, packages):
        if 'python3' in packages:
            wp_python3_xml = subprocess.check_output(["zypper", "--xmlout", "what-provides", "python3"])
            wp_python3 = ET.fromstring(wp_python3_xml).find('./search-result/solvable-list/solvable').attrib['name']
            self.real_python3_package = wp_python3
            packages[packages.index('python3')] = wp_python3
        return 'zypper --xmlout info {}'.format(' '.join(packages))

    def parse_info(self, output):
        root = ET.fromstring(output)
        messages = root.findall("./message[@type='info']")
        messages = [msg.text for msg in messages]
        messages = list(filter(lambda msg: ':' in msg, messages))
        info = self.parse_chunks(messages)

        # Undo the `zypper what-provides` mess above.
        info["python3"] = info.pop(self.real_python3_package)

        return info


class FreeBSD(Distro):
    def info_command(self, packages):
        if 'clang' in packages:
            packages[packages.index('clang')] = 'llvm'

        return 'sudo pkg rquery "%n %v %dn=%dv" {}'.format(' '.join(packages))

    def parse_info(self, output):
        info = {}

        output = output.strip()
        lines = output.split("\n")
        for line in lines:
            pkg, version, dep = line.split(' ')
            if dep.startswith(pkg):
                realpkg, version = dep.split('=')
            version = self._normalize_version(version.split('_')[0])
            info[pkg] = {
                'version': version,
                'via': None,
            }

            # clang is provided by the 'llvm<version>' package, in FreeBSD
            if pkg == 'llvm':
                info['clang'] = {
                    'version': version,
                    'via': pkg,
                }
                #info['clang'] = '{}:via={}'.format(version, pkg)

        return info


DISTROS = {
    'Arch Linux': ArchLinux,
    'Manjaro Linux': ArchLinux,
    'Debian': Debian,
    'Ubuntu': Debian,
    'Fedora Linux': Fedora,
    'openSUSE Tumbleweed': OpenSUSE,
    'openSUSE Leap': OpenSUSE,
    'FreeBSD': FreeBSD,
}


def discover():
    # Detect the operating system name/description.
    if sys.platform.startswith('freebsd'):
        os_name = 'FreeBSD'
        os_desc = run('uname -sr')
    else: # Assume everything else is Linux.
        # Treat /etc/os-release as a key/value pair of strings,
        # with optional quotes on the value side.
        os_release = {k: v[1:-1] if v[0] == '"' else v for (k, v) in [line.split("=") for line in Path("/etc/os-release").read_text().splitlines() if not line.startswith("#")]}
        os_name = os_release['NAME'].replace(' GNU/Linux', '')
        os_version = os_release.get('VERSION_ID', '')
        os_desc = '{} {}'.format(os_name, os_version).strip()

    return DISTROS[os_name](os_name, os_desc)



if __name__ == "__main__":
    main()
