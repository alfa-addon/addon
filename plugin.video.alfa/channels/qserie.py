# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.qserie.com'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Series", action="todas", url=host,
                         thumbnail='https://s27.postimg.cc/iahczwgrn/series.png',
                         fanart='https://s27.postimg.cc/iahczwgrn/series.png'))

    itemlist.append(Item(channel=item.channel, title="Generos", action="generos", url=host,
                         thumbnail='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                         fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png'))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="lasmas", url=host,
                         thumbnail='https://s17.postimg.cc/fwi1y99en/a-z.png',
                         fanart='https://s17.postimg.cc/fwi1y99en/a-z.png', extra='letras'))

    itemlist.append(Item(channel=item.channel, title="Ultimas Agregadas", action="ultimas", url=host,
                         thumbnail='https://s22.postimg.cc/cb7nmhwv5/ultimas.png',
                         fanart='https://s22.postimg.cc/cb7nmhwv5/ultimas.png'))

    itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="lasmas", url=host,
                         thumbnail='https://s9.postimg.cc/wmhzu9d7z/vistas.png',
                         fanart='https://s9.postimg.cc/wmhzu9d7z/vistas.png', extra='Vista'))

    itemlist.append(Item(channel=item.channel, title="Mas Votadas", action="lasmas", url=host,
                         thumbnail='https://s7.postimg.cc/9kg1nthzf/votadas.png',
                         fanart='https://s7.postimg.cc/9kg1nthzf/votadas.png', extra='Votos'))

    return itemlist


def todas(item):
    logger.info()
    audio = {'Latino': '[COLOR limegreen]LATINO[/COLOR]', 'Español': '[COLOR yellow]ESPAÑOL[/COLOR]',
             'Sub Español': '[COLOR red]ORIGINAL SUBTITULADO[/COLOR]'}
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    patron = '<h2 class=.*?><a href="([^"]+)" title="([^"]+)">.*?\/h2>.*?<img src="([^"]+)".*?\/><\/a>.*?<p>([^<]+)<\/p>.*?<strong>Genero<\/strong>: .*?, (.*?)<\/div>.*?<img src=.*?>([^<]+)<\/div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot, scrapedyear, scrapedidioma in matches:
        idioma = scrapedidioma.strip()
        idioma = scrapertools.decodeHtmlentities(idioma)
        url = urlparse.urljoin(item.url, scrapedurl)
        year = scrapedyear

        title = scrapertools.decodeHtmlentities(scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = scrapedplot
        fanart = 'https://s31.postimg.cc/dousrbu9n/qserie.png'
        itemlist.append(
            Item(channel=item.channel, action="temporadas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fanart=fanart, extra=idioma, contentSerieName=scrapedtitle, infoLabels={'year': year},
                 language=idioma))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion
    siguiente = ''
    title = ''
    actual = scrapertools.find_single_match(data, '<li><a href=".*?"><span><b>([^<]+)<\/b><\/span><\/a><\/li>')
    ultima = scrapertools.find_single_match(data, '<li><a href=".*?page=([^"]+)">Ultima<\/a><\/li>')
    if 'page' in item.title:
        while not item.url.endswith('='): item.url = item.url[:-1]
    if actual:
        siguiente = int(actual) + 1
        if item.url.endswith('='):
            siguiente_url = item.url + str(siguiente)
        else:
            siguiente_url = item.url + '?&page=' + str(siguiente)
    if actual and ultima and siguiente <= int(ultima):
        titlen = 'Pagina Siguiente >>> ' + str(actual) + '/' + str(ultima)
        fanart = 'https://s32.postimg.cc/4q1u1hxnp/qserie.png'
        thumbnail = 'https://s16.postimg.cc/9okdu7hhx/siguiente.png'
        itemlist.append(Item(channel=item.channel, action="todas", title=titlen, url=siguiente_url, fanart=fanart,
                             thumbnail=thumbnail))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    url_base = item.url
    patron = '<a href="javascript:.*?;" class="lccn"><b>([^<]+)<\/b><\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    temp = 1
    if matches:
        for scrapedtitle in matches:
            url = url_base
            title = scrapedtitle
            thumbnail = item.thumbnail
            plot = item.plot
            contentSeasonNumber = str(temp)

            infoLabels['season'] = contentSeasonNumber
            fanart = scrapertools.find_single_match(data, '<img src="([^"]+)"/>.*?</a>')
            itemlist.append(
                Item(channel=item.channel, action="episodiosxtemp", title=title, fulltitle=item.title, url=url,
                     thumbnail=thumbnail, plot=plot, fanart=fanart, contentSeasonNumber=contentSeasonNumber,
                     contentSerieName=item.contentSerieName, infoLabels=infoLabels))
            temp = temp + 1

        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_serie_to_library", extra="episodios",
                                 contentSerieName=item.contentSerieName))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        return itemlist
    else:
        item.title = ''
        item.modo = 'unico'
        return episodiosxtemp(item)


def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    if item.modo == 'unico':
        itemlist += episodiosxtemp(item)
    else:
        for tempitem in templist:
            itemlist += episodiosxtemp(tempitem)

    return itemlist


def episodiosxtemp(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    infoLabels = item.infoLabels
    temp = item.contentSeasonNumber
    if item.title == '':
        temp = '1'
        item.contenSeasonNumber = temp
        infoLabels['season'] = temp

        patron = '<li><a href="([^"]+)" class="lcc"><b>([^<]+)<\/b>.*?<\/a><\/li>'

    else:
        patron = '<li><a href="([^"]+)" class="lcc"><b>([^<]+)<\/b> - Temp\. ' + temp + '<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        capitulo = re.findall(r'\d+', scrapedtitle)
        contentEpisodeNumber = str(capitulo[0])
        infoLabels['episode'] = contentEpisodeNumber
        title = item.contentSerieName + ' ' + temp + 'x' + contentEpisodeNumber
        thumbnail = item.thumbnail
        plot = item.plot
        fanart = item.fanart
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=item.fulltitle, url=url,
                             thumbnail=item.thumbnail, plot=plot, extra=item.extra, extra1=item.extra1,
                             extra2=item.extra2, infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if item.modo == 'unico':
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_serie_to_library", extra="episodios",
                                 contentSerieName=item.contentSerieName, modo='unico',
                                 contentSeasonNumber=item.contenSeasonNumber))

    return itemlist


def generos(item):
    tgenero = {"comedia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
               "suspenso": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
               "drama": "https://s16.postimg.cc/94sia332d/drama.png",
               "acción": "https://s3.postimg.cc/y6o9puflv/accion.png",
               "aventura": "https://s10.postimg.cc/6su40czih/aventura.png",
               "aventuras": "https://s10.postimg.cc/6su40czih/aventura.png",
               "romance": "https://s15.postimg.cc/fb5j8cl63/romance.png",
               "infantil": "https://s23.postimg.cc/g5rmazozv/infantil.png",
               "ciencia ficción": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
               "terror": "https://s7.postimg.cc/yi0gij3gb/terror.png",
               "anime": 'https://s2.postimg.cc/s38borokp/anime.png',
               "animes": "https://s2.postimg.cc/s38borokp/anime.png",
               "dibujos": "https://s2.postimg.cc/aqwqksyop/dibujos.png",
               "documental": "https://s16.postimg.cc/7xjj4bmol/documental.png",
               "fantástico": "https://s10.postimg.cc/pbkbs6j55/fantastico.png",
               "intriga": "https://s27.postimg.cc/v9og43u2b/intriga.png",
               "musical": "https://s29.postimg.cc/bbxmdh9c7/musical.png",
               "secuela": "https://s7.postimg.cc/bti0nauh7/secuela.png",
               "thriller (suspenso)": "https://s22.postimg.cc/5y9g0jsu9/thriller.png",
               "western": "https://s23.postimg.cc/lzyfbjzhn/western.png"}

    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li><a title="([^"]+)" href="([^"]+)" onclick=.*?'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle.decode('cp1252')
        title = title.encode('utf-8')
        if title.lower() in tgenero:
            thumbnail = tgenero[title.lower()]
            fanart = tgenero[title.lower()]
        else:
            thumbnail = ''
            fanart = ''
        plot = ''
        itemlist.append(
            Item(channel=item.channel, action="todas", title=title.lower(), fulltitle=item.fulltitle, url=url,
                 thumbnail=thumbnail, plot=plot, fanart=fanart))

    return itemlist


def ultimas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    realplot = ''
    patron = '<li><a title="([^"]+)" href="([^"]+)"><strong>.*?</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        data = httptools.downloadpage(scrapedurl).data
        thumbnail = scrapertools.get_match(data, '<link rel="image_src" href="([^"]+)"/>')
        realplot = scrapertools.find_single_match(data, '<p itemprop="articleBody">([^<]+)<\/p> ')
        plot = scrapertools.remove_htmltags(realplot)
        inutil = re.findall(r' Temporada \d', scrapedtitle)
        title = scrapedtitle
        title = scrapertools.decodeHtmlentities(title)
        realtitle = scrapedtitle.replace(inutil[0], '')
        fanart = 'https://s22.postimg.cc/cb7nmhwv5/ultimas.png'
        itemlist.append(
            Item(channel=item.channel, action="temporadas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 fanart=fanart, contentSerieName=realtitle))

    return itemlist


def lasmas(item):
    thumbletras = {'0-9': 'https://s32.postimg.cc/drojt686d/image.png',
                   '0 - 9': 'https://s32.postimg.cc/drojt686d/image.png',
                   '#': 'https://s32.postimg.cc/drojt686d/image.png',
                   'a': 'https://s32.postimg.cc/llp5ekfz9/image.png',
                   'b': 'https://s32.postimg.cc/y1qgm1yp1/image.png',
                   'c': 'https://s32.postimg.cc/vlon87gmd/image.png',
                   'd': 'https://s32.postimg.cc/3zlvnix9h/image.png',
                   'e': 'https://s32.postimg.cc/bgv32qmsl/image.png',
                   'f': 'https://s32.postimg.cc/y6u7vq605/image.png',
                   'g': 'https://s32.postimg.cc/9237ib6jp/image.png',
                   'h': 'https://s32.postimg.cc/812yt6pk5/image.png',
                   'i': 'https://s32.postimg.cc/6nbbxvqat/image.png',
                   'j': 'https://s32.postimg.cc/axpztgvdx/image.png',
                   'k': 'https://s32.postimg.cc/976yrzdut/image.png',
                   'l': 'https://s32.postimg.cc/fmal2e9yd/image.png',
                   'm': 'https://s32.postimg.cc/m19lz2go5/image.png',
                   'n': 'https://s32.postimg.cc/b2ycgvs2t/image.png',
                   'o': 'https://s32.postimg.cc/c6igsucpx/image.png',
                   'p': 'https://s32.postimg.cc/jnro82291/image.png',
                   'q': 'https://s32.postimg.cc/ve5lpfv1h/image.png',
                   'r': 'https://s32.postimg.cc/nmovqvqw5/image.png',
                   's': 'https://s32.postimg.cc/zd2t89jol/image.png',
                   't': 'https://s32.postimg.cc/wk9lo8jc5/image.png',
                   'u': 'https://s32.postimg.cc/w8s5bh2w5/image.png',
                   'v': 'https://s32.postimg.cc/e7dlrey91/image.png',
                   'w': 'https://s32.postimg.cc/fnp49k15x/image.png',
                   'x': 'https://s32.postimg.cc/dkep1w1d1/image.png',
                   'y': 'https://s32.postimg.cc/um7j3zg85/image.png',
                   'z': 'https://s32.postimg.cc/jb4vfm9d1/image.png'}

    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    realplot = ''
    if item.extra == 'letras':
        patron = '<li><a href="([^"]+)" title="Series que comienzan con.*?">([^<]+)</a></li>'
    else:
        patron = '<a href="([^"]+)" title="([^V]+)' + item.extra + '.*?">'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        if item.extra != 'letras':
            data = httptools.downloadpage(scrapedurl).data
            thumbnail = scrapertools.get_match(data, '<link rel="image_src" href="([^"]+)"/>')
            realplot = scrapertools.find_single_match(data, '<p itemprop="articleBody">([^<]+)<\/p> ')
            plot = scrapertools.remove_htmltags(realplot)
            action = 'temporadas'
        else:
            if scrapedtitle.lower() in thumbletras:
                thumbnail = thumbletras[scrapedtitle.lower()]
            else:
                thumbnail = ''
            plot = ''
            action = 'todas'
        title = scrapedtitle.replace(': ', '')
        title = scrapertools.decodeHtmlentities(title)
        if item.extra == 'letras':
            fanart = 'https://s17.postimg.cc/fwi1y99en/a-z.png'
        elif item.extra == 'Vista':
            fanart = 'https://s9.postimg.cc/wmhzu9d7z/vistas.png'
        else:
            fanart = ''

        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             fanart=fanart, contentSerieName=scrapedtitle))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    anterior = scrapertools.find_single_match(data, '<a class="left" href="([^"]+)" title="Cap.tulo Anterior"></a>')
    siguiente = scrapertools.find_single_match(data, '<a class="right" href="([^"]+)" title="Cap.tulo Siguiente"></a>')
    titulo = scrapertools.find_single_match(data,
                                            '<h1 class="tithd bold fs18px lnht30px ico_b pdtop10px">([^<]+)</h1> ')
    existe = scrapertools.find_single_match(data, '<center>La pel.cula que quieres ver no existe.</center>')

    from core import servertools
    itemlist.extend(servertools.find_video_items(data=data))
    for videoitem in itemlist:
        if 'youtube' in videoitem.url:
            itemlist.remove(videoitem)
    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.action = "play"
        videoitem.folder = False
        videoitem.fanart = item.fanart
        videoitem.title = titulo + " " + videoitem.server
    if item.extra2 != 'todos':
        data = httptools.downloadpage(anterior).data
        existe = scrapertools.find_single_match(data, '<center>La pel.cula que quieres ver no existe.</center>')
        if not existe:
            itemlist.append(Item(channel=item.channel, action="findvideos", title='Capitulo Anterior', url=anterior,
                                 thumbnail='https://s1.postimg.cc/dbq8gvldb/anterior.png', folder=True))

        data = httptools.downloadpage(siguiente).data
        existe = scrapertools.find_single_match(data, '<center>La pel.cula que quieres ver no existe.</center>')
        if not existe:
            itemlist.append(Item(channel=item.channel, action="findvideos", title='Capitulo Siguiente', url=siguiente,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png', folder=True))

    return itemlist
