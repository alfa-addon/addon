from __future__ import absolute_import, unicode_literals
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    import urllib.parse as _urllib
    import urllib.parse as _urlparse
else:
    import urllib as _urllib
    import urlparse as _urlparse


def urljoin(base, *paths, allow_fragments=True):
    joined_url = ""

    for path in paths:
        _urlparse.urljoin(joined_url, path, allow_fragments)

    return joined_url


def urlencode(query, safe_chars="", quote_via=None):
    if quote_via:
        return _urllib.urlencode(query, safe=safe_chars, quote_via=quote_via)
    else:
        return _urllib.urlencode(query, safe=safe_chars)


def urlparse(url, scheme="", allow_fragments=True):
    return _urlparse.urlparse(url, scheme, allow_fragments)


def urlsplit(url, scheme="", allow_fragments=True):
    return _urlparse.urlsplit(url, scheme, allow_fragments)


def parse_qs(query_str):
    return {x: y[0] for x, y in _urlparse.parse_qs(query_str).items()}


def parse_qsl(query_str):
    return _urlparse.parse_qsl(query_str)


def quote(string, safe="", encoding=None, errors=None):
    return _urllib.quote(string, safe=safe, encoding=encoding, errors=errors)


def quote_plus(string, safe="", encoding=None, errors=None):
    return _urllib.quote_plus(string, safe=safe, encoding=encoding, errors=errors)


def unquote(string):
    return _urllib.unquote(string)


def unquote_plus(string):
    return _urllib.unquote_plus(string)


def urlunparse(components):
    return _urlparse.urlunparse(components)


def urlunsplit(components):
    return _urlparse.urlunsplit(components)
