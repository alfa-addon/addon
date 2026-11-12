from __future__ import absolute_import, unicode_literals
import sys

PY3 = sys.version_info > (3,)

if PY3:
    import urllib.parse as _urllib
    import urllib.parse as _urlparse
    import urllib.error as urlerror
    import urllib.request as urlrequest
    from html import unescape as _unescape
    unescape = _unescape
else:
    import urllib as _urllib
    import urlparse as _urlparse
    import urllib2 as urlrequest
    import urllib2 as urlerror
    from HTMLParser import HTMLParser as _HTMLParser
    unescape = _HTMLParser().unescape


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


def normalize_domain(domain):
    """Remove root slashes from HTTP(S) domains, not from content URLs."""
    if not isinstance(domain, (str, type(u""))):
        return domain
    try:
        parsed = _urlparse.urlsplit(domain)
    except ValueError:
        return domain
    if (parsed.scheme in ("http", "https") and parsed.netloc
            and not parsed.path.strip("/") and not parsed.query
            and not parsed.fragment):
        return domain.rstrip("/")
    return domain


def normalize_canonical(canonical):
    """Return a domain-normalized copy, keeping other options and list order."""
    result = dict(canonical)
    for key in ("host", "host_alt", "host_black_list", "host_alt_new", "host_alt_tor"):
        if key not in result:
            continue
        value = result[key]
        if isinstance(value, (list, tuple)):
            domains = []
            for domain in value:
                domain = normalize_domain(domain)
                if domain not in domains:
                    domains.append(domain)
            if key == "host_alt" and "host_alt_main" in result:
                index = result["host_alt_main"]
                if isinstance(index, int) and 0 <= index < len(value):
                    result["host_alt_main"] = domains.index(normalize_domain(value[index]))
            result[key] = domains
        else:
            result[key] = normalize_domain(value)
    return result


def url_domain(url):
    """Extract the HTTP(S) origin for canonical comparisons."""
    try:
        parsed = _urlparse.urlsplit(url)
    except (TypeError, ValueError):
        return ""
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return _urlparse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def replace_domain(url, domain):
    """Replace only the origin, preserving paths, queries and fragments."""
    if not url_domain(url) or not url_domain(domain):
        return url
    target = _urlparse.urlsplit(domain)
    if target.path.strip("/") or target.query or target.fragment:
        return url
    parsed = _urlparse.urlsplit(url)
    return _urlparse.urlunsplit((target.scheme, target.netloc, parsed.path,
                                parsed.query, parsed.fragment))


def format_channel_host(domain, reference):
    """Keep the channel's legacy separator until its URL builders migrate."""
    domain = normalize_domain(domain)
    if (isinstance(domain, (str, type(u""))) and domain
            and isinstance(reference, (str, type(u"")))
            and normalize_domain(domain + "/") == domain
            and reference.endswith("/")):
        return domain + "/"
    return domain


def format_channel_canonical(canonical, reference):
    """Adapt normalized metadata for channels that still concatenate hosts."""
    result = normalize_canonical(canonical)
    for key in ("host", "host_alt", "host_black_list", "host_alt_new", "host_alt_tor"):
        if key not in result:
            continue
        if isinstance(result[key], list):
            result[key] = [format_channel_host(domain, reference) for domain in result[key]]
        else:
            result[key] = format_channel_host(result[key], reference)
    return result
