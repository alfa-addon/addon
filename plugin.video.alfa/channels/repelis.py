# -*- coding: utf-8 -*-

import re
import urlparse

from core import scrapertools
from core import servertools
from core import httptools
from core import tmdb
from core.item import Item
from platformcode import config, logger


# Main list manual
def mainlist(item):
    logger.info()
    itemlist = []

    item.url = "http://www.repelis.tv/pag/1"

    mifan = "http://www.psicocine.com/wp-content/uploads/2013/08/Bad_Robot_Logo.jpg"

    itemlist.append(Item(channel=item.channel, action="menupelis", title="Peliculas", url="http://www.repelis.tv/pag/1",
                         thumbnail="http://www.gaceta.es/sites/default/files/styles/668x300/public"
                                   "/metro_goldwyn_mayer_1926-web.png?itok=-lRSR9ZC",
                         fanart=mifan))
    itemlist.append(Item(channel=item.channel, action="menuestre", title="Estrenos",
                         url="http://www.repelis.tv/archivos/estrenos/pag/1",
                         thumbnail="http://t0.gstatic.com/images?q=tbn"
                                   ":ANd9GcS4g68rmeLQFuX7iCrPwd00FI_OlINZXCYXEFrJHTZ0VSHefIIbaw",
                         fanart=mifan))
    itemlist.append(
            Item(channel=item.channel, action="menudesta", title="Destacadas", url="http://www.repelis.tv/pag/1",
                 thumbnail="http://img.irtve.es/v/1074982/", fanart=mifan))
    itemlist.append(Item(channel=item.channel, action="menupelis", title="Proximos estrenos",
                         url="http://www.repelis.tv/archivos/proximos-estrenos/pag/1",
                         thumbnail="https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcTpsRC"
                                   "-GTYzCqhor2gIDfAB61XeymwgXWSVBHoRAKs2c5HAn29f&reload=on",
                         fanart=mifan))
    itemlist.append(Item(channel=item.channel, action="menupelis", title="Todas las Peliculas",
                         url="http://www.repelis.tv/pag/1",
                         thumbnail="https://freaksociety.files.wordpress.com/2012/02/logos-cine.jpg", fanart=mifan))

    if config.get_setting("adult_mode") != 0:
        itemlist.append(Item(channel=item.channel, action="menupelis", title="Eroticas +18",
                             url="http://www.repelis.tv/genero/eroticas/pag/1",
                             thumbnail="http://www.topkamisetas.com/catalogo/images/TB0005.gif",
                             fanart="http://www.topkamisetas.com/catalogo/images/TB0005.gif", extra='adult'))
        # Quito la busqueda por aÃ±o si no esta enabled el adultmode, porque no hay manera de filtrar los enlaces
        # eroticos72
        itemlist.append(
                Item(channel=item.channel, action="poranyo", title="Por Año", url="http://www.repelis.tv/anio/2016",
                     thumbnail="http://t3.gstatic.com/images?q=tbn:ANd9GcSkxiYXdBcI0cvBLsb_nNlz_dWXHRl2Q"
                               "-ER9dPnP1gNUudhrqlR",
                     fanart=mifan))

    # Por categoria si que filtra la categoria de eroticos
    itemlist.append(Item(channel=item.channel, action="porcateg", title="Por Categoria",
                         url="http://www.repelis.tv/genero/accion/pag/1",
                         thumbnail="http://www.logopro.it/blog/wp-content/uploads/2013/07/categoria-sigaretta"
                                   "-elettronica.png",
                         fanart=mifan))
    itemlist.append(
            Item(channel=item.channel, action="search", title="Buscar...", url="http://www.repelis.tv/search/?s=",
                 thumbnail="http://thumbs.dreamstime.com/x/buscar-pistas-13159747.jpg", fanart=mifan))

    return itemlist



def menupelis(item):
    logger.info(item.url)

    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')

    if item.extra == '':
        section = 'Recién Agregadas'
    elif item.extra == 'year':
        section = 'del Año \d{4}'
    elif item.extra == 'adult':
        section = 'de Eróticas \+18'
    else:
        section = 'de %s'%item.extra

    patronenlaces = '<h.>Películas %s<\/h.>.*?>(.*?)<\/section>'%section


    matchesenlaces = re.compile(patronenlaces, re.DOTALL).findall(data)

    for bloque_enlaces in matchesenlaces:

        patron = '<div class="poster-media-card">.*?'
        patron += '<a href="(.*?)".*?title="(.*?)"(.*?)'
        patron += '<img src="(.*?)"'
        matches = re.compile(patron, re.DOTALL).findall(bloque_enlaces)

        for scrapedurl, scrapedtitle, extra_info, scrapedthumbnail in matches:
            logger.info("He encontrado el segundo bloque")
            logger.info("extra_info: %s" % extra_info)
            title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
            title = title.replace("Online", "");
            url = urlparse.urljoin(item.url, scrapedurl)
            thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
            quality = scrapertools.find_single_match(extra_info, 'calidad.*?>Calidad (.*?)<')
            year = scrapertools.find_single_match(extra_info, '"anio">(\d{4})<')
            language = scrapertools.find_multiple_matches(extra_info, 'class="(latino|espanol|subtitulado)"')
            # if language = 'ingles':
            #    language='vo'
            new_item=Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                                 thumbnail=thumbnail, fanart=thumbnail, language=language, quality=quality,
                                 infoLabels={'year': year})
            if year:
                tmdb.set_infoLabels_item(new_item)

            itemlist.append(new_item)

    try:
        next_page = scrapertools.get_match(data, '<span class="current">\d+</span><a href="([^"]+)"')
        title = "[COLOR red][B]Pagina siguiente »[/B][/COLOR]"
        itemlist.append(
                Item(channel=item.channel, title=title, url=next_page, action="menupelis", thumbnail=item.thumbnail,
                     fanart=item.fanart, folder=True, extra=item.extra))
    except:
        pass
    return itemlist


# Peliculas Destacadas
def menudesta(item):
    logger.info(item.url)

    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')

    patronenlaces = '<h3>.*?Destacadas.*?>(.*?)<h3>'
    matchesenlaces = re.compile(patronenlaces, re.DOTALL).findall(data)

    for bloque_enlaces in matchesenlaces:

        # patron = '<a href="([^"]+)" title="([^"]+)"> <div class="poster".*?<img src="([^"]+)"'

        patron = '<div class="poster-media-card">.*?'
        patron += '<a href="(.*?)".*?title="(.*?)".*?'
        patron += '<img src="(.*?)"'

        matches = re.compile(patron, re.DOTALL).findall(bloque_enlaces)
        for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
            title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
            title = title.replace("Online", "");
            url = urlparse.urljoin(item.url, scrapedurl)
            thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                                 thumbnail=thumbnail, fanart=thumbnail))

    return itemlist


# Peliculas de Estreno
def menuestre(item):
    logger.info(item.url)

    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')
    patronenlaces = '<h1>Estrenos</h1>(.*?)</section>'
    matchesenlaces = re.compile(patronenlaces, re.DOTALL).findall(data)

    for bloque_enlaces in matchesenlaces:

        # patron = '<a href="([^"]+)" title="([^"]+)"> <div class="poster".*?<img src="([^"]+)"'

        patron = '<div class="poster-media-card">.*?'
        patron += '<a href="(.*?)".*?title="(.*?)"(.*?)'
        patron += '<img src="(.*?)"'

        matches = re.compile(patron, re.DOTALL).findall(bloque_enlaces)
        for scrapedurl, scrapedtitle, extra_info, scrapedthumbnail in matches:
            title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
            title = title.replace("Online", "");
            url = urlparse.urljoin(item.url, scrapedurl)
            thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
            quality = scrapertools.find_single_match(extra_info, 'calidad.*?>Calidad (.*?)<')
            year = scrapertools.find_single_match(extra_info, '"anio">(\d{4})<')
            language = scrapertools.find_single_match(extra_info, 'class="(latino|espanol|subtitulado)"')

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                                 thumbnail=thumbnail, fanart=thumbnail, language=language, quality=quality,
                                 infoLabels={'year': year}))

    ## PaginaciÃ³n
    # <span class="current">2</span><a href="http://www.repelis.tv/page/3"

    # Si falla no muestra ">> PÃ¡gina siguiente"
    try:
        next_page = scrapertools.get_match(data, '<span class="current">\d+</span><a href="([^"]+)"')
        title = "[COLOR red][B]Pagina siguiente »[/B][/COLOR]"
        itemlist.append(Item(channel=item.channel, title=title, url=next_page, action="menuestre", folder=True))
    except:
        pass
    return itemlist


def findvideos(item):
    logger.info(item.url)

    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')

    patron = '<h2>Sinopsis</h2>.*?<p>(.*?)</p>.*?<div id="informacion".*?</h2>.*?<p>(.*?)</p>'  # titulo
    matches = re.compile(patron, re.DOTALL).findall(data)
    for sinopsis, title in matches:
        title = "[COLOR white][B]" + title + "[/B][/COLOR]"

    patron = '<div id="informacion".*?>(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedplot in matches:
        splot = title + "\n\n"
        plot = scrapedplot
        plot = re.sub('<h2>', "[COLOR red][B]", plot)
        plot = re.sub('</h2>', "[/B][/COLOR] : ", plot)
        plot = re.sub('<p>', "[COLOR green]", plot)
        plot = re.sub('</p>', "[/COLOR]\n", plot)
        plot = re.sub('<[^>]+>', "", plot)
        splot += plot + "\n[COLOR red][B] Sinopsis[/B][/COLOR]\n " + sinopsis

    # datos de los enlaces
    '''
    <a rel="nofollow" href="(.*?)".*?<td><img.*?</td><td>(.*?)</td><td>(.*?)</td></tr>
 
    ">Vimple</td>
    '''

    patron = '<tbody>(.*?)</tbody>'
    matchesx = re.compile(patron, re.DOTALL).findall(data)

    for bloq in matchesx:
        patron = 'href="(.*?)".*?0 0">(.*?)</.*?<td>(.*?)</.*?<td>(.*?)<'

        matches = re.compile(patron, re.DOTALL).findall(bloq)

    for scrapedurl, scrapedserver, scrapedlang, scrapedquality in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.info("Lang:[" + scrapedlang + "] Quality[" + scrapedquality + "] URL[" + url + "]")
        patronenlaces = '.*?://(.*?)/'
        matchesenlaces = re.compile(patronenlaces, re.DOTALL).findall(scrapedurl)
        scrapedtitle = ""
        if scrapedserver == 'Vimple':
            scrapedserver = 'vimpleru'
        elif scrapedserver == 'Ok.ru':
            scrapedserver = 'okru'
        server = servertools.get_server_name(scrapedserver)
        for scrapedenlace in matchesenlaces:
            scrapedtitle = title + "  [COLOR white][ [/COLOR]" + "[COLOR green]" + scrapedquality + "[/COLOR]" + "[COLOR white] ][/COLOR]" + " [COLOR red] [" + scrapedlang + "][/COLOR]  » " + scrapedserver

        itemlist.append(Item(channel=item.channel, action="play", title=scrapedtitle, extra=title, url=url,
                             fanart=item.thumbnail, thumbnail=item.thumbnail, plot=splot, language=scrapedlang,
                             quality=scrapedquality, server=server))
    if itemlist:
        itemlist.append(Item(channel=item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir pelicula a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail=item.thumbnail,
                                 fulltitle=item.fulltitle))
    return itemlist


def play(item):
    logger.info()
    itemlist =[]

    data = httptools.downloadpage(item.url).data

    enc = scrapertools.find_multiple_matches(data, "Player\.decode\('(.*?)'\)")
    dec=''
    for cod in enc:
        dec+=decode(cod)
    url = scrapertools.find_single_match(dec,'src="(.*?)"')
    itemlist.append(item.clone(url=url))

    return itemlist


def search(item, texto):
    logger.info(item.url)
    texto = texto.replace(" ", "+")
    item.url = 'http://www.repelis.tv/buscar/?s=%s' % (texto)
    logger.info(item.url)

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')

    logger.info("data: " + data)

    patron = '<div class="col-xs-2">.*?'
    patron += '<div class="row">.*?'
    patron += '<a href="(.*?)" title="(.*?)">.*?'
    patron += '<img src="(.*?)"'

    logger.info(patron)

    matches = re.compile(patron, re.DOTALL).findall(data)

    itemlist = []

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
        title = title.replace("Online", "")
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        logger.info(url)
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                             thumbnail=thumbnail, fanart=thumbnail))

    return itemlist


def poranyo(item):
    logger.info(item.url)

    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')

    patron = '<option value="([^"]+)">(.*?)</option>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
        title = title.replace("Online", "")
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="menupelis", title=title, fulltitle=title, url=url,
                             fanart=item.fanart, extra='year'))

    return itemlist


def porcateg(item):
    logger.info(item.url)
    itemlist = []

    data = httptools.downloadpage(item.url).data.decode('iso-8859-1').encode('utf-8')
    patron = '<li class="cat-item cat-item-3">.*?<a href="([^"]+)" title="([^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.remove_show_from_title(scrapedtitle, "Ver Película")
        title = title.replace("Online", "")
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.info(url)
        # si no esta permitidas categoria adultos, la filtramos
        extra = title
        adult_mode = config.get_setting("adult_mode")
        if adult_mode != 0:
            if 'erotic' in scrapedurl:
                extra = 'adult'
        else:
            extra=title

        if (extra=='adult' and adult_mode != 0) or extra != 'adult':
            itemlist.append(Item(channel=item.channel, action="menupelis", title=title, fulltitle=title, url=url,
                                 fanart=item.fanart, extra = extra))

    return itemlist


def decode(string):

    keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    output = ''
    input = string.encode('utf8')
    i = 0
    while i < len(input):

        enc1 = keyStr.index(input[i])
        i += 1
        enc2 = keyStr.index(input[i])
        i += 1
        enc3 = keyStr.index(input[i])
        i += 1
        enc4 = keyStr.index(input[i])
        i += 1

        chr1 = (enc1 << 2) | (enc2 >> 4)
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
        chr3 = ((enc3 & 3) << 6) | enc4

        output = output + unichr(chr1)
        if enc3 != 64:
            output = output + unichr(chr2)

        if enc4 != 64:
            output = output + unichr(chr3)

    output = output.decode('utf8')

    return output
