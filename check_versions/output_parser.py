import subprocess
import xml.etree.ElementTree as ET

from .linux_common import common_parse_info

class Distro:
    OUTPUT_FORMAT = 'common'
    def parse_info(self, output):
        return common_parse_info(self.OUTPUT_FORMAT, output)

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

class OpenSUSE(Distro):
    OUTPUT_FORMAT = 'zypper'
    def info_command(self, packages):
        if 'python3' in packages:
            wp_python3_xml = subprocess.check_output(["zypper", "--xmlout", "what-provides", "python3"])
            wp_python3 = ET.fromstring(wp_python3_xml).find('./search-result/solvable-list/solvable').attrib['name']
            packages[packages.index('python3')] = wp_python3
        return 'zypper --xmlout info {}'.format(' '.join(packages))

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
            version = version.split('_')[0]
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
