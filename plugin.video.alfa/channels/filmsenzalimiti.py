# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmsenzalimiti
# ------------------------------------------------------------
import base64
import re
import urlparse

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import scrapertools, servertools, httptools
from platformcode import logger, config
from core.item import Item
from platformcode import config
from core import tmdb

__channel__ = 'filmsenzalimiti'

host = 'https://filmsenzalimiti.app'

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'vidoza', 'okru']
list_quality = ['1080p', '720p', '480p', '360']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'filmsenzalimiti')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'filmsenzalimiti')

headers = [['Referer', host]]


def mainlist(item):
    logger.info('[filmsenzalimiti.py] mainlist')

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = [Item(channel=item.channel,
                     action='video',
                     title='Film',
                     contentType='movie',
                     url=host,
                     thumbnail= ''),
                Item(channel=item.channel,
                     action='video',
                     title='Novità',
                     contentType='movie',
                     url=host + '/category/nuove-uscite',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='In Sala',
                     contentType='movie',
                     url=host + '/category/in-sala',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='video',
                     title='Sottotitolati',
                     contentType='movie',
                     url=host + '/category/sub-ita',
                     thumbnail=''),
                Item(channel=item.channel,
                     action='sottomenu',
                     title='[B]Categoria[/B]',
                     contentType='movie',
                     url=host,
                     thumbnail=''),
                Item(channel=item.channel,
                     action='search',
                     extra='tvshow',
                     title='[B]Cerca...[/B]',
                     contentType='movie',
                     thumbnail='')]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info('[filmsenzalimiti.py] search')

    item.url = host + '/?s=' + texto

    try:
        return cerca(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error('%s' % line)
        return []


def sottomenu(item):
    logger.info('[filmsenzalimiti.py] sottomenu')
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<li class="cat-item.*?<a href="([^"]+)">(.*?)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title=scrapedtitle,
                 url=scrapedurl))

    # Elimina Film dal Sottomenù
    itemlist.pop(0)

    return itemlist


def video(item):
    logger.info('[filmsenzalimiti.py] video')
    itemlist = []

    data = httptools.downloadpage(item.url).data.replace('\t','').replace('\n','')
    logger.info('[filmsenzalimiti.py] video' +data)

    patron = '<div class="col-mt-5 postsh">.*?<a href="([^"]+)" title="([^"]+)">.*?<span class="rating-number">(.*?)<.*?<img src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedrating, scrapedthumbnail in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        scrapedrating = scrapertools.decodeHtmlentities(scrapedrating)

        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title=scrapedtitle + ' (' + scrapedrating + ')',
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 contentType=item.contentType,
                 thumbnail=scrapedthumbnail), tipo='movie')

    patron = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title='[COLOR lightgreen]' + config.get_localized_string(30992) + '[/COLOR]',
                 contentType=item.contentType,
                 url=next_page))

    return itemlist

def cerca(item):
    logger.info('[filmsenzalimiti.py] cerca')
    itemlist = []

    data = httptools.downloadpage(item.url).data.replace('\t','').replace('\n','')
    logger.info('[filmsenzalimiti.py] video' +data)

    patron = '<div class="list-score">(.*?)<.*?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedrating, scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedthumbnail = httptools.get_url_headers(scrapedthumbnail)
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        scrapedrating = scrapertools.decodeHtmlentities(scrapedrating)

        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title=scrapedtitle + ' (' + scrapedrating + ')',
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 show=scrapedtitle,
                 contentType=item.contentType,
                 thumbnail=scrapedthumbnail), tipo='movie')

    patron = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"'
    next_page = scrapertools.find_single_match(data, patron)
    if next_page != '':
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 title='[COLOR lightgreen]' + config.get_localized_string(30992) + '[/COLOR]',
                 contentType=item.contentType,
                 url=next_page))

    return itemlist


def findvideos(item):
    logger.info('[filmsenzalimiti.py] findvideos')

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data.replace('\t', '').replace('\n', '')
    logger.info('[filmsenzalimiti.py] findvideos page download= '+data)

    patron = r'Streaming in HD<\/a><\/li><\/ul><br><p><iframe width="100%" height="430px" src="([^"]+)"'
    url = scrapertools.find_single_match(data, patron)

    if 'hdpass' in url:
        data = httptools.downloadpage('http:%s' % url if 'http' not in url else url).data

        start = data.find('<div class="row mobileRes">')
        end = data.find('<div id="playerFront">', start)
        data = data[start:end]

        patron_res = '<div class="row mobileRes">(.*?)</div>'
        patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
        patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="[^"]+" id="urlEmbed" value="([^"]+)"[^>]+>'

        res = scrapertools.find_single_match(data, patron_res)

        for res_url, resolution in scrapertools.find_multiple_matches(res, '<option[^v]+value="([^"]*)">([^<]*)</option>'):
            res_url = urlparse.urljoin(url, res_url)
            data = httptools.downloadpage('http:%s' % res_url if 'http' not in res_url else res_url).data.replace('\n', '')

            mir = scrapertools.find_single_match(data, patron_mir)

            for mir_url, server in scrapertools.find_multiple_matches(mir, '<option[^v]+value="([^"]*)">([^<]*)</value>'):
                mir_url = urlparse.urljoin(url, mir_url)
                data = httptools.downloadpage('http:%s' % mir_url if 'http' not in mir_url else mir_url).data.replace('\n', '')

                for media_url in re.compile(patron_media).findall(data):
                    scrapedurl = url_decode(media_url)
                    logger.info(scrapedurl)
                    itemlist.append(
                        Item(channel=item.channel,
                             action="play",
                             title='[[COLOR green]%s[/COLOR]][[COLOR orange]%s[/COLOR]] %s' % (resolution, server, item.title),
                             url=scrapedurl,
                             server=server,
                             fulltitle=item.fulltitle,
                             thumbnail=item.thumbnail,
                             show=item.show,
                             plot=item.plot,
                             quality=resolution,
                             contentType=item.contentType,
                             folder=False))

   # Link Aggiungi alla Libreria
    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findservers':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR lightblue][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findservers", contentTitle=item.contentTitle))

    #Necessario per filtrare i Link
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Necessario per  FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Necessario per  AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    itemlist = servertools.find_video_items(data=item.url)

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
    logger.info('[filmsenzalimiti.py] newest' + categoria)
    itemlist = []
    item = Item()
    try:

        ## cambiare i valori 'peliculas, infantiles, series, anime, documentales por los que correspondan aqui en
        # nel py e nel json ###
        if categoria == 'peliculas':
            item.url = host
            itemlist = video(item)

            if 'Successivo>>' in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error('{0}'.format(line))
        return []

    return itemlist
