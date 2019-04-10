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


host = "http://www.asialiveaction.com"

IDIOMAS = {'Japones': 'Japones'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['gvideo', 'openload','streamango']

def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="lista", title="Peliculas",
                             url=urlparse.urljoin(host, "/category/pelicula"), type='pl', pag=1))
    itemlist.append(Item(channel=item.channel, action="lista", title="Series",
                         url=urlparse.urljoin(host, "/category/serie"), type='sr', pag=1))
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
            itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, type='cat', pag=0))
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
    item.pag = 0
    if texto != '':
        return lista(item)


def episodios(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(item.url).data
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
    data = httptools.downloadpage(item.url).data
    patron  = '(?is)Num">.*?href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?>.*?'
    patron += '<strong>([^<]+)<.*?'
    patron += '<td>([^<]+)<.*?'
    patron += 'href.*?>([^"]+)<\/a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
        action = "findvideos"
        if "Serie" in scrapedtype: action = "episodios"
        itemlist.append(item.clone(action=action, title=scrapedtitle, contentTitle=scrapedtitle, contentSerieName=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                       infoLabels={'year':scrapedyear}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
        
    patron = '<article .*?">'
    patron += '<a href="([^"]+)"><.*?><figure.*?>' #scrapedurl
    patron += '<img.*?src="([^"]+)".*?>.*?' #scrapedthumbnail
    patron += '<h3 class=".*?">([^"]+)<\/h3>' #scrapedtitle
    patron += '<span.*?>([^"]+)<\/span>.+?' #scrapedyear
    patron += '<a.+?>([^"]+)<\/a>' #scrapedtype
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedtype in matches:
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
    pag = item.pag + 1
    url_next_page = item.url+"/page/"+str(pag)+"/"
    if len(itemlist)>19:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='lista', pag=pag))
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
            itemlist.append(item.clone(action = "play", title = "Ver en %s (" + language + ")", language = language, url = url))
            continue
        data1 = httptools.downloadpage(url).data
        packed = scrapertools.find_single_match(data1, "(?is)eval\(function\(p,a,c,k,e.*?</script>")
        unpack = jsunpack.unpack(packed)
        urls = scrapertools.find_multiple_matches(unpack, '"file":"([^"]+).*?label":"([^"]+)')
        for url2, quality in urls:
            itemlist.append(item.clone(action = "play", title = "Ver en %s (" + quality + ") (" + language + ")", language = language, url = url2))
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
                itemlist.append(item.clone(action = "play", title = "Ver en %s (" + quality + ") (" + language + ")", language = language, url = url2))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
     # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    return itemlist
