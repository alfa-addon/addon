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

IDIOMAS = {'latino': 'LAT','Latino': 'LAT', 'Español': 'ESP', 'Subtitulado': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['Rapidvideo', 'Streamgo', 'Gvideo', 'Okru', 'Openload', 'Fembed']

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
    itemlist.append(item.clone(title="Novedades", action="lista", url=host + "/pelicula/category/estreno/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url= host))
    itemlist.append(item.clone(title="Año" , action="categorias", url= host))
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
        return lista2(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista2(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="list-score">([^<]+)</div>.*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += '<img src="([^"]+)".*?'
    patron += '>Película de (\d+)</p>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for calidad, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear in matches:
        scrapedtitle = scrapedtitle.replace("Ver", "").replace("Online", "")
        scrapedtitle = scrapedtitle.replace("(%s)"  % scrapedyear, "").replace("%s"  % scrapedyear, "")
        if not config.get_setting('unify'):
            title =  '%s [COLOR red] %s [/COLOR] (%s)' % (scrapedtitle, calidad , scrapedyear)
        else:
            title = ''
        if not 'temporada' in scrapedtitle:
            itemlist.append(item.clone(action="findvideos", title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   contentTitle = scrapedtitle, quality=calidad, infoLabels={'year':scrapedyear}) )
    tmdb.set_infoLabels(itemlist, True)
    next_page_url = scrapertools.find_single_match(data, '<a href="([^"]+)" class="next-posts-link">')
    if next_page_url != "":
        next_page_url = next_page_url
        itemlist.append(item.clone(action="lista", title="Siguiente >>", text_color="yellow",
                                   url=next_page_url))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "Categorias" in item.title: 
        data = scrapertools.find_single_match(data,'>Generos</h3>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data,'Años</h3>(.*?)</ul>')
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
    patron = '<div class="col-mt-5 postsh">.*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += 'year">(\d+)</span>.*?'
    patron += '<span class="calidad".*?>([^<]+)</span>.*?'
    patron += 'src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedyear, calidad, scrapedthumbnail in matches:
        scrapedtitle = scrapedtitle.replace("Ver", "").replace("Online", "")
        scrapedtitle = scrapedtitle.replace("(%s)"  % scrapedyear, "").replace("%s"  % scrapedyear, "")
        if not config.get_setting('unify'):
            title =  '%s [COLOR red] %s [/COLOR] (%s)' % (scrapedtitle, calidad , scrapedyear)
        else:
            title = ''
        if not 'temporada' in scrapedtitle:
            itemlist.append(item.clone(action="findvideos", title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   contentTitle = scrapedtitle, quality=calidad, infoLabels={'year':scrapedyear}) )
    tmdb.set_infoLabels(itemlist, True)
    next_page_url = scrapertools.find_single_match(data, '<a href="([^"]+)" class="next-posts-link">')
    if next_page_url != "":
        next_page_url = next_page_url
        itemlist.append(item.clone(action="lista", title="Siguiente >>", text_color="yellow",
                                   url=next_page_url))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-src="https://gnula.mobi/redirect\?id=([^"]+)".*?'
    patron += '>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, lang in matches:
        if "latino" in lang: lang = "Latino"
        if "subtitulado" in lang: lang = "Subtitulado"
        if "español" in lang: lang = "Español"
        if lang in IDIOMAS:
            lang = IDIOMAS[lang]
        url = base64.b64decode(url + "==")
        if "?id=" in url:
            url = url.replace("&value=b3U", "").replace("https://gnula.mobi/redirect/?id=", "")
            url = base64.b64decode(url + "==")
            
        if "seriesynovelas" in url:
            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
        if "cine24.online" in url:
            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
        if not config.get_setting('unify'):
            title =  ' (%s)' % lang
        else:
            title = ''   
        if not "xdrive" in url:
            itemlist.append(item.clone(action = "play", title ='%s'+ title, url = url, language=lang))
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


