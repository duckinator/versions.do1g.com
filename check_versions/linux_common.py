import xml.etree.ElementTree as ET


def _normalize_version(version):
    if ':' in version:
        version = version.split(':')[1]
    if '-' in version:
        version = version.split('-')[0]
    if '+' in version:
        version = version.split('+')[0]
    if ',' in version:
        version = version.split(',')[0]
    return version


def parse_chunk(chunk):
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

    version = _normalize_version(data['Version'])

    print("{:20} {}".format(name, version))

    return (name, {
        'version': version,
        'via': None,
        })


def parse_chunks(chunks):
    parsed_chunks = [parse_chunk(chunk) for chunk in chunks]
    return {name: data for (name, data) in parsed_chunks}


def parse_common(output):
    output = output.replace("\r", "")
    chunks = output.strip().split("\n\n")
    return parse_chunks(chunks)


# raw `dnf info <packages>` output => {'pkg1': 'ver1', 'pkg2': 'ver2'}
def _parse_dnf(output):
    # Remove \r, collapse line continuations.
    output = output.replace("\r", "").replace("\n             : ", ' ')
    return parse_common(output)


def common_parse_info(pkgman, output):
    return {
        'common': parse_common,
        'dnf': _parse_dnf,
    }[pkgman](output)
