# -*- coding: UTF-8 -*-

import re
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from lib import jsunpack
from platformcode import config, logger


host = "https://elhogardelaprendiz.es/"

IDIOMAS = {}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gvideo', 'openload','streamango']

def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="lista", title="Ultimas Agregadas",
                             url=urlparse.urljoin(host, "/peliculas"), type='pl'))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series",
                         url=urlparse.urljoin(host, "/series"), type='sr'))
    itemlist.append(Item(channel=item.channel, action="category", title="Orden Alfabético", url=host, cat='abc'))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+"/?s="))
    itemlist.append(Item(channel=item.channel, action="lista", title="Visita [COLOR=orange]www.elhogardelaprendiz.es[/COLOR]",
                             ))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def category(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
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
    data = httptools.downloadpage(item.url).data
    patron = '<span class=.post-labels.>([^<]+)</span>.*?class="poster-bg" src="([^"]+)"/>.*?<h4>.*?'
    patron +=">(\d{4})</a>.*?<h6>([^<]+)<a href='([^']+)"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtype, scrapedthumbnail, scrapedyear, scrapedtitle ,scrapedurl in matches:
        title="%s [%s]" % (scrapedtitle, scrapedyear)
        new_item= Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail)
        if scrapedtype.strip() == 'Serie':
            new_item.contentSerieName = scrapedtitle
            new_item.action = 'episode'
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
    if texto != '':
        return lista(item)


def episodios(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
    data = data.replace('"ep0','"epp"')
    patron  = 'class="Num">(\d+)<.*?'
    patron += 'class="MvTbImg"><img src="([^"]+)".*?'
    patron += 'class="MvTbTtl"><a href="([^"]+)">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapednum_epi, scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        #title="1x%s - %s" % (episode, item.contentSerieName) # episode es scrapednum_epi
        title="1x%s - %s" % (scrapednum_epi, item.contentSerieName)
        #urls = scrapertools.find_multiple_matches(scrapedurls, 'href="([^"]+)')
        itemlist.append(item.clone(action='findvideos', episodios=scrapednum_epi, thumbnail=scrapedthumbnail, url=scrapedurl, title=title, type=item.type,
                                    infoLabels=item.infoLabels))
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                            url=item.url, action="add_serie_to_library", extra="episode",
                            contentSerieName=item.contentSerieName))
    return itemlist


def lista_a(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?is)Num">.*?href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?>.*?'
    patron += '<strong>([^<]+)<.*?'
    patron += '<td>([^<]+)<.*?'
    patron += 'href.*?>([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
        if not scrapedthumbnail.startswith("http"): scrapedthumbnail = "https:" + scrapedthumbnail
        action = "findvideos"
        if "Serie" in scrapedtype: action = "episode"
        itemlist.append(item.clone(action=action, title=scrapedtitle, contentTitle=scrapedtitle, contentSerieName=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                       infoLabels={'year':scrapedyear}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger.debug(data)
    patron  = '(?is)class="TPost C">.*?href="([^"]+)".*?' #scrapedurl
    patron += 'src="([^"]+)".*?>.*?' #scrapedthumbnail
    patron += 'Title">([^<]+)<.*?' #scrapedtitle
    patron += 'Year">([^<]+)<.*?' #scrapedyear
    #patron += 'href.*?>([^"]+)<\/a>' #scrapedtype
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        if not scrapedthumbnail.startswith("http"): scrapedthumbnail = "https:" + scrapedthumbnail
        title="%s - %s" % (scrapedtitle,scrapedyear)
        new_item = Item(channel=item.channel, title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                        infoLabels={'year':scrapedyear}) # no utilizas scrapedtype por lo que no es necesario
        #if scrapedtype == "Serie": # scrapedtype no toma nada en el regex si miras
        if '/serie' in scrapedurl: # sabes que es una serie porque la url lo dice
            new_item.contentSerieName = scrapedtitle
            #new_item.action = 'episode' # La funcion que lista los episodios se llama episodios
            new_item.action = 'episodios' # La funcion que lista los episodios se llama episodios
        else:
            new_item.contentTitle = scrapedtitle
            new_item.action = 'findvideos'
            
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    #pagination
    url_next_page = scrapertools.find_single_match(data, 'class="next page-numbers" href="([^"]+)"')
    if len(itemlist)>0 and url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista'))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data.replace("&quot;",'"').replace("amp;","").replace("#038;","")
    matches = scrapertools.find_multiple_matches(data, 'TPlayerTb.*?id="([^"]+)".*?src="([^"]+)"')
    matches_del = scrapertools.find_multiple_matches(data, '(?is)<!--<td>.*?-->')
    # Borra los comentarios - que contienen enlaces duplicados
    for del_m in matches_del:
        data = data.replace(del_m, "")
    # Primer grupo de enlaces
    for id, url1 in matches:
        language = scrapertools.find_single_match(data, '(?is)data-tplayernv="%s".*?span><span>([^<]+)' %id)
        data1 = httptools.downloadpage(url1).data
        url = scrapertools.find_single_match(data1, 'src="([^"]+)')
        if "a-x" in url:
            data1 = httptools.downloadpage(url, headers={"Referer":url1}).data
            url = scrapertools.find_single_match(data1, 'src: "([^"]+)"')
        if "embed.php" not in url:
            if url:
                itemlist.append(item.clone(action = "play", title = "Servidor: %s (" + language + ")", language = language, url = url))
            continue
        data1 = httptools.downloadpage(url).data
        packed = scrapertools.find_single_match(data1, "(?is)eval\(function\(p,a,c,k,e.*?</script>")
        unpack = jsunpack.unpack(packed)
        urls = scrapertools.find_multiple_matches(unpack, '"file":"([^"]+).*?label":"([^"]+)')
        for url2, quality in urls:
            if url2:
                itemlist.append(item.clone(action = "play", title = "Servidor: %s (" + quality + ") (" + language + ")", language = language, url = url2))
    # Segundo grupo de enlaces
    matches = scrapertools.find_multiple_matches(data, '<span><a rel="nofollow" target="_blank" href="([^"]+)"')
    for url in matches:
        data1 = httptools.downloadpage(url).data
        matches1 = scrapertools.find_multiple_matches(data1, '"ser".*?</tr>')
        for ser in matches1:
            ser = ser.replace("&#215;","x")
            aud = scrapertools.find_single_match(ser, 'aud"><i class="([^"]+)')
            sub = scrapertools.find_single_match(ser, 'sub"><i class="([^"]+)')
            quality = scrapertools.find_single_match(ser, 'res">.*?x([^<]+)')
            language = "Versión RAW"
            if aud == "jp" and sub == "si":
                language = "Sub. Español"
            matches2 = scrapertools.find_multiple_matches(ser, 'href="([^"]+)')
            for url2 in matches2:
                if url2:
                    itemlist.append(item.clone(action = "play", title = "Servidor: %s (" + quality + ") (" + language + ")", language = language, url = url2))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
