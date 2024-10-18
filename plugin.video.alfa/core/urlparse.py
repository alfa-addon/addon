from __future__ import absolute_import, unicode_literals
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    import urllib.parse as _urllib
    import urllib.parse as _urlparse
else:
    import urllib as _urllib
    import urlparse as _urlparse


def urljoin(base, *paths, **kwargs):
    joined_url = base
    allow_fragments = kwargs.get("allow_fragments", True)
    for path in paths:
        joined_url = _urlparse.urljoin(joined_url, path, allow_fragments)
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


def parse_qs(
    query_str,
    keep_blank_values=False,
    strict_parsing=False,
    encoding="utf-8",
    errors="replace",
    max_num_fields=None,
    separator="&",
):
    return _urlparse.parse_qs(
        query_str,
        keep_blank_values,
        strict_parsing,
        encoding,
        errors,
        max_num_fields,
        separator,
    )


def parse_qsl(
    query_str,
    keep_blank_values=False,
    strict_parsing=False,
    encoding="utf-8",
    errors="replace",
    max_num_fields=None,
    separator="&",
):
    return _urlparse.parse_qsl(
        query_str,
        keep_blank_values,
        strict_parsing,
        encoding,
        errors,
        max_num_fields,
        separator,
    )


def quote(string, safe="", encoding=None, errors=None):
    return _urllib.quote(string, safe=safe, encoding=encoding, errors=errors)


def quote_plus(string, safe="", encoding=None, errors=None):
    return _urllib.quote_plus(string, safe=safe, encoding=encoding, errors=errors)


def unquote(string, encoding="utf-8", errors="replace"):
    return _urllib.unquote(string, encoding, errors)


def unquote_plus(string, encoding="utf-8", errors="replace"):
    return _urllib.unquote_plus(string, encoding, errors)


def urlunparse(components):
    return _urlparse.urlunparse(components)


def urlunsplit(components):
    return _urlparse.urlunsplit(components)
