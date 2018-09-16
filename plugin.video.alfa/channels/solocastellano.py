# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://solocastellano.com/'
headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

IDIOMAS = {'Castellano': 'Castellano'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['yourupload', 'openload', 'sendvid']

vars = {
    'ef5ca18f089cf01316bbc967fa10f72950790c39ef5ca18f089cf01316bbc967fa10f72950790c39': 'http://tawnestdplsnetps.pw/',
    'b48699bb49d4550f27879deeb948d4f7d9c5949a8': 'embed',
    'JzewJkLlrvcFnLelj2ikbA': 'php?url=',
    'p889c6853a117aca83ef9d6523335dc065213ae86': 'player',
    'e20fb341325556c0fc0145ce10d08a970538987': 'http://yourupload.com/embed/'
}

tgenero = {"acción": "https://s3.postimg.cc/y6o9puflv/accion.png",
           "animación": "https://s13.postimg.cc/5on877l87/animacion.png",
           "aventura": "https://s10.postimg.cc/6su40czih/aventura.png",
           "belico": "https://s23.postimg.cc/71itp9hcr/belica.png",
           "ciencia ficción": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
           "comedia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
           "comedia romántica": "https://s21.postimg.cc/xfsj7ua0n/romantica.png",
           "cortometrajes": "https://s15.postimg.cc/kluxxwg23/cortometraje.png",
           "crimen": "https://s4.postimg.cc/6z27zhirx/crimen.png",
           "cristianas": "https://s7.postimg.cc/llo852fwr/religiosa.png",
           "deportivas": "https://s13.postimg.cc/xuxf5h06v/deporte.png",
           "drama": "https://s16.postimg.cc/94sia332d/drama.png",
           "familiar": "https://s7.postimg.cc/6s7vdhqrf/familiar.png",
           "fantasía": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
           "guerra": "https://s4.postimg.cc/n1h2jp2jh/guerra.png",
           "historia": "https://s15.postimg.cc/fmc050h1n/historia.png",
           "intriga": "https://s27.postimg.cc/v9og43u2b/intriga.png",
           "misterios": "https://s1.postimg.cc/w7fdgf2vj/misterio.png",
           "musical": "https://s29.postimg.cc/bbxmdh9c7/musical.png",
           "romance": "https://s15.postimg.cc/fb5j8cl63/romance.png",
           "suspenso": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
           "terror": "https://s7.postimg.cc/yi0gij3gb/terror.png",
           "thriller": "https://s22.postimg.cc/5y9g0jsu9/thriller.png"}

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail=get_thumb('all', auto=True),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + 'lista-de-peliculas/',
                               extra='peliculas'
                               ))

    itemlist.append(item.clone(title="Ultimas",
                               action="lista",
                               thumbnail=get_thumb('last', auto=True),
                               fanart='https://s22.postimg.cc/cb7nmhwv5/ultimas.png',
                               url=host,
                               extra='peliculas'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="generos",
                               thumbnail=get_thumb('genres', auto=True),
                               fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                               url=host,
                               extra='peliculas'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + 'search?q=',
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    contentSerieName = ''

    patron = '<div class=movie><div class=imagen><img src=(.*?) alt=(.*?) width=.*? height=.*?\/><a href=(.*?)><span '
    patron += 'class=player>.*?class=year>(.*?)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if item.extra == 'peliculas':
        accion = 'findvideos'
    else:
        accion = 'temporadas'

    for scrapedthumbnail, scrapedtitle, scrapedurl, scrapedyear in matches:

        scrapedurl = scrapedurl.translate(None, '"')
        scrapedurl = scrapedurl.translate(None, "'")
        url = host + scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapedtitle
        year = scrapedyear
        if item.extra == 'series':
            contentSerieName = scrapedtitle

        itemlist.append(Item(channel=item.channel,
                             action=accion,
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentTitle=scrapedtitle,
                             extra=item.extra,
                             contentSerieName=contentSerieName,
                             infoLabels={'year': year}
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # #Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<div class=siguiente><a href=(.*?)>')
        url = host + next_page
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="lista",
                                 title='Siguiente >>>',
                                 url=url,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                                 extra=item.extra
                                 ))
    return itemlist


def generos(item):
    logger.info()

    itemlist = []
    norep = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="cat-item cat-item-.*?"><a href="([^"]+)".*?>([^<]+)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:

        url = host + scrapedurl
        title = scrapedtitle.lower()
        if title in tgenero:
            thumbnail = tgenero[title.lower()]
        else:
            thumbnail = ''

        itemactual = Item(channel=item.channel,
                          action='lista',
                          title=title, url=url,
                          thumbnail=thumbnail,
                          extra=item.extra
                          )

        if title not in norep:
            itemlist.append(itemactual)
            norep.append(itemactual.title)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="has-sub"><a href="([^"]+)"><span><b class="icon-bars"><\/b> ([^<]+)<\/span><\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    temp = 1
    infoLabels = item.infoLabels
    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapedtitle.strip('')
        contentSeasonNumber = temp
        infoLabels['season'] = contentSeasonNumber
        thumbnail = item.thumbnail
        plot = scrapertools.find_single_match(data, '<p>([^<]+)<\/p>')
        itemlist.append(Item(channel=item.channel,
                             action="episodiosxtemp",
                             title=title,
                             fulltitle=item.title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=item.contentSerieName,
                             contentSeasonNumber=contentSeasonNumber,
                             plot=plot,
                             infoLabels=infoLabels
                             ))
        temp = temp + 1
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             extra1=item.extra1,
                             temp=str(temp)
                             ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    temp = 'temporada-' + str(item.contentSeasonNumber)
    patron = '<li>.\s*<a href="(.*?)">.\s*<span.*?datex">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedepisode in matches:
        url = host + scrapedurl
        title = item.contentSerieName + ' ' + scrapedepisode
        thumbnail = item.thumbnail
        fanart = ''
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             fulltitle=item.fulltitle,
                             url=url,
                             thumbnail=item.thumbnail,
                             plot=item.plot,
                             extra=item.extra,
                             contentSerieName=item.contentSerieName
                             ))

    return itemlist


def episodiosxtemp(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    temp = 'temporada-' + str(item.contentSeasonNumber)
    patron = '<li>.\s*<a href="(.*?-' + temp + '.*?)">.\s*<span.*?datex">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedurl, scrapedepisode in matches:
        url = host + scrapedurl
        title = item.contentSerieName + ' ' + scrapedepisode
        scrapedepisode = re.sub(r'.*?x', '', scrapedepisode)
        infoLabels['episode'] = scrapedepisode
        thumbnail = item.thumbnail
        fanart = ''
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             fulltitle=item.fulltitle,
                             url=url,
                             thumbnail=item.thumbnail,
                             plot=item.plot,
                             extra=item.extra,
                             contentSerieName=item.contentSerieName,
                             infoLabels=infoLabels
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def dec(encurl):
    logger.info()
    url = ''
    encurl = encurl.translate(None, "',(,),;")
    encurl = encurl.split('+')

    for cod in encurl:
        if cod in vars:
            url = url + vars[cod]
        else:
            url = url + cod
    return url


def findvideos(item):
    logger.info()

    itemlist = []
    langs = dict()

    data = httptools.downloadpage(item.url).data
    patron = '<a onclick="return (play\d+).*?;"> (.*?) <\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for key, value in matches:
        langs[key] = value.strip()

    patron = 'function (play\d).*?servidores.*?attr.*?src.*?\+([^;]+);'
    matches = re.compile(patron, re.DOTALL).findall(data)
    title = item.title
    enlace = scrapertools.find_single_match(data,
                                            'var e20fb341325556c0fc0145ce10d08a970538987 =.*?"\/your\.".*?"([^"]+)"')

    for scrapedlang, encurl in matches:

        if 'e20fb34' in encurl:
            url = dec(encurl)
            url = url + enlace

        else:
            url = dec(encurl)
        title = ''
        server = ''
        servers = {'/opl': 'openload', '/your': 'yourupload', '/sen': 'senvid', '/face': 'netutv', '/vk': 'vk',
                   '/jk':'streamcherry'}
        server_id = re.sub(r'.*?embed|\.php.*', '', url)
        if server_id and server_id in servers:
            server = servers[server_id]


        if (scrapedlang in langs) and langs[scrapedlang] in list_language:
            language = IDIOMAS[langs[scrapedlang]]
        else:
            language = 'Latino'
        #
        # if langs[scrapedlang] == 'Latino':
        #     idioma = '[COLOR limegreen]LATINO[/COLOR]'
        # elif langs[scrapedlang] == 'Sub Español':
        #     idioma = '[COLOR red]SUB[/COLOR]'

        if item.extra == 'peliculas':
            title = item.contentTitle + ' (' + server + ') ' + language
            plot = scrapertools.find_single_match(data, '<p>([^<]+)<\/p>')
        else:
            title = item.contentSerieName + ' (' + server + ') ' + language
            plot = item.plot

        thumbnail = servertools.guess_server_thumbnail(title)

        if 'player' not in url and 'php' in url:
            itemlist.append(item.clone(title=title,
                                       url=url,
                                       action="play",
                                       plot=plot,
                                       thumbnail=thumbnail,
                                       server=server,
                                       quality='',
                                       language=language
                                       ))
    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_pelicula_to_library",
                             extra="findvideos",
                             contentTitle=item.contentTitle
                             ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if 'your' in item.url:
        item.url = 'http://www.yourupload.com/embed/' + scrapertools.find_single_match(data, 'src=".*?code=(.*?)"')
        itemlist.append(item)
    else:
        itemlist = servertools.find_video_items(data=data)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return lista(item)


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # categoria='peliculas'
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'search?q=animación'
        elif categoria == 'terror':
            item.url = host + 'search?q=terror'

        item.extra = 'peliculas'
        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
