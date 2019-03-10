# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per seriehd
# Alhaziel
# ------------------------------------------------------------
import base64
import re
import urlparse

from channels import autoplay
from channels import filtertools
from core import scrapertools, servertools, httptools
from platformcode import logger, config
from core.item import Item
from platformcode import config
from core.tmdb import infoIca

__channel__ = "seriehd"

host = "https://www.seriehd.video"

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'thevideome']
list_quality = ['1080p', '720p', '480p', '360']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'seriehd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'seriehd')

headers = [['Referer', host]]


def mainlist(item):
    logger.info("seriehd.py mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     action="fichas",
                     title="[COLOR azure]Serie TV[/COLOR]",
                     url=host + "/serie-tv-streaming/",
                     thumbnail="http://i.imgur.com/rO0ggX2.png"),
                Item(channel=__channel__,
                     action="sottomenu",
                     title="[COLOR orange]Categoria[/COLOR]",
                     url=host,
                     thumbnail="http://i.imgur.com/rO0ggX2.png"),
                Item(channel=__channel__,
                     action="search",
                     extra="tvshow",
                     title="[COLOR limegreen]Cerca...[/COLOR]",
                     thumbnail="")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info("[seriehd.py] search")

    item.url = host + "/?s=" + texto

    try:
        return fichas(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sottomenu(item):
    logger.info("[seriehd.py] sottomenu")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title=scrapedtitle,
                 url=scrapedurl))

    # Elimina 'Serie TV' de la lista de 'sottomenu'
    itemlist.pop(0)

    return itemlist


def fichas(item):
    logger.info("[seriehd.py] fichas")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<h2>(.*?)</h2>\s*'
    patron += '<img src="([^"]+)" alt="[^"]*" />\s*'
    patron += '<A HREF="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedthumbnail, scrapedurl in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        itemlist.append(infoIca(
            Item(channel=__channel__,
                 action="episodios",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 thumbnail=scrapedthumbnail), tipo='tv'))

    patron = "<span class='current'>\d+</span><a rel='nofollow' class='page larger' href='([^']+)'>\d+</a>"
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != "":
        itemlist.append(
            Item(channel=__channel__,
                 action="fichas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page))

    return itemlist


def episodios(item):
    logger.info("[seriehd.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<iframe width=".+?" height=".+?" src="([^"]+)" allowfullscreen frameborder="0">'
    url = scrapertools.find_single_match(data, patron).replace("?seriehd", "")

    data = httptools.downloadpage(url).data.replace('\t', '').replace('\n', '').replace(' class="active"', '')


    section_stagione = scrapertools.find_single_match(data, '<h3>STAGIONE</h3><ul>(.*?)</ul>')
    patron = '<li[^>]+><a href="([^"]+)">(\d+)<'
    seasons = re.compile(patron, re.DOTALL).findall(section_stagione)

    for scrapedseason_url, scrapedseason in seasons:

        season_url = urlparse.urljoin(url, scrapedseason_url)
        data = httptools.downloadpage(season_url).data.replace('\t', '').replace('\n', '').replace(' class="active"', '')

        section_episodio = scrapertools.find_single_match(data, '<h3>EPISODIO</h3><ul>(.*?)</ul>')
        patron = '<a href="([^"]+)">(\d+)<'
        episodes = re.compile(patron, re.DOTALL).findall(section_episodio)

        for scrapedepisode_url, scrapedepisode in episodes:
            episode_url = urlparse.urljoin(url, scrapedepisode_url)

            title = scrapedseason + "x" + scrapedepisode.zfill(2)

            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     contentType="episode",
                     title=title,
                     url=episode_url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=__channel__,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("[seriehd.py] findvideos")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data.replace('\n', '')

    patron = r'<iframe[^s]+src="([^"]+)" allowfullscreen[^>]+>'
    url = scrapertools.find_single_match(data, patron)

    if 'hdpass' in url:
        data = httptools.downloadpage("http:%s" % url if 'http' not in url else url).data

        start = data.find('<div class="row mobileRes">')
        end = data.find('<div id="playerFront">', start)
        data = data[start:end]

        patron_res = '<div class="row mobileRes">(.*?)</div>'
        patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
        patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="[^"]+" id="urlEmbed" value="([^"]+)"[^>]+>'

        res = scrapertools.find_single_match(data, patron_res)

        urls = []
        for res_url in scrapertools.find_multiple_matches(res, '<option[^v]+value="([^"]*)">[^<]*</option>'):
            res_url = urlparse.urljoin(url, res_url)
            data = httptools.downloadpage("http:%s" % res_url if 'http' not in res_url else res_url).data.replace('\n', '')

            mir = scrapertools.find_single_match(data, patron_mir)

            for mir_url in scrapertools.find_multiple_matches(mir, '<option[^v]+value="([^"]*)">[^<]*</value>'):
                mir_url = urlparse.urljoin(url, mir_url)
                data = httptools.downloadpage("http:%s" % mir_url if 'http' not in mir_url else mir_url).data.replace('\n', '')

                for media_url in re.compile(patron_media).findall(data):
                    urls.append(url_decode(media_url))

        itemlist = servertools.find_video_items(data='\n'.join(urls))
        for videoitem in itemlist:
            server = re.sub(r'[-\[\]\s]+', '', videoitem.title).capitalize()
            videoitem.title = "[[COLOR orange]%s[/COLOR]] %s" % (server, item.title)
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.show = item.show
            videoitem.plot = item.plot
            videoitem.channel = __channel__
            videoitem.contentType = item.contentType
            videoitem.language = IDIOMAS['Italiano']

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    #if item.contentType != 'episode':
        #if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            #itemlist.append(
                #Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     #action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def url_decode(url_enc):
    lenght = len(url_enc)
    if lenght % 2 == 0:
        len2 = lenght / 2
        first = url_enc[0:len2]
        last = url_enc[len2:lenght]
        url_enc = last + first
        reverse = url_enc[::-1]
        return base64.b64decode(reverse)

    last_car = url_enc[lenght - 1]
    url_enc[lenght - 1] = ' '
    url_enc = url_enc.strip()
    len1 = len(url_enc)
    len2 = len1 / 2
    first = url_enc[0:len2]
    last = url_enc[len2:len1]
    url_enc = last + first
    reverse = url_enc[::-1]
    reverse = reverse + last_car
    return base64.b64decode(reverse)


def newest(categoria):
    logger.info("[seriehd] newest" + categoria)
    itemlist = []
    item = Item()
    try:

        ## cambiar los valores "peliculas, infantiles, series, anime, documentales por los que correspondan aqui en
        # el py y en l json ###
        if categoria == "series":
            item.url = host
            itemlist = fichas(item)

            if 'Successivo>>' in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
