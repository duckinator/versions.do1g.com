import xml.etree.ElementTree as ET


def _normalize_version(version):
    if ':' in version:
        version = version.split(':')[1]
    if '-' in version:
        version = version.split('-')[0]
    return version


def parse_chunk(chunk):
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


def parse_common(output):
    chunks = output.strip().split("\n\n")

    package_info = {}
    for chunk in chunks:
        data = parse_chunk(chunk)

        # pacman uses 'Package', apt/dnf/zypper use 'Name'
        name = data.get('Package', data.get('Name'))

        # DAMNIT ARCHLINUX.
        if name == 'python':
            name = 'python3'

        version = _normalize_version(data['Version'])
        package_info[name] = version
        print("{:20} {}".format(name, version))
    return package_info


# raw `apt show <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_apt(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n ", ' ')
    return parse_common(output)


# raw `dnf info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_dnf(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n             : ", ' ')
    return parse_common(output)


# raw `pacman -Syi <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_pacman(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n                  ", ' ')

    # Remove ":: <...>" and "downloading <repo name>..." lines.
    valid = lambda x: not x.startswith(":: ") and not x.startswith("downloading ")
    output = "\n".join(filter(valid, output.split("\n")))

    return parse_common(output)


# raw `zypper info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_zypper(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n    ", ' ')

    root = ET.fromstring(output)
    messages = root.findall("./message[@type='info']")
    messages = [msg.text for msg in messages]
    messages = list(filter(lambda msg: ':' in msg, messages))

    output = "\n\n".join(messages)

    return parse_common(output)


def parse(pkgman, output):
    return {
        'apt': _parse_apt,
        'dnf': _parse_dnf,
        'pacman': _parse_pacman,
        'zypper': _parse_zypper,
    }[pkgman](output)
