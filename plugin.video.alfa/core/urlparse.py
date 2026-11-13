from __future__ import absolute_import, unicode_literals
import sys
import math
import re
from collections import OrderedDict
try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

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


def urlencode(query, safe="", quote_via=None, doseq=False, encoding=None, errors=None):
    if PY3:
        if quote_via:
            return _urllib.urlencode(query, doseq=doseq, safe=safe, quote_via=quote_via,
                                     encoding=encoding, errors=errors)
        else:
            return _urllib.urlencode(query, doseq=doseq, safe=safe,
                                     encoding=encoding, errors=errors)
    else:
        return _urllib.urlencode(query, doseq=doseq)


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


_TEXT = type(u"")
try:
    _INTEGER_TYPES = (int, long)
except NameError:
    _INTEGER_TYPES = (int,)


def _text(value):
    if isinstance(value, _TEXT):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise TypeError("Expected text or UTF-8 bytes")


def _query_value(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        raise TypeError("Convert boolean query values explicitly")
    if isinstance(value, _INTEGER_TYPES):
        return _TEXT(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("Query numbers must be finite")
        return _TEXT(value)
    return _text(value)


def _decoded_pairs(value):
    """Decode percent-escaped UTF-8 consistently on Python 2 and 3."""
    value = _text(value)
    if not PY3:
        value = value.encode("utf-8")
    return [(_text(key), _text(entry))
            for key, entry in parse_qsl(value, keep_blank_values=True)]


class _QueryList(list):
    """Validate every mutation before notifying the owning query."""

    def __init__(self, values, changed):
        list.__init__(self, [_query_value(v) for v in values])
        self._changed = changed

    def _replace(self, values, change=None):
        values = [_query_value(v) for v in values]
        previous = list(self)
        if previous == values:
            return
        list.__setitem__(self, slice(None), values)
        self._changed(self, previous, change)

    def append(self, value):
        value = _query_value(value)
        self._replace(list(self) + [value], ("splice", len(self), len(self), [value]))

    def extend(self, values):
        values = [_query_value(v) for v in values]
        self._replace(list(self) + values, ("splice", len(self), len(self), values))

    def insert(self, index, value):
        values = list(self)
        value = _query_value(value)
        values.insert(index, value)
        position = min(index, len(self)) if index >= 0 else max(0, len(self) + index)
        self._replace(values, ("splice", position, position, [value]))

    def __setitem__(self, index, value):
        values = list(self)
        values[index] = ([_query_value(v) for v in value]
                         if isinstance(index, slice) else _query_value(value))
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            added = len(values) - len(self) + max(0, stop - start)
            change = (("splice", start, stop, values[start:start + added])
                      if step == 1 else None)
        else:
            position = int(index) if index >= 0 else len(self) + int(index)
            change = ("splice", position, position + 1, [values[position]])
        self._replace(values, change)

    def __delitem__(self, index):
        values = list(self)
        del values[index]
        positions = (list(range(*index.indices(len(self))))
                     if isinstance(index, slice) else
                     [int(index) if index >= 0 else len(self) + int(index)])
        self._replace(values, ("delete", positions))

    def __setslice__(self, start, stop, values):
        self.__setitem__(slice(start, stop), values)

    def __delslice__(self, start, stop):
        self.__delitem__(slice(start, stop))

    def __iadd__(self, values):
        self.extend(values)
        return self

    def __imul__(self, count):
        values = list(self) * count
        change = (("splice", len(self), len(self), values[len(self):])
                  if values else ("delete", list(range(len(self)))))
        self._replace(values, change)
        return self

    def pop(self, index=-1):
        values = list(self)
        result = values.pop(index)
        position = index if index >= 0 else len(self) + index
        self._replace(values, ("delete", [position]))
        return result

    def remove(self, value):
        values = list(self)
        position = values.index(value)
        values.remove(value)
        self._replace(values, ("delete", [position]))

    def clear(self):
        self._replace([], ("delete", list(range(len(self)))))

    def reverse(self):
        self._replace(list(reversed(self)))

    def sort(self, *args, **kwargs):
        values = list(self)
        values.sort(*args, **kwargs)
        self._replace(values)


class QueryParams(MutableMapping):
    """Case-sensitive parameters with ordered occurrences and validated lists."""

    def __init__(self, values=()):
        self._data = OrderedDict()
        self._pairs = []
        self._raw = None
        self.dirty = False
        if isinstance(values, QueryParams):
            for key, value in values.items():
                self[key] = list(value) if isinstance(value, list) else value
            self._pairs = list(values._pairs)
            self._raw = values._raw
            self.dirty = values.dirty
        elif hasattr(values, "items"):
            self.update(values)
        else:
            pairs = []
            for key, value in values:
                key = _text(key)
                if isinstance(value, list):
                    value = [_query_value(v) for v in value]
                    if key not in self:
                        self[key] = value
                    else:
                        for entry in value or [""]:
                            self.add(key, entry)
                    pairs.extend((key, entry) for entry in value or [""])
                else:
                    value = _query_value(value)
                    self.add(key, value)
                    pairs.append((key, value))
            self._pairs = pairs

    def update(self, values=(), **kwargs):
        pairs = list(values.items() if hasattr(values, "items") else values)
        pairs.extend(kwargs.items())
        prepared = [(_text(k), [_query_value(v) for v in value]
                     if isinstance(value, list) else _query_value(value))
                    for k, value in pairs]
        for key, value in prepared:
            self[key] = value

    @classmethod
    def from_string(cls, query):
        result = cls(_decoded_pairs(query))
        result._raw = _text(query)
        result.dirty = False
        return result

    def __getitem__(self, key):
        return self._data[_text(key)]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def _values(self, value):
        return (list(value) or [""]) if isinstance(value, list) else [value]

    def _sync(self, key, previous, values, change=None):
        old, new = self._values(previous), self._values(values)
        positions = [i for i, pair in enumerate(self._pairs) if pair[0] == key]
        if not previous or not values:
            first = positions[0]
            self._pairs = [p for p in self._pairs if p[0] != key]
            self._pairs[first:first] = [(key, v) for v in new]
            self.dirty = True
            return
        if change is not None:
            if change[0] == "delete":
                removed = set(positions[i] for i in change[1])
                self._pairs = [p for i, p in enumerate(self._pairs) if i not in removed]
            else:
                _, start, stop, added = change
                insertion = positions[start] if start < len(positions) else positions[-1] + 1
                removed = set(positions[start:stop])
                self._pairs = [p for i, p in enumerate(self._pairs) if i not in removed]
                self._pairs[insertion:insertion] = [(key, v) for v in added]
            self.dirty = True
            return
        if len(old) == len(new):
            for position, value in zip(positions, new):
                self._pairs[position] = (key, value)
            self.dirty = True
            return
        prefix = 0
        while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
            prefix += 1
        suffix = 0
        while (suffix < min(len(old), len(new)) - prefix
               and old[-1 - suffix] == new[-1 - suffix]):
            suffix += 1
        stop = len(old) - suffix
        insertion = positions[prefix] if prefix < len(positions) else positions[-1] + 1
        removed = set(positions[prefix:stop])
        self._pairs = [p for i, p in enumerate(self._pairs) if i not in removed]
        self._pairs[insertion:insertion] = [(key, v) for v in new[prefix:len(new) - suffix]]
        self.dirty = True

    def _list_changed(self, key, value, previous, change):
        if self._data.get(key) is value:
            self._sync(key, previous, value, change)

    def __setitem__(self, key, value):
        key = _text(key)
        if key in self._data and value is self._data[key] and isinstance(value, _QueryList):
            return
        if isinstance(value, list):
            value = _QueryList(
                value, lambda current, old, change:
                self._list_changed(key, current, old, change))
        else:
            value = _query_value(value)
        positions = [i for i, p in enumerate(self._pairs) if p[0] == key]
        insertion = positions[0] if positions else len(self._pairs)
        self._pairs = [p for p in self._pairs if p[0] != key]
        self._pairs[insertion:insertion] = [(key, v) for v in self._values(value)]
        self._data[key] = value
        self.dirty = True

    def __delitem__(self, key):
        key = _text(key)
        del self._data[key]
        self._pairs = [p for p in self._pairs if p[0] != key]
        self.dirty = True

    def add(self, key, value):
        key, value = _text(key), _query_value(value)
        if key not in self:
            self[key] = value
        elif isinstance(self[key], list):
            self[key].append(value)
        else:
            self[key] = [self[key], value]
        return self

    def get_all(self, key):
        if key not in self:
            return []
        value = self[key]
        return list(value) if isinstance(value, list) else [value]

    def to_string(self):
        if self._raw is not None and not self.dirty:
            return self._raw
        pairs = self._pairs
        if not PY3:
            pairs = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in pairs]
        return urlencode(pairs)

    def copy(self):
        return QueryParams(self)


class Headers(MutableMapping):
    """Single-valued case-insensitive names, with optional original spelling."""

    _name = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")

    def __init__(self, values=()):
        self._data = OrderedDict()
        self.dirty = False
        self._raw = None
        if isinstance(values, Headers):
            self._data = values._data.copy()
            self._raw, self.dirty = values._raw, values.dirty
        else:
            self.update(values)

    @classmethod
    def from_string(cls, headers):
        result = cls(_decoded_pairs(headers))
        result._raw = _text(headers)
        result.dirty = False
        return result

    def __getitem__(self, key):
        return self._data[_text(key).lower()][1]

    @classmethod
    def _entry(cls, key, value):
        key, value = _text(key), _text(value)
        if not cls._name.match(key) or "\r" in key or "\n" in key:
            raise ValueError("Invalid header name")
        if "\r" in value or "\n" in value:
            raise ValueError("Header values cannot contain newlines")
        return key, value

    def __setitem__(self, key, value):
        key, value = self._entry(key, value)
        self._data[key.lower()] = (key, value)
        self.dirty = True

    def update(self, values=(), **kwargs):
        pairs = list(values.items() if hasattr(values, "items") else values)
        pairs.extend(kwargs.items())
        prepared = [self._entry(k, v) for k, v in pairs]
        for key, value in prepared:
            self._data[key.lower()] = (key, value)
            self.dirty = True

    def __delitem__(self, key):
        del self._data[_text(key).lower()]
        self.dirty = True

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def to_string(self, preserve_case=False):
        if self._raw is not None and not self.dirty and preserve_case:
            return self._raw
        pairs = [(original if preserve_case else key, value)
                 for key, (original, value) in self._data.items()]
        if not PY3:
            pairs = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in pairs]
        return urlencode(pairs)

    def copy(self):
        return Headers(self)


class AlfaURL(object):
    """Opt-in URL editing. Ordinary strings never implicitly parse Kodi headers."""

    def __init__(self, url):
        self._original = _text(url)
        self._parts = urlsplit(self._original)
        self.query = QueryParams.from_string(self._parts.query)
        self.headers = Headers()
        self._changed = False
        self._kodi = False

    @classmethod
    def from_kodi_string(cls, url):
        parts = _text(url).split("|", 1)
        result = cls(parts[0])
        result._kodi = len(parts) == 2
        if result._kodi:
            result.headers = Headers.from_string(parts[1])
        return result

    @property
    def scheme(self):
        return self._parts.scheme

    @property
    def netloc(self):
        return self._parts.netloc

    @property
    def path(self):
        return self._parts.path

    @property
    def fragment(self):
        return self._parts.fragment

    def _http(self):
        if self.scheme not in ("http", "https") or not self.netloc:
            raise ValueError("This operation requires an absolute HTTP(S) URL")

    def append_path(self, *paths, **options):
        self._http()
        path = self.path
        for part in paths:
            part = _text(part)
            if "?" in part or "#" in part or urlsplit(part).scheme or part.startswith("//"):
                raise ValueError("Pass URLs to resolve(), and queries separately")
            if part:
                path = "/".join((path.rstrip("/"), part.lstrip("/")))
        trailing = options.pop("trailing_slash", None)
        if options:
            raise TypeError("Unknown path options")
        if trailing is not None:
            path = path.rstrip("/") + ("/" if trailing else "")
        self._changed = self._changed or path != self.path
        self._parts = self._parts._replace(path=path)
        return self

    def set_query(self, values):
        self._http()
        self.query = (values.copy() if isinstance(values, QueryParams)
                      else QueryParams.from_string(values) if isinstance(values, (str, _TEXT, bytes))
                      else QueryParams(values))
        self._changed = True
        return self

    def add_header(self, name, value):
        self._http()
        self.headers[name] = value
        self._kodi = True
        return self

    def copy(self):
        result = AlfaURL(self._original)
        result._parts = self._parts
        result.query = self.query.copy()
        result.headers = self.headers.copy()
        result._changed, result._kodi = self._changed, self._kodi
        return result

    def resolve(self, reference):
        self._http()
        target = reference if isinstance(reference, AlfaURL) else AlfaURL(reference)
        result = AlfaURL(urljoin(self._main_string(), target._main_string()))
        if target._kodi:
            result.headers, result._kodi = target.headers.copy(), True
        elif url_domain(result._main_string()) == url_domain(self._main_string()):
            result.headers, result._kodi = self.headers.copy(), self._kodi
        return result

    def _main_string(self):
        if not self._changed and not self.query.dirty:
            return self._original
        return urlunsplit(self._parts._replace(query=self.query.to_string()))

    def to_string(self, preserve_header_case=True):
        url = self._main_string()
        if self._kodi or len(self.headers):
            url += "|" + self.headers.to_string(preserve_case=preserve_header_case)
        return url

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        value = self.to_string()
        return value if PY3 else value.encode("utf-8")


def build_url(base, *paths, **options):
    """Build an endpoint; paths append to the base instead of resolving links."""
    result = AlfaURL(base)
    result.append_path(*paths, trailing_slash=options.pop("trailing_slash", None))
    if "query" in options:
        result.set_query(options.pop("query"))
    if "fragment" in options:
        result._parts = result._parts._replace(fragment=_text(options.pop("fragment")))
        result._changed = True
    if options:
        raise TypeError("Unknown URL options")
    return result.to_string()


def update_query(url, values=(), **parameters):
    result = AlfaURL(url)
    result._http()
    result.query.update(values)
    result.query.update(parameters)
    return result.to_string()


def add_url_headers(url, headers, *additional_headers):
    if url == "":
        return url
    result = AlfaURL.from_kodi_string(url)
    for mapping in (headers,) + additional_headers:
        for name, value in mapping.items():
            result.add_header(name, value)
    return result.to_string()


def append_path_suffix(url, suffix):
    """Extend a filename or route identifier, without introducing a separator."""
    result = AlfaURL(url)
    result._http()
    suffix = _text(suffix)
    if "?" in suffix or "#" in suffix:
        raise ValueError("Pass query and fragment separately")
    result._parts = result._parts._replace(path=result.path + suffix)
    result._changed = bool(suffix)
    return result.to_string()


def append_query(url, values):
    """Append parameters, preserving already serialized query fragments."""
    result = AlfaURL(url)
    result._http()
    additions = (_text(values) if isinstance(values, (str, _TEXT, bytes))
                 else QueryParams(values).to_string())
    if additions:
        query = result._parts.query
        result.set_query("&".join((query, additions)) if query else additions)
    return result.to_string()


def build_page_url(url, reference):
    """Apply a channel's relative pagination path/query to its listing URL."""
    result = AlfaURL(url)
    result._http()
    reference = _text(reference)
    if reference.startswith("&"):
        reference = "?" + reference[1:]
    parts = urlsplit(reference)
    if parts.scheme or parts.netloc:
        raise ValueError("Pagination patterns must be relative")
    if parts.path:
        result.append_path(parts.path)
    if parts.query:
        result.query.update(QueryParams.from_string(parts.query))
    if parts.fragment:
        result._parts = result._parts._replace(fragment=parts.fragment)
        result._changed = True
    return result.to_string()


def update_page_url(url, patterns, page, fallback=True):
    """Apply legacy page patterns without confusing query delimiters and paths."""
    result = AlfaURL(url)
    result._http()
    patterns = list(patterns)
    if not patterns:
        raise ValueError("At least one pagination pattern is required")
    matched = False
    for pattern, template in patterns:
        reference = _text(template) % _TEXT(page)
        if reference.startswith(("?", "&")):
            query = result.query.to_string()
            if re.search(pattern, "?" + query) or re.search(pattern, "&" + query):
                result.query.update(QueryParams.from_string(reference[1:]))
                matched = True
        else:
            if re.search(pattern, result.path) or re.search(pattern, result.path.rstrip("/")):
                path = result.path.rstrip("/")
                if not re.search(pattern, path):
                    path = result.path
                path = re.sub(pattern, reference, path)
                result._parts = result._parts._replace(path=path)
                result._changed = True
                matched = True
            query = result.query.to_string()
            if re.search(pattern, query):
                result.set_query(re.sub(pattern, reference, query))
                matched = True
    if not matched and fallback:
        return build_page_url(url, _text(patterns[0][1]) % _TEXT(page))
    return result.to_string()


def quote_path(value, safe=""):
    """Encode a dynamic path component as UTF-8, including on Python 2."""
    value = _text(value)
    return quote(value if PY3 else value.encode("utf-8"), safe=safe)
