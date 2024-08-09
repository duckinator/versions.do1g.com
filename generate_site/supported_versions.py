"""Fetches lists of supported versions for various software."""

from functools import lru_cache as memoize
from urllib.request import urlopen
from lxml import html
from pkg_resources import parse_version as V


urls = {
    'clang': 'https://llvm.org',
    'gcc': 'https://gcc.gnu.org/',
    'python3': 'https://devguide.python.org/versions/#supported-versions',
    'ruby': 'https://www.ruby-lang.org/en/downloads/branches/',
}


package_names = urls.keys()


@memoize()
def _get_html(url):
    with urlopen(url) as f:
        result = f.read().decode()
        return html.document_fromstring(result)


def is_latest(package, version):
    """Determine if +version+ is the latest version of +package+.

    Returns True if it is; False otherwise.
    """
    latest = list(reversed(sorted(all()[package])))[0]
    # print(f"  {package} {version} >= {latest}?")
    return loose_ge(version, latest)


def supported(package, version):
    """Determine if version +version+ of +package+ is still supported.

    Returns True if it is; False otherwise.
    """
    versions = all()[package]
    return any(V(version) >= V(v) for v in versions)


def unknown(package, _version):
    """Determine if it is unknown whether +_version+ of +package+ is supported.

    Returns True if it is; False otherwise.
    """
    return len(all()[package]) == 0


def loose_ge(v1, v2):
    v1_parts = len(v1.split('.'))
    v2_parts = len(v2.split('.'))
    parts_to_keep = min(v1_parts, v2_parts)
    v1 = '.'.join(v1.split('.')[:parts_to_keep])
    v2 = '.'.join(v2.split('.')[:parts_to_keep])
    return V(v1) >= V(v2)


def all():
    """Return information about all software we check."""
    return {
        'clang': clang(),
        'gcc': gcc(),
        'python3': python3(),
        'ruby': ruby(),
    }


def clang():
    """Return supported versions of Clang."""
    versions = _get_html(urls['clang']).xpath('//a[starts-with(@href, "https://releases.llvm.org/")]/b/text()')
    assert len(versions) > 0, "no Clang versions found."
    return versions


def gcc():
    """Return supported versions of GCC."""
    return [version.split()[1] for version in _get_html(urls['gcc']).xpath('//td/dl/dt/span[@class="version"]/a/text()')]


def python3():
    """Return supported versions of Python3."""
    return _get_html(urls['python3']).xpath('//*[@id="supported-versions"]//table//tr/td[1]/p[not(contains(text(), "main")]/text()')


def ruby():
    """Return supported versions of Ruby."""
    return [version.split()[1] for version in _get_html(urls['ruby']).xpath('//div[@id="content-wrapper"]/div/p[contains(text(), "maintenance")]/preceding-sibling::h3/text()')]
