import xml.etree.ElementTree as ET


def _normalize_version(version):
    if ':' in version:
        version = version.split(':')[1]
    if '-' in version:
        version = version.split('-')[0]
    if '+' in version:
        version = version.split('+')[0]
    return version


def parse_chunk(chunk):
    lines = chunk.split("\n")

    chunk_info = {}
    for line in lines:
        if ':' not in line:
            continue
        parts = line.split(':', 1)
        name = parts[0].strip()
        value = parts[1].strip()
        chunk_info[name] = value
    return chunk_info


def parse_common(output):
    output = output.replace("\r", "")
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
        package_info[name] = {
            'version': version,
            'via': None,
        }
        print("{:20} {}".format(name, version))
    return package_info


# raw `dnf info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_dnf(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n             : ", ' ')
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


def common_parse_info(pkgman, output):
    return {
        'common': parse_common,
        'dnf': _parse_dnf,
        'zypper': _parse_zypper,
    }[pkgman](output)
