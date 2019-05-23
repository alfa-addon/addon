# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa 
# ------------------------------------------------------------

import re, urllib, urlparse
import base64

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools
from channels import filtertools

host = 'http://www.gnula.mobi'

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'ESP', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['rapidvideo', 'streamgo', 'openload']

list_quality = ['HD',  'BR-S', 'TS']

__channel__='gmobi'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)


try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = list()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(item.clone(title="Novedades", action="lista", url=host + "/categorias/estrenos"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url= host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<a>CATEGORÍAS</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(channel=item.channel, action="lista", title=scrapedtitle , url=scrapedurl ,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<div class="Image">(.*?)</div>.*?'
    patron += '"Title">([^"]+)</h2>.*?'
    patron += '"Year">(\d+)</span>.*?'
    patron += '<span class="Qlty">\w+ \(([^"]+)\)</span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, calidad in matches:
        thumbnail = scrapertools.find_single_match(scrapedthumbnail, 'src="([^"]+)"')
        scrapedtitle = scrapedtitle.replace("(%s)"  % scrapedyear, "")
        if not config.get_setting('unify'):
            title =  title = '%s [COLOR red] %s [/COLOR] (%s)' % (scrapedtitle, calidad , scrapedyear)
        else:
            title = ''
        if not '>TV<' in scrapedthumbnail:
            itemlist.append(item.clone(action="findvideos", title=title, url=scrapedurl, thumbnail=thumbnail,
                                   contentTitle = scrapedtitle, quality=calidad, infoLabels={'year':scrapedyear}) )
    tmdb.set_infoLabels(itemlist, True)
    next_page_url = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
    if next_page_url != "":
        next_page_url = next_page_url
        itemlist.append(item.clone(action="lista", title="Siguiente >>", text_color="yellow",
                                   url=next_page_url))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '"server":"[^"]+",'
    patron += '"lang":"([^"]+)",'
    patron += '"quality":"\w+ \(([^"]+)\)",'
    patron += '"link":"https:.*?=([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for lang, quality, url in matches:
        if lang in IDIOMAS:
            lang = IDIOMAS[lang]
        url = base64.b64decode(url + "==")
        if not config.get_setting('unify'):
            title =  '[COLOR red] %s [/COLOR] (%s)' % (quality , lang)
        else:
            title = ''
        itemlist.append(item.clone(action = "play", title = '%s'+ title, url = url, language=lang, quality=quality,
                                   fulltitle = item.title))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' :
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle))
    return itemlist


