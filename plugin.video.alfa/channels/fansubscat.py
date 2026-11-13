# -*- coding: utf-8 -*-
# Fansubs.cat - Anime subtitulat en català per a Alfa

import re
import traceback
from urllib.parse import urlencode

from channelselector import get_thumb
from core import httptools, scrapertools, servertools, urlparse
from core.item import Item
from platformcode import logger
from modules import autoplay, filtertools

host = "https://anime.fansubs.cat/"
api_file = urlparse.urljoin(host, "get_file_data.php")
list_language = ["CAT"]
list_quality = []


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, ["directo"], list_quality)
    return [
        Item(channel=item.channel, action="list_all", title="Catàleg d'anime",
             url=host, thumbnail=get_thumb("channels_anime.png")),
        Item(channel=item.channel, action="newest", title="Darrers capítols",
             url=host, thumbnail=get_thumb("now_playing.png")),
        Item(channel=item.channel, action="search", title="Cerca",
             url=host, thumbnail=get_thumb("search.png"))
    ]


def _download(url, post=None, referer=None):
    headers = {"Referer": referer or host, "Origin": "https://anime.fansubs.cat"}
    return httptools.downloadpage(url, post=post, headers=headers, timeout=20)


def _clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = scrapertools.htmlclean(value)
    return re.sub(r"\s+", " ", value).strip()


def _attr(tag, name):
    match = re.search(r'\b%s\s*=\s*["\']([^"\']*)["\']' % re.escape(name), tag, re.I)
    return scrapertools.unescape(match.group(1)) if match else ""


def _absolute(url):
    return urlparse.urljoin(host, url or "")


def list_all(item):
    logger.info()
    itemlist = []
    try:
        data = _download(item.url or host).data
        # Les targetes del catàleg enllacen directament a fitxes /slug/catsub.
        pattern = r'<a\b([^>]*href=["\'][^"\']+/catsub[^"\']*["\'][^>]*)>(.*?)</a>'
        seen = set()
        for attrs, body in re.findall(pattern, data, re.I | re.S):
            url = _absolute(_attr(attrs, "href"))
            if url in seen:
                continue
            seen.add(url)
            img = re.search(r'<img\b[^>]*>', body, re.I | re.S)
            title = _attr(img.group(0), "alt") if img else ""
            thumb = _attr(img.group(0), "src") if img else ""
            if not title:
                title = _clean(body)
            if not title:
                continue
            itemlist.append(Item(channel=item.channel, action="episodios", title=title,
                                 url=url, thumbnail=_absolute(thumb) if thumb else "",
                                 contentSerieName=title, contentType="tvshow"))
        if not itemlist:
            logger.debug("Fansubs.cat: no s'han trobat targetes al catàleg")
    except Exception:
        logger.error(traceback.format_exc())
    return itemlist


def newest(item):
    logger.info()
    # El agregador de novedades pasa una categoría; el menú pasa un Item.
    if not isinstance(item, Item):
        if item != "anime":
            return []
        item = Item(channel="fansubscat", url=host)
    itemlist = []
    try:
        data = _download(host).data
        # Darrers capítols: els enllaços de capítol apunten a fitxes d'anime.
        section = re.search(r'Darrers cap[ií]tols(.*?)(?:Animes d|<footer)', data, re.I | re.S)
        block = section.group(1) if section else data
        seen = set()
        for href, title in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', block, re.I | re.S):
            label = _clean(title)
            if not label or "cap." not in label.lower() or "/catsub" not in href:
                continue
            url = _absolute(href)
            if url in seen:
                continue
            seen.add(url)
            itemlist.append(Item(channel=item.channel, action="episodios", title=label,
                                 url=url, contentSerieName=label, contentType="tvshow"))
    except Exception:
        logger.error(traceback.format_exc())
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    try:
        data = _download(item.url, referer=item.url).data
        # Cada versió/fansub té els seus file-launcher. El file_id és el que
        # el web envia a get_file_data.php per obtenir les fonts de vídeo.
        versions = re.findall(r'<div\b[^>]*class=["\'][^"\']*file-launcher[^"\']*["\'][^>]*>', data, re.I)
        for tag in versions:
            file_id = _attr(tag, "data-file-id")
            if not file_id:
                continue
            title = _attr(tag, "data-title") or _attr(tag, "data-episode-title")
            if not title:
                title = "Capítol"
            episode = scrapertools.find_single_match(title, r'(?i)(?:cap[ií]tol|episodi)\s*(\d+)')
            info = dict(item.infoLabels or {})
            if episode:
                try:
                    info["episode"] = int(episode)
                    info["season"] = 1
                except Exception:
                    pass
            itemlist.append(Item(channel=item.channel, action="findvideos",
                                 title=title, url=item.url, thumbnail=item.thumbnail,
                                 infoLabels=info, extra=file_id, contentType="episode",
                                 contentSerieName=item.contentSerieName or item.title))
    except Exception:
        logger.error(traceback.format_exc())
    return itemlist


def _collect_urls(value, found):
    if isinstance(value, dict):
        for key, val in value.items():
            if isinstance(val, str) and val.startswith(("http://", "https://")):
                if any(ext in val.lower() for ext in (".m3u8", ".mp4", ".mkv", ".webm")) or key.lower() in ("url", "file", "src", "link", "direct_url"):
                    found.append((key, val))
            else:
                _collect_urls(val, found)
    elif isinstance(value, list):
        for val in value:
            _collect_urls(val, found)


def findvideos(item):
    logger.info()
    itemlist = []
    try:
        file_id = item.extra
        if not file_id:
            return []
        response = _download(api_file, post=urlencode({"file_id": file_id}), referer=item.url)
        payload = response.json
        sources = payload.get("data_sources", []) if isinstance(payload, dict) else []
        found = []
        _collect_urls(sources, found)
        seen = set()
        for key, url in found:
            if url in seen:
                continue
            seen.add(url)
            itemlist.append(Item(channel=item.channel, action="play", title="Fansubs.cat - %s" % key,
                                 url=url, language="CAT", infoLabels=item.infoLabels))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title)
        itemlist = filtertools.get_links(itemlist, item, list_language)
        autoplay.start(itemlist, item)
    except Exception:
        logger.error(traceback.format_exc())
    return itemlist


def search(item, texto):
    logger.info()
    texto = (texto or "").strip()
    if not texto:
        return []
    # La cerca del web es una cerca GET. Mantenim el text codificat.
    item.url = host + "?" + urlencode({"q": texto})
    return list_all(item)
