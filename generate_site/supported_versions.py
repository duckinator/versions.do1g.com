"""Fetches lists of supported versions for various software."""

from functools import lru_cache as memoize
from urllib.request import urlopen
from lxml import html
from pkg_resources import parse_version as V


urls = {
    'clang': 'https://llvm.org',
    'gcc': 'https://gcc.gnu.org/',
    'python3': 'https://devguide.python.org/#status-of-python-branches',
    'ruby': 'https://www.ruby-lang.org/en/downloads/branches/',
}


package_names = urls.keys()


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


def is_latest(package, version):
    """Determine if +version+ is the latest version of +package+.

    Returns True if it is; False otherwise.
    """
    latest = list(reversed(sorted(all()[package])))[0]
    print("  {} >= {}?".format(version, latest))
    return loose_ge(version, latest)


def supported(package, version):
    """Determine if version +version+ of +package+ is still supported.

    Returns True if it is; False otherwise.
    """
    versions = all()[package]
    return any([V(version) >= V(v) for v in versions])


def outdated(package, version):
    """Determine if version +version+ of +package+ is supported but not latest.

    Returns True if it is; False otherwise.
    """
    # versions = all()[package]

    # Ignore anything with only 1 version available.
    # if len(versions) == 1:
    #     return False

    return number_newer(package, version) >= 2


def unknown(package, _version):
    """Determine if it is unknown whether +_version+ of +package+ is supported.

    Returns True if it is; False otherwise.
    """
    return len(all()[package]) == 0


def _loose_compare(v1, v2, fn):
    v1_parts = len(v1.split('.'))
    v2_parts = len(v2.split('.'))
    parts_to_keep = min(v1_parts, v2_parts)
    v1 = '.'.join(v1.split('.')[:parts_to_keep])
    v2 = '.'.join(v2.split('.')[:parts_to_keep])
    return fn(V(v1), V(v2))


def loose_ge(v1, v2):
    """TODO: Figure out wtf this does, again."""
    return _loose_compare(v1, v2, lambda a, b: a >= b)


def loose_eq(v1, v2):
    """TODO: Figure out wtf this does, again."""
    return _loose_compare(v1, v2, lambda a, b: a == b)


def loose_gt(v1, v2):
    """TODO: Figure out wtf this does, again."""
    return _loose_compare(v1, v2, lambda a, b: a > b)


def loose_lt(v1, v2):
    """TODO: Figure out wtf this does, again."""
    return _loose_compare(v1, v2, lambda a, b: a < b)


def number_newer(package, version):
    """Return number of versions of `package` which are newer than `version`."""
    versions = list(reversed(sorted(all()[package])))
    for idx in range(0, len(versions)):
        if loose_gt(version, versions[idx]):
            return idx

    # If we get here, _every_ version we know of is older.
    return len(versions)


def percent_newer(package, version):
    """Return percentage of `package` versions which are newer than `version`."""
    num_newer = number_newer(package, version)
    num_versions = len(all()[package])
    return int(float(num_newer) / num_versions * 100)


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
    versions = _get_html(urls['clang']).xpath('//a[starts-with(@href, "/releases/download.html#")]/b/text()')
    return _normalize(versions)


def gcc():
    """Return supported versions of GCC."""
    versions = _get_html(urls['gcc']).xpath('//td/dl/dt/span[@class="version"]/a/text()')
    return _normalize(versions)


def python3():
    """Return supported versions of Python3."""
    versions = _get_html(urls['python3']).xpath('//div[@id="status-of-python-branches"]/table[1]//tr/td[1][starts-with(text(), "3.")]/text()')
    # FIXME: figure out how to automate removing unreleased versions, instead
    #        of hard-coding things.
    versions = filter(lambda x: not x == 'master', versions)
    return list(versions)


def ruby():
    """Return supported versions of Ruby."""
    versions = _get_html(urls['ruby']).xpath('//div[@id="content-wrapper"]/div/p[contains(text(), "maintenance")]/preceding-sibling::h3/text()')
    # FIXME: go based off which versions have a "preview" status, instead
    #        of hard-coding things.
    versions = filter(lambda x: not x == 'Ruby 2.7', versions)
    return _normalize(versions)
