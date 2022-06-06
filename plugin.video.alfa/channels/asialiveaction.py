# -*- coding: UTF-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from lib import jsunpack
from platformcode import config, logger

canonical = {
             'channel': 'asialiveaction', 
             'host': config.get_setting("current_host", 'asialiveaction', default=''), 
             'host_alt': ["https://asialiveaction.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

IDIOMAS = {'Japones': 'Japones'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gvideo', 'openload','streamango']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="lista", title="Peliculas",
                             url=urlparse.urljoin(host, "/pelicula"), type='pl'))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series",
                         url=urlparse.urljoin(host, "/serie"), type='sr'))
    itemlist.append(Item(channel=item.channel, action="category", title="Géneros", url=host, cat='genre'))
    itemlist.append(Item(channel=item.channel, action="category", title="Calidad", url=host, cat='quality'))
    itemlist.append(Item(channel=item.channel, action="category", title="Orden Alfabético", url=host, cat='abc'))
    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno", url=host, cat='year'))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+"/?s="))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def category(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    action = "lista"
    if item.cat == 'abc':
        data = scrapertools.find_single_match(data, '<div class="Body Container">(.+?)<main>')
        action = "lista_a"
    elif item.cat == 'genre':
        data = scrapertools.find_single_match(data, '<a>Géneros<\/a><ul class="sub.menu">(.+?)<a>Año<\/a>')
    elif item.cat == 'year':
        data = scrapertools.find_single_match(data, '<a>Año<\/a><ul class="sub.menu">(.+?)<a>Idioma<\/a>')
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<a>Calidad<\/a><ul class="sub-menu">(.+?)<a>Géneros<\/a>')
    patron = '<li.*?><a href="(.*?)">(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        if scrapedtitle != 'Próximas Películas':
            if not scrapedurl.startswith("http"): scrapedurl = host + scrapedurl
            itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, type='cat'))
    return itemlist


def search_results(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron = '<span class=.post-labels.>([^<]+)</span>.*?class="poster-bg" src="([^"]+)"/>.*?<h4>.*?'
    patron +=">(\d{4})</a>.*?<h6>([^<]+)<a href='([^']+)"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtype, scrapedthumbnail, scrapedyear, scrapedtitle ,scrapedurl in matches:
        title="%s [%s]" % (scrapedtitle, scrapedyear)
        new_item= Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail)
        if scrapedtype.strip() == 'Serie':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episodios'
            new_item.type = 'sr'
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
            new_item.type = 'pl'
        itemlist.append(new_item)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def episodios(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = data.replace('"ep0','"epp"')
    patron  = '(?is)MvTbImg B.*?href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'span>Episodio ([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedepi in matches:
        title="1x%s - %s" % (scrapedepi, item.contentSerieName)
        #urls = scrapertools.find_multiple_matches(scrapedurls, 'href="([^"]+)')
        itemlist.append(item.clone(action='findvideos', title=title, url=scrapedurl, thumbnail=scrapedthumbnail, type=item.type,
                                   infoLabels=item.infoLabels))
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                             url=item.url, action="add_serie_to_library", extra="episodios",
                             contentSerieName=item.contentSerieName))
    return itemlist


def lista_a(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    patron  = '(?is)Num">.*?href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?>.*?'
    patron += '<strong>([^<]+)<.*?'
    patron += '<td>([^<]+)<.*?'
    patron += 'href.*?>([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
        if not scrapedthumbnail.startswith("http"): scrapedthumbnail = "https:" + scrapedthumbnail
        action = "findvideos"
        if "Serie" in scrapedtype: action = "episodios"
        itemlist.append(item.clone(action=action, title=scrapedtitle, contentTitle=scrapedtitle, contentSerieName=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                       infoLabels={'year':scrapedyear}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
        
    patron  = '(?is)class="TPost C">.*?href="([^"]+)".*?' #scrapedurl
    patron += 'src="([^"]+)".*?>.*?' #scrapedthumbnail
    patron += 'title">([^<]+)<.*?' #scrapedtitle
    patron += 'year">([^<]+)<.*?' #scrapedyear
    patron += 'href.*?>([^"]+)<\/a>' #scrapedtype
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
        if not scrapedthumbnail.startswith("http"): scrapedthumbnail = "https:" + scrapedthumbnail
        title="%s - %s" % (scrapedtitle,scrapedyear)

        new_item = Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                       type=scrapedtype, infoLabels={'year':scrapedyear})
        if scrapedtype == 'Serie':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episodios'
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
            
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    #pagination
    url_next_page = scrapertools.find_single_match(data, 'rel="next" href="([^"]+)"')
    if len(itemlist)>0 and url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista'))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data.replace("&quot;",'"').replace("amp;","").replace("#038;","")
    url = scrapertools.find_single_match(data, '<span><a rel="nofollow" target="_blank" href="([^"]+)"')
    data = httptools.downloadpage(url).data
    bloque = scrapertools.find_single_match(data, 'videosJap = \[(.*)\];')
    matches  = scrapertools.find_multiple_matches(bloque, "(http.*?)'")
    for url in matches:
        itemlist.append(item.clone(action = "play", title = "%s", url = url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
