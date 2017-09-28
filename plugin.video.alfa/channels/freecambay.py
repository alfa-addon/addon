# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger

host = "http://www.freecambay.com"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(action="lista", title="Nuevos Vídeos", url=host + "/latest-updates/"))
    itemlist.append(item.clone(action="lista", title="Mejor Valorados", url=host + "/top-rated/"))
    itemlist.append(item.clone(action="lista", title="Más Vistos", url=host + "/most-popular/"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host + "/categories/"))
    itemlist.append(item.clone(action="categorias", title="Modelos",
                               url=host + "/models/?mode=async&function=get_block&block_id=list_models_models" \
                                          "_list&sort_by=total_videos"))
    itemlist.append(item.clone(action="playlists", title="Listas", url=host + "/playlists/"))
    itemlist.append(item.clone(action="tags", title="Tags", url=host + "/tags/"))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto.replace("+", "-"))
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []

    # Descarga la pagina 
    data = httptools.downloadpage(item.url).data

    action = "play"
    if config.get_setting("menu_info", "freecambay"):
        action = "menu_info"

    # Extrae las entradas
    patron = '<div class="item.*?href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)"(.*?)<div class="duration">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, quality, duration in matches:
        if duration:
            scrapedtitle = "%s - %s" % (duration, scrapedtitle)
        if '>HD<' in quality:
            scrapedtitle += "  [COLOR red][HD][/COLOR]"

        itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))

    # Extrae la marca de siguiente página
    if item.extra:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?from_videos\+from_albums:(\d+)')
        if next_page:
            if "from_videos=" in item.url:
                next_page = re.sub(r'&from_videos=(\d+)', '&from_videos=%s' % next_page, item.url)
            else:
                next_page = "%s?mode=async&function=get_block&block_id=list_videos_videos_list_search_result" \
                            "&q=%s&category_ids=&sort_by=post_date&from_videos=%s" % (item.url, item.extra, next_page)
            itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))
    else:
        next_page = scrapertools.find_single_match(data, '<li class="next">.*?href="([^"]*)"')
        if next_page and not next_page.startswith("#"):
            next_page = urlparse.urljoin(host, next_page)
            itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))
        else:
            next_page = scrapertools.find_single_match(data, '<li class="next">.*?from:(\d+)')
            if next_page:
                if "from=" in item.url:
                    next_page = re.sub(r'&from=(\d+)', '&from=%s' % next_page, item.url)
                else:
                    next_page = "%s?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from=%s" % (
                        item.url, next_page)
                itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=next_page))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    # Descarga la pagina    
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas
    patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?src="([^"]+)".*?<div class="videos">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, videos in matches:
        if videos:
            scrapedtitle = "%s  (%s)" % (scrapedtitle, videos)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next">.*?from:(\d+)')
    if next_page:
        if "from=" in item.url:
            next_page = re.sub(r'&from=(\d+)', '&from=%s' % next_page, item.url)
        else:
            next_page = "%s&from=%s" % (item.url, next_page)
        itemlist.append(item.clone(action="categorias", title=">> Página Siguiente", url=next_page))

    return itemlist


def playlists(item):
    logger.info()
    itemlist = []

    # Descarga la pagina    
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas
    patron = '<div class="item.*?href="([^"]+)" title="([^"]+)".*?data-original="([^"]+)".*?<div class="videos">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, videos in matches:
        if videos:
            scrapedtitle = "%s  (%s)" % (scrapedtitle, videos)
        itemlist.append(item.clone(action="videos", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next">.*?href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(host, next_page)
        itemlist.append(item.clone(action="playlists", title=">> Página Siguiente", url=next_page))

    return itemlist


def videos(item):
    logger.info()
    itemlist = []

    # Descarga la pagina    
    data = httptools.downloadpage(item.url).data

    action = "play"
    if config.get_setting("menu_info", "freecambay"):
        action = "menu_info"
    # Extrae las entradas
    patron = '<a href="([^"]+)" class="item ".*?data-original="([^"]+)".*?<strong class="title">\s*([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.strip()
        itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next">.*?from:(\d+)')
    if next_page:
        if "from=" in item.url:
            next_page = re.sub(r'&from=(\d+)', '&from=%s' % next_page, item.url)
        else:
            next_page = "%s?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by" \
                        "=added2fav_date&&from=%s" % (item.url, next_page)
        itemlist.append(item.clone(action="videos", title=">> Página Siguiente", url=next_page))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '(?:video_url|video_alt_url[0-9]*)\s*:\s*\'([^\']+)\'.*?(?:video_url_text|video_alt_url[0-9]*_text)\s*:\s*\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    if not matches:
        patron = '<iframe.*?height="(\d+)".*?video_url\s*:\s*\'([^\']+)\''
        matches = scrapertools.find_multiple_matches(data, patron)
    for url, quality in matches:
        if "http" in quality:
            calidad = url
            url = quality
            quality = calidad + "p"

        itemlist.append(['.mp4 %s [directo]' % quality, url])

    if item.extra == "play_menu":
        return itemlist, data

    return itemlist


def menu_info(item):
    logger.info()
    itemlist = []

    video_urls, data = play(item.clone(extra="play_menu"))
    itemlist.append(item.clone(action="play", title="Ver -- %s" % item.title, video_urls=video_urls))

    bloque = scrapertools.find_single_match(data, '<div class="block-screenshots">(.*?)</div>')
    matches = scrapertools.find_multiple_matches(bloque, '<img class="thumb lazy-load".*?data-original="([^"]+)"')
    for i, img in enumerate(matches):
        if i == 0:
            continue
        img = urlparse.urljoin(host, img)
        title = "Imagen %s" % (str(i))
        itemlist.append(item.clone(action="", title=title, thumbnail=img, fanart=img))

    return itemlist


def tags(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    if item.title == "Tags":
        letras = []
        matches = scrapertools.find_multiple_matches(data, '<strong class="title".*?>\s*(.*?)</strong>')
        for title in matches:
            title = title.strip()
            if title not in letras:
                letras.append(title)
                itemlist.append(Item(channel=item.channel, action="tags", url=item.url, title=title, extra=title))
    else:
        if not item.length:
            item.length = 0

        bloque = scrapertools.find_single_match(data,
                                                '>%s</strong>(.*?)(?:(?!%s)(?!#)[A-Z#]{1}</strong>|<div class="footer-margin">)' % (
                                                    item.extra, item.extra))
        matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">\s*(.*?)</a>')
        for url, title in matches[item.length:item.length + 100]:
            itemlist.append(Item(channel=item.channel, action="lista", url=url, title=title))

        if len(itemlist) >= 100:
            itemlist.append(Item(channel=item.channel, action="tags", url=item.url, title=">> Página siguiente",
                                 length=item.length + 100, extra=item.extra))

    return itemlist
