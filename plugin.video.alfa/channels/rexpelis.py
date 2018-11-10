# -*- coding: utf-8 -*-
# -*- Channel Rexpelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools


idio = {'es-mx': 'LAT','es-es': 'ESP','en': 'VO'}
cali = {'poor': 'SD','low': 'SD','medium': 'HD','high': 'HD'}

list_language = idio.values()
list_quality = ["SD","HD"]
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'openload', 'netu', 'vidoza', 'uptobox']


__channel__='rexpelis'

host = "https://www.rexpelis.com"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    data = httptools.downloadpage(host).data
    matches = scrapertools.find_multiple_matches(data, 'cant-genre">([^<]+)')
    cantidad = 0
    for cantidad1 in matches:
        cantidad += int(cantidad1)
    itemlist.append(Item(channel = item.channel, title = "Actualizadas", action = "peliculas", url = host, page=1, type ="movie", thumbnail = get_thumb("updated", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Estrenos", action = "estrenos", url = host + "/estrenos", page=1, thumbnail = get_thumb("premieres", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género (Total películas: %s)" %cantidad, action = "generos", url = host, extra = "Genero", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "annos", url = host, extra = "Genero", thumbnail = get_thumb("year", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "/search?term=", thumbnail = get_thumb("search", auto = True)))
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = host + "/suggest?que=" + texto
    item.extra = "busca"
    item.page = 1
    item.texto = texto
    if texto != '':
        return sub_search(item)
    else:
        return []

    
def sub_search(item):
    logger.info()
    itemlist = []
    url = item.url
    headers = [
    ['X-Requested-With', 'XMLHttpRequest']
    ]
    data = httptools.downloadpage(item.url).data
    token = scrapertools.find_single_match(data, 'csrf-token" content="([^"]+)')
    data = httptools.downloadpage(item.url + "&_token=" + token, headers=headers).data
    data_js = jsontools.load(data)["data"]["m"]
    for js in data_js:
        js["title"] = quitano(js["title"])
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = js["title"],
                             infoLabels = {'year': js["release_year"]},
                             thumbnail = js["cover"],
                             title = js["title"] + " (%s)" %js["release_year"],
                             url = js["slug"]
                             ))
    tmdb.set_infoLabels(itemlist)
    #pagination
    if len(itemlist)>0:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = item.page + 1,
                             title = "Página siguiente >>",
                             url = item.url
                             ))
    return itemlist
    
    
def peliculas_gen(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'item-pelicula.*?href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'text-center">([^<]+).*?'
    patron += '<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        scrapedtitle = quitano(scrapedtitle)
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def estrenos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'item-pelicula.*?href="([^"]+).*?'
    patron += 'src="([^"]+).*?'
    patron += 'text-center">([^<]+).*?'
    patron += '<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("Película ","")
        scrapedtitle = quitano(scrapedtitle)
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    headers = [
    ['X-Requested-With', 'XMLHttpRequest']
    ]
    data = httptools.downloadpage(item.url).data
    token = scrapertools.find_single_match(data, 'csrf-token" content="([^"]+)')
    post = "page=%s&type=%s&_token=%s" %(item.page, item.type, token)
    if item.slug:
        post += "&slug=%s" %item.slug
    data = httptools.downloadpage(host + "/pagination", post=post, headers=headers).data
    patron  = '(?s)href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'text-center">([^<]+).*?'
    patron += '<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        scrapedtitle = quitano(scrapedtitle)
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    #pagination
    if len(itemlist)>0:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = item.page + 1,
                             title = "Página siguiente >>",
                             url = item.url
                             ))
    return itemlist
    
    
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
            item.page=1
        elif categoria == 'infantiles':
            item.url = host + '/genero/animacion'
            item.page = 1
        elif categoria == 'terror':
            item.url = host + '/genero/terror'
            item.page = 1
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, "genressomb.*?</ul>")
    patron  = 'href="([^"]+)".*?'
    patron += '</i>([^<]+).*?'
    patron += 'cant-genre">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo, cantidad in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas_gen",
                             page = 1,
                             slug = titulo,
                             title = titulo + "(%s)" %cantidad,
                             type = "genres",
                             url = url
                             ))
    return itemlist


def annos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'div class="years.*?</ul>')
    patron  = 'href="([^"]+)"'
    patron += '>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = 1,
                             slug = titulo,
                             title = titulo,
                             type = "year",
                             url = url
                             ))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = "video\[(\d)+\] = '([^']+)"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedoption, scrapedurl in matches:
        tit = scrapertools.find_single_match(data, 'option%s">([^<]+)' %scrapedoption)
        if "VIP" in tit: tit = "fembed"
        titulo = "Ver en %s" %tit.capitalize()
        itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 title = titulo,
                 url = host + "/embed/%s/" %scrapedurl
                 ))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe src="([^"]+)')
    headers = {"Referer":item.url}
    item.url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, headers=headers).headers.get("location", "")
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    item.thumbnail = item.contentThumbnail
    return itemlist


def quitano(title):
    # Quita el año que muestran en el título en la página, para que funcione bien tmdb
    t = title.replace(scrapertools.find_single_match(title, '\(\s*\d{4}\)'),"")
    return t.strip()
