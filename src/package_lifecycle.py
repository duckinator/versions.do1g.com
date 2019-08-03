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


def is_latest(package, version):
    latest = list(reversed(sorted(all()[package])))[0]
    print("  {} >= {}?".format(version, latest))
    return loose_ge(version, latest)


def supported(package, version):
    versions = all()[package]
    return any([V(version) >= V(v) for v in versions])


def outdated(package, version):
    versions = all()[package]

    # Ignore anything with only 1 version available.
    #if len(versions) == 1:
    #    return False

    return number_newer(package, version) >= 2


def _loose_compare(v1, v2, fn):
    v1_parts = len(v1.split('.'))
    v2_parts = len(v2.split('.'))
    parts_to_keep = min(v1_parts, v2_parts)
    v1 = '.'.join(v1.split('.')[:parts_to_keep])
    v2 = '.'.join(v2.split('.')[:parts_to_keep])
    return fn(V(v1), V(v2))


def loose_ge(v1, v2):
    return _loose_compare(v1, v2, lambda a, b: a >= b)


def loose_eq(v1, v2):
    return _loose_compare(v1, v2, lambda a, b: a == b)


def loose_gt(v1, v2):
    return _loose_compare(v1, v2, lambda a, b: a > b)


def loose_lt(v1, v2):
    return _loose_compare(v1, v2, lambda a, b: a < b)


# The number of all versions for `package` which are newer than `version`.
def number_newer(package, version):
    versions = list(reversed(sorted(all()[package])))
    for idx in range(0, len(versions)):
        if loose_gt(version, versions[idx]):
            return idx

    # If we get here, _every_ version we know of is older.
    return len(versions)


# The percentage of all versions for `package` which are newer than `version`.
def percent_newer(package, version):
    num_newer = number_newer(package, version)
    num_versions = len(all()[package])
    return int(float(num_newer) / num_versions * 100)


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
    versions = _get_html(urls['python3']).xpath('//div[@id="status-of-python-branches"]/table[1]//tr/td[1][starts-with(text(), "3.")]/text()')
    # FIXME: go based off which versions have the 'prerelease' status, instead
    #        of hard-coding things.
    versions = filter(lambda x: not x == '3.8', versions)
    return list(versions)


def ruby():
    versions = _get_html(urls['ruby']).xpath('//div[@id="content-wrapper"]/div/p[contains(text(), "maintenance")]/preceding-sibling::h3/text()')
    return _normalize(versions)
