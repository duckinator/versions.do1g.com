import datetime
import http.client
import io
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from . import supported_versions


def download_data(build_id, os_name):
    Path('_data').mkdir(exist_ok=True)

    uri_domain = 'https://api.cirrus-ci.com'
    uri_path = '/v1/artifact/build/{}/{}/json.zip'.format(build_id, os_name)

    print('Downloading {}{}...'.format(uri_domain, uri_path))

    conn = http.client.HTTPSConnection('api.cirrus-ci.com')
    conn.request("GET", uri_path)
    resp = conn.getresponse().read()
    conn.close()
    zf = ZipFile(io.BytesIO(resp))
    for member in zf.infolist():
        print('> Extracting {}'.format(member.filename))
        zf.extract(member, path='_data/')


def download_all(build_id):
    os_names = [
        'archlinux_and_manjaro',
        'fedora',
        'opensuse',
        'debian_and_ubuntu',
        'freebsd',
    ]

    for os_name in os_names:
        download_data(build_id, os_name)


def raw_data():
    paths = Path('_data/source').glob('*.json')
    return [json.loads(path.read_text()) for path in paths]


def os_names():
    return sorted([data['description'] for data in raw_data()])


def normalized_data():
    raw = raw_data()
    data = {}
    for chunk in raw:
        data[chunk['description']] = chunk
    return data


def build_table():
    data = normalized_data()
    for name in os_names():
        print(data[name])

    exit()


def main(argv):
    if len(argv) == 1:
        print("Usage: python3 -m generate_site BUILD_ID")
        sys.exit(1)

    build_id = argv[1]

    Path('_site').mkdir()
    Path('_site/application.css').write_text(
        Path('src/application.css').read_text()
    )

    download_all(build_id)

    date = datetime.datetime.utcnow().strftime('%b %d, %Y at %H:%M UTC')
    table = build_table()
    template = Path('src/index.html.template').read_text()
    Path('_site/index.html').write_text(
        template.replace('{{ date }}', date).replace('{{ table }}', table)
    )
