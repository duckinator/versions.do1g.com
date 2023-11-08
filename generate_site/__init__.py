"""Downloads data from Cirrus CI artifacts and generates the site."""

import datetime
import http.client
import io
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

from . import supported_versions


def build_index(directory):
    """Build a basic HTML index listing all of the files in a directory."""
    directory_url = str(directory).split('_site', 1)[1]
    urls = [str(path).split('_site', 1)[1].split('/')[-1]
            for path in Path(directory).glob('*')]
    links = [f'<li><a href="{url}">{url}</a></li>' for url in urls]
    return '\n'.join([
        '<!doctype html>',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        f'<title>Directory listing for {directory_url}</title>'
        f'<h1>Directory listing for {directory_url}</h1>'
        '<ul>',
        *links,
        '</ul>',
    ])


def download_data(build_id, os_name):
    """Download relevant Cirrus CI artifacts."""
    Path('_data').mkdir(exist_ok=True)

    uri_domain = 'https://api.cirrus-ci.com'
    uri_path = '/v1/artifact/build/{}/{}/json.zip'.format(build_id, os_name)

    print('Downloading {}{}...'.format(uri_domain, uri_path))

    conn = http.client.HTTPSConnection('api.cirrus-ci.com')
    conn.request("GET", uri_path)
    resp = conn.getresponse().read()
    conn.close()
    with ZipFile(io.BytesIO(resp)) as zip_file:
        for member in zip_file.infolist():
            print('> Extracting {}'.format(member.filename))
            zip_file.extract(member, path='_data/')


def download_all(build_id):
    """Download Cirrus CI artifacts for all supported operating systems."""
    os_name_list = [
        'archlinux_and_manjaro',
        'fedora',
        'opensuse',
        'debian_and_ubuntu',
        'freebsd',
    ]

    for os_name in os_name_list:
        download_data(build_id, os_name)


def raw_data():
    """Get raw data for each .json file in _data/."""
    paths = Path('_data/source').glob('*.json')
    return [json.loads(path.read_text()) for path in paths]


def os_names():
    """Return a list of all operating system names."""
    return sorted([data['description'] for data in raw_data()], key=str.lower)


def normalized_data():
    """Return normalized versions of data from all .json files in _data/."""
    raw = raw_data()
    data = {}
    for chunk in raw:
        data[chunk['description']] = chunk
    return data


def maintenance_status(package, version):
    """Returns one of 'latest', 'outdated', 'unsupported', or 'unknown'.
    These are used as class names in the generated HTML."""

    if supported_versions.unknown(package, version):
        raise Exception(f"don't know if {package} v{version} is supported. this shouldn't happen.")

    if supported_versions.is_latest(package, version):
        return 'latest'

    if supported_versions.supported(package, version):
        return 'outdated'

    return 'unsupported'


def maintenance_status_note(package, version):
    """Returns '1', '2', or '3'. These correspond to the notes at the bottom
    of the website."""
    return {
        'latest': '*',
        'outdated': '&dagger;',
        'unsupported': '&ddagger;',
        'unknown': '4',
    }[maintenance_status(package, version)]


def build_table():
    """Generate a table of version information."""
    os_data = normalized_data()
    table = [
        "<table>",
        '  <tr class="header">',
        '    <th>Package</th>',
        *['    <th>{}</th>'.format(os_data[os]['description']) for os in os_names()],
        '  </tr>',
    ]
    for package in supported_versions.package_names:
        table.append(f'  <tr id="pkg-{package}">')
        table.append(f'    <th class="left-header"><a href="#pkg-{package}">{package}</a></th>')
        for os_name in os_names():
            os_package_data = os_data[os_name]['results'][package]
            version = os_package_data['version']
            via = os_package_data['via']
            if via:
                via_note = f'(via {via})'
            else:
                via_note = ''
            status = maintenance_status(package, version)
            note = maintenance_status_note(package, version)
            table.append(f'    <td class="{status}">{version}&nbsp;<sup>{note}</sup> {via_note}</td>')
        table.append('  </tr>')

    table.append('</table>')

    return '\n'.join(table)


def main(argv):
    """Entrypoint for the script."""
    if len(argv) == 1:
        print("Usage: python3 -m generate_site BUILD_ID")
        sys.exit(1)

    build_id = argv[1]

    Path('_site').mkdir()
    Path('_site/application.css').write_text(
        Path('src/application.css').read_text(),
    )

    if build_id.lower() == 'local':
        shutil.copytree('source/', '_data/source/')
    else:
        download_all(build_id)

    shutil.copytree('_data/', '_site/data/')

    date = datetime.datetime.utcnow().strftime('%b %d, %Y at %H:%M UTC')
    table = build_table()
    template = Path('src/index.html.template').read_text()
    text = template.replace('{{ date }}', date).replace('{{ table }}', table)
    for (package, url) in supported_versions.urls.items():
        text = text.replace('{{ ' + package + ' }}', url)
    Path('_site/index.html').write_text(text)

    Path('_site/data/index.html').write_text(build_index('_site/data'))
    Path('_site/data/source/index.html').write_text(build_index('_site/data/source'))
