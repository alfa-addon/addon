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


def urlencode(query, safe="", quote_via=None):
    if PY3:
        if quote_via:
            return _urllib.urlencode(query, safe=safe, quote_via=quote_via)
        else:
            return _urllib.urlencode(query, safe=safe)
    else:
        return _urllib.urlencode(query)


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
):
    if PY3:
        return _urlparse.parse_qs(
            query_str,
            keep_blank_values=keep_blank_values,
            strict_parsing=strict_parsing,
            encoding=encoding,
            errors=errors,
        )
    else:
        return _urlparse.parse_qs(
            query_str,
            keep_blank_values=keep_blank_values,
            strict_parsing=strict_parsing,
        )


def parse_qsl(
    query_str,
    keep_blank_values=False,
    strict_parsing=False,
    encoding="utf-8",
    errors="replace",
):
    if PY3:
        return _urlparse.parse_qsl(
            query_str,
            keep_blank_values=keep_blank_values,
            strict_parsing=strict_parsing,
            encoding=encoding,
            errors=errors,
        )
    else:
        return _urlparse.parse_qsl(
            query_str,
            keep_blank_values=keep_blank_values,
            strict_parsing=strict_parsing,
        )


def quote(string, safe="", encoding=None, errors=None):
    if PY3:
        return _urllib.quote(string, safe=safe, encoding=encoding, errors=errors)
    else:
        return _urllib.quote(string, safe=safe)


def quote_plus(string, safe="", encoding=None, errors=None):
    if PY3:
        return _urllib.quote_plus(string, safe=safe, encoding=encoding, errors=errors)
    else:
        return _urllib.quote_plus(string, safe=safe)


def unquote(string, encoding="utf-8", errors="replace"):
    if PY3:
        return _urllib.unquote(string, encoding, errors)
    else:
        return _urllib.unquote(string)


def unquote_plus(string, encoding="utf-8", errors="replace"):
    if PY3:
        return _urllib.unquote_plus(string, encoding, errors)
    else:
        return _urllib.unquote_plus(string)


def urlunparse(components):
    return _urlparse.urlunparse(components)


def urlunsplit(components):
    return _urlparse.urlunsplit(components)
