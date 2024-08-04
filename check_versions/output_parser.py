import subprocess
import xml.etree.ElementTree as ET

class Distro:
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
            packages[packages.index('python3')] = wp_python3
        return 'zypper --xmlout info {}'.format(' '.join(packages))

    def parse_info(self, output):
        root = ET.fromstring(output)
        messages = root.findall("./message[@type='info']")
        messages = [msg.text for msg in messages]
        messages = list(filter(lambda msg: ':' in msg, messages))
        return self.parse_chunks(messages)


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
