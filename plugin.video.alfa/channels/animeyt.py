# -*- coding: utf-8 -*-

import re
import urlparse

from channels import renumbertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from platformcode import config,logger

__modo_grafico__ = config.get_setting('modo_grafico', 'animeyt')

HOST = "http://animeyt.tv/"

def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades", url=HOST))

    itemlist.append(Item(channel=item.channel, title="Recientes", action="recientes", url=HOST))
    
    itemlist.append(Item(channel=item.channel, title="Alfabético", action="alfabetico", url=HOST))

    itemlist.append(Item(channel=item.channel, title="Búsqueda", action="search", url=urlparse.urljoin(HOST, "busqueda?terminos=")))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def novedades(item):
    logger.info()
    itemlist = list()
    if not item.pagina:
        item.pagina = 0

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron_novedades = '<div class="capitulos-portada">[\s\S]+?<h2>Comentarios</h2>'

    data_novedades = scrapertools.find_single_match(data, patron_novedades)

    patron = 'href="([^"]+)"[\s\S]+?src="([^"]+)"[^<]+alt="([^"]+) (\d+)([^"]+)'

    matches = scrapertools.find_multiple_matches(data_novedades, patron)
    
    for url, img, scrapedtitle, eps, info in matches[item.pagina:item.pagina + 20]:
        title = scrapedtitle + " " + "1x" + eps + info
        title = title.replace("Sub Español", "").replace("sub español", "")
        infoLabels = {'filtro': {"original_language": "ja"}.items()}
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumb=img, action="findvideos", contentTitle=scrapedtitle, contentSerieName=scrapedtitle, infoLabels=infoLabels, contentType="tvshow"))
    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        for it in itemlist:
                it.thumbnail = it.thumb
    except:
        pass
    
    if len(matches) > item.pagina + 20:
        pagina = item.pagina + 20
        itemlist.append(item.clone(channel=item.channel, action="novedades", url=item.url, title=">> Página Siguiente", pagina=pagina))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    
    for letra in '0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        titulo = letra
        if letra == "0":
            letra = "num"
        itemlist.append(Item(channel=item.channel, action="recientes", title=titulo,
                             url=urlparse.urljoin(HOST, "animes?tipo=0&genero=0&anio=0&letra={letra}".format(letra=letra))))


    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ","+")
    item.url = item.url+texto
    if texto!='':
       return recientes(item)


def recientes(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron_recientes = '<article class="anime">[\s\S]+?</main>'

    data_recientes = scrapertools.find_single_match(data, patron_recientes)

    patron = '<a href="([^"]+)"[^<]+<img src="([^"]+)".+?js-synopsis-reduce">(.*?)<.*?<h3 class="anime__title">(.*?)<small>(.*?)</small>'

    matches = scrapertools.find_multiple_matches(data_recientes, patron)

    for url, thumbnail, plot, title, cat in matches:
        itemlist.append(item.clone(title=title, url=url, action="episodios", show=title, thumbnail=thumbnail, plot=plot, cat=cat, context=renumbertools.context(item)))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    paginacion = scrapertools.find_single_match(data, '<a class="pager__link icon-derecha last" href="([^"]+)"')
    paginacion = scrapertools.decodeHtmlentities(paginacion)

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="recientes", title=">> Página Siguiente", url=paginacion))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
  
    patron = '<span class="icon-triangulo-derecha"></span>.*?<a href="([^"]+)">([^"]+) (\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, scrapedtitle, episode in matches:
		
        season = 1
        episode = int(episode)
        season, episode = renumbertools.numbered_for_tratk(item.channel, scrapedtitle, season, episode)
        title = "%sx%s %s" % (season, str(episode).zfill(2), scrapedtitle)
        itemlist.append(item.clone(title=title, url=url, action='findvideos'))
        
    if config.get_videolibrary_support:
        itemlist.append(Item(channel=item.channel, title="Añadir serie a la biblioteca", url=item.url, action="add_serie_to_library", extra="episodios", show=item.show))
        
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    duplicados = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron = 'Player\("(.*?)"'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url in matches:
        if "cldup" in url:
            title = "Opcion Cldup"
        if "chumi" in url:
            title = "Opcion Chumi"
        itemlist.append(item.clone(channel=item.channel, folder=False, title=title, action="play", url=url))

    if item.extra != "library":
        if config.get_videolibrary_support() and item.extra:
            itemlist.append(item.clone(channel=item.channel, title="[COLOR yellow]Añadir pelicula a la videoteca[/COLOR]", url=item.url, action="add_pelicula_to_library", extra="library", contentTitle=item.show, contentType="movie"))

    return itemlist


def player(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url, add_referer=True).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
	
    url = scrapertools.find_single_match(data, 'sources: \[{file:\'(.*?)\'')

    itemlist = servertools.find_video_items(data=data)

    return itemlist

