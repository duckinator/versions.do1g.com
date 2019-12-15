import http.client
import io
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

def main(argv):
    if len(argv) == 1:
        print("Usage: python3 -m generate_site BUILD_ID")
        sys.exit(1)

    Path('_site').mkdir()
    Path('_site/application.css').write_text(
        Path('src/application.css').read_text()
    )

    build_id = argv[1]
    download_all(build_id)
