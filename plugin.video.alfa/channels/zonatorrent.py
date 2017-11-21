# -*- coding: utf-8 -*-
# -*- Channel TioTorrent -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger

__channel__ = "zonatorrent"

HOST = 'https://zonatorrent.org'

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=item.channel, title="Últimas Películas", action="listado", url=HOST, page=False))
    itemlist.append(Item(channel=item.channel, title="Alfabético", action="alfabetico"))
    itemlist.append(Item(channel=item.channel, title="Géneros", action="generos", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Más vistas", action="listado", url=HOST + "/peliculas-mas-vistas/"))
    itemlist.append(Item(channel=item.channel, title="Más votadas", action="listado", url=HOST + "/peliculas-mas-votadas/"))
    itemlist.append(Item(channel=item.channel, title="Castellano", action="listado", url=HOST + "/?s=spanish",
                         page=True))
    itemlist.append(Item(channel=item.channel, title="Latino", action="listado", url=HOST + "/?s=latino", page=True))
    itemlist.append(Item(channel=item.channel, title="Subtitulado", action="listado", url=HOST + "/?s=Subtitulado",
                         page=True))
    itemlist.append(Item(channel=item.channel, title="Con Torrent", action="listado", url=HOST + "/?s=torrent",
                         page=True))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=HOST + "/?s=",
                         page=False))

    return itemlist


def alfabetico(item):
    logger.info()

    itemlist = []

    for letra in "#ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        itemlist.append(Item(channel=item.channel, action="listado", title=letra, page=True,
                             url=HOST + "/letters/%s/" % letra.replace("#", "0-9")))

    return itemlist


def generos(item):
    logger.info()

    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = scrapertools.find_single_match(data, '<a href="#">Generos</a><ulclass="sub-menu">(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)">(.*?)</a>')

    for url, title in matches:
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url, page=True))

    return itemlist


def search(item, texto):
    logger.info()
    item.url = item.url + texto.replace(" ", "+")

    try:
        itemlist = listado(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist


def listado(item):
    logger.info()

    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)

    pattern = '<a href="(?P<url>[^"]+)"><div[^>]+><figure[^>]+><img[^>]+src="(?P<thumb>[^"]+)"[^>]+></figure></div>' \
              '<h2 class="Title">(?P<title>.*?)</h2>.*?<span class="Time[^>]+>(?P<duration>.*?)</span><span ' \
              'class="Date[^>]+>(?P<year>.*?)</span><span class="Qlty">(?P<quality>.*?)</span></p><div ' \
              'class="Description"><p>.*?\:\s*(?P<plot>.*?)</p>'
    matches = re.compile(pattern, re.DOTALL).findall(data)

    for url, thumb, title, duration, year, quality, plot in matches:
        #title = title.strip().replace("Spanish Online Torrent", "").replace("Latino Online Torrent", "").replace(r'\d{4}','')
        title = re.sub('Online|Spanish|Latino|Torrent|\d{4}','',title)
        infoLabels = {"year": year}

        aux = scrapertools.find_single_match(duration, "(\d+)h\s*(\d+)m")
        duration = "%s" % ((int(aux[0]) * 3600) + (int(aux[1]) * 60))
        infoLabels["duration"] = duration

        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                             contentTitle=title, plot=plot, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    if item.page:
        pattern = "<span class='page-numbers current'>[^<]+</span><a class='page-numbers' href='([^']+)'"
        url = scrapertools.find_single_match(data, pattern)

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente", url=url, page=True,
                             thumbnail=get_thumb("next.png")))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    language = ''
    quality = ''
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    data = re.sub(r"&quot;", '"', data)
    data = re.sub(r"&lt;", '<', data)

    titles = re.compile('data-TPlayerNv="Opt\d+">.*? <span>(.*?)</span></li>', re.DOTALL).findall(data)
    urls = re.compile('id="Opt\d+"><iframe[^>]+src="([^"]+)"', re.DOTALL).findall(data)

    if len(titles) == len(urls):
        for i in range(0, len(titles)):
            if i > 0:
                logger.debug('titles: %s' % titles[i].strip())
                language, quality = titles[i].split(' - ')
                title = "%s" % titles[i].strip()
            else:
                title = titles[0]

            if "goo.gl" in urls[i]:
                urls[i] = httptools.downloadpage(urls[i], follow_redirects=False, only_headers=True)\
                    .headers.get("location", "")
            videourl = servertools.findvideos(urls[i])
            if len(videourl) > 0:
                server = videourl[0][0].capitalize()
                title = '%s %s' % (server, title)
                itemlist.append(Item(channel=item.channel, action="play", title=title, url=videourl[0][1],
                                     server=server, thumbnail=videourl[0][3], fulltitle=item.title,
                                     language=language, quality=quality ))

    pattern = '<a[^>]+href="([^"]+)"[^<]+</a></td><td><span><img[^>]+>(.*?)</span></td><td><span><img[^>]+>(.*?)' \
              '</span></td><td><span>(.*?)</span>'
    torrents = re.compile(pattern, re.DOTALL).findall(data)

    if len(torrents) > 0:
        for url, text, lang, quality in torrents:
            title = "%s %s - %s" % (text, lang, quality)
            itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, server="torrent",
                                 fulltitle=item.title, thumbnail=get_thumb("channels_torrent.png")))

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = HOST
        elif categoria == 'infantiles':
            item.url = HOST + "/animacion"
        elif categoria == 'terror':
            item.url = HOST + "/terror/"
        elif categoria == 'torrent':
            item.url = HOST + "/?s=torrent"
        else:
            return []

        itemlist = listado(item)
        if itemlist[-1].title == ">> Página siguiente":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
