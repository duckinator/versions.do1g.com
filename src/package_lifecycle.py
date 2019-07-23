from functools import lru_cache as memoize
from lxml import html
from pkg_resources import parse_version as V
from urllib.request import urlopen


urls = {
    'clang': 'https://llvm.org',
    'gcc': 'https://gcc.gnu.org/',
    'python3': 'https://devguide.python.org/#status-of-python-branches',
    'ruby': 'https://www.ruby-lang.org/en/downloads/branches/',
}


# We memoize _get() to avoid redundant network requests.
@memoize()
def _get(url):
    return urlopen(url).read().decode()


def _get_html(url):
    return html.document_fromstring(_get(url))


def _normalize_version(version):
    # replace \xa0 (non-breaking space) with space.
    version = version.replace("\xa0", " ")

    # given "<name> <version>", return "<version>".
    return version.split(' ')[1]


def _normalize(versions):
    return [_normalize_version(version) for version in versions]


def supported(package, version):
    versions = all()[package]
    return any([V(version) >= V(v) for v in versions])


def all():
    return {
        'clang': clang(),
        'gcc': gcc(),
        'python3': python3(),
        'ruby': ruby(),
    }


def clang():
    versions = _get_html(urls['clang']).xpath('//a[starts-with(@href, "/releases/download.html#")]/b/text()')
    return _normalize(versions)


def gcc():
    versions = _get_html(urls['gcc']).xpath('//td/dl/dt/span[@class="version"]/a/text()')
    return _normalize(versions)


def python3():
    return _get_html(urls['python3']).xpath('//div[@id="status-of-python-branches"]/table[1]//tr/td[1][starts-with(text(), "3.")]/text()')


def ruby():
    versions = _get_html(urls['ruby']).xpath('//div[@id="content-wrapper"]/div/p[not(contains(text(), "status: eol"))]/preceding-sibling::h3/text()')
    return _normalize(versions)
