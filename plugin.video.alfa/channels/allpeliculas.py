# -*- coding: utf-8 -*-

import urlparse
import string
import urllib
import urllib2

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger, platformtools

__modo_grafico__ = config.get_setting('modo_grafico', "allpeliculas")
__perfil__ = int(config.get_setting('perfil', "allpeliculas"))

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

IDIOMAS = {"Castellano": "CAST", "Latino": "LAT", "Subtitulado": "VOSE", "Ingles": "VO"}
SERVERS = {"26": "powvideo", "45": "okru", "75": "openload", "12": "netutv", "65": "thevideos",
           "67": "spruto", "71": "stormo", "73": "idowatch", "48": "okru", "55": "openload",
           "20": "nowvideo", "84": "fastplay", "96": "raptu", "94": "tusfiles"}

# headers = {'Content-Type':'application/json'}

host = "http://allpeliculas.com/"

def mainlist(item):
    logger.info()
    itemlist = []
    item.text_color = color1

    itemlist.append(item.clone(title="Películas", action="lista", fanart="http://i.imgur.com/c3HS8kj.png",
                               url= host + "movies/newmovies?page=1"))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(title="Buscar...", action="search"))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    # Rellena diccionarios idioma y calidad
    idiomas_videos, calidad_videos = dict_videos()

    data = httptools.downloadpage(item.url).data

    patron  = 'data-link="([^"]+).*?'
    patron += '>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, cal in matches:
        titulo = cal

        itemlist.append(Item(
                             channel = item.channel,
                             action = "play",
                             title = titulo,
                             url = url,
                             ))
    itemlist = servertools.get_servers_itemlist(itemlist)
    try:
        from core import tmdb
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
    except:
        pass

    return itemlist


def dict_videos():
    idiomas_videos = {}
    calidad_videos = {}
    data = httptools.downloadpage("http://allpeliculas.co/Search/advancedSearch&ajax=1").data
    data = data.replace("\n", "").replace("\t", "")
    bloque_idioma = scrapertools.find_single_match(data,
                                                   '<select name="language".*?<option value="" selected(.*?)</select>')
    matches = scrapertools.find_multiple_matches(bloque_idioma, '<option value="([^"]+)" >(.*?)</option>')
    for key1, key2 in matches:
        idiomas_videos[key1] = unicode(key2, "utf8").capitalize().encode("utf8")
    bloque_calidad = scrapertools.find_single_match(data, '<select name="movieTypeId".*?<option value="" selected(.*?)'
                                                          '</select>')
    matches = scrapertools.find_multiple_matches(bloque_calidad, '<option value="([^"]+)" >(.*?)</option>')
    for key1, key2 in matches:
        calidad_videos[key1] = key2

    return idiomas_videos, calidad_videos



def lista(item):
    logger.info()
    itemlist = []
    item.infoLabels = {}
    item.text_color = color2
    genero = 64
    ano = 2017
    sort = ""
    countries = ""
    optiones = ""
    params = '{"genero":genero,"ano":ano,"countries":countries,"sort":sort,"optiones":optiones}'
    params = '{"genereo":"64"}'
    #params = urllib.urlencode(params)
    #logger.info("Intel55 %s" %params)
    #req = urllib2.Request(item.url, data=params)
    #logger.info("Intel66 %s" %req)

    #logger.info("Intel22 %s" %data)

    data = httptools.downloadpage(item.url, post=params).data
    dict_data = jsontools.load(data)

    for it in dict_data["items"]:
        title = it["title"]
        plot = it["slogan"]
        rating = it["imdb"]
        year = it["year"]

        url = host + "pelicula/" + it["slug"]
        thumb = urlparse.urljoin(host, it["image"])

        item.infoLabels['year'] = year
        # item.infoLabels['rating'] = rating

        itemlist.append(item.clone(action="findvideos", title=title, fulltitle=title, url=url, thumbnail=thumb,
                                   plot=plot, context=["buscar_trailer"], contentTitle=title, contentType="movie"))

    pagina = scrapertools.find_single_match(item.url, 'page=([0-9]+)')
    item.url = item.url.replace(pagina, "")
    if pagina == "":
        pagina = "0"
    pagina = int(pagina) + 1
    item.url = item.url + "%s" %pagina
    if item.extra != "busqueda":
        itemlist.append(Item(channel = item.channel, action="lista", title="Pagina %s" %pagina, url=item.url,
                             ))
    try:
        from core import tmdb
        # Obtenemos los datos basicos de todas las peliculas mediante multihilos
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    except:
        pass

    return itemlist

def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = host + "/movies/search/" + texto
    item.extra = "busqueda"
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = "http://allpeliculas.co/Movies/fullView/1/0/&ajax=1"
            item.action = "lista"
            itemlist = lista(item)

            if itemlist[-1].action == "lista":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
