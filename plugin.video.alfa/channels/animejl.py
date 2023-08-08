# -*- coding: utf-8 -*-
# -*- Channel AnimeJL -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

from platformcode import logger
from platformcode import config
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from channelselector import get_thumb
import sys
import re

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib

canonical = {
             'channel': 'animejl', 
             'host': config.get_setting("current_host", 'animejl', default=''), 
             'host_alt': ["https://www.anime-jl.net/"], 
             'host_black_list': [], 
             'pattern': '<ul\s*class="Menu">\s*<li\s*class="Current">\s*<a\s*href="([^"]+)"', 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

host = 'https://www.anime-jl.net/'

def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(
        Item(
            action = "new_episodes",
            channel = item.channel,
            thumbnail = get_thumb('new_episodes', auto=True),
            title = "Nuevos Episodios",
            url = host,
            viewType = "episodes"
        )
    )

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            thumbnail = get_thumb('all', auto=True),
            title = "Todas",
            url = "%s%s" % (host, 'animes'),
            viewType = "videos"
        )
    )

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            thumbnail = get_thumb('movies',auto=True),
            title = "Películas",
            url = "%s%s" % (host, 'animes?type%5B%5D=2&order=default'),
            viewType = "movies"
        )
    )

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            thumbnail = get_thumb('tvshows', auto=True),
            title = "Series",
            url = "%s%s" % (host, 'animes?type%5B%5D=1&order=default'),
            viewType = "tvshows"
        )
    )

    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            thumbnail = get_thumb('search', auto=True),
            title = "Buscar",
            url = "%s%s" % (host, 'animes?q='),
            viewType = "videos"
        )
    )

    return itemlist


def get_source(url, json=False, unescape=True, **opt):
    logger.info()

    opt['canonical'] = canonical
    data = httptools.downloadpage(url, **opt)

    if json:
        data = data.json
    else:
        data = data.data
        data = scrapertools.replace(r'\n|\r|\t|&nbsp;|<br>|\s{2,}|\(|\)', "", data) if unescape else data

    return data


def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, "<h2>Últimos episodios agregados</h2>.*?</ul>")
    patron = "<li><a href='(.*?)' class.*?<img src='(.*?)' alt='(.*?)'></span><span class='Capi'>(.*?)</span>"

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedepi in matches:
        url = scrapedurl
        thumbnail = host+scrapedthumbnail
        title = '%s %s' % (scrapedtitle.replace('ver ', ''), scrapedepi)
        itemlist.append(
            Item(
                 action = 'findvideos',
                 channel = item.channel,
                 contentSerieName = scrapedtitle,
                 thumbnail = thumbnail,
                 title = title,
                 url = url
            )
        )

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = "<article class='Anime alt B'><a href='([^']+)'>.*?class=.*?<img src='([^']+)' alt='([^']+)'>"
    patron += "</figure><span class='Type' .*?>([^']+)</span>.*?star.*?<p>([^<]+)</p>"

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, _type, plot in matches:
        url = scrapedurl
        thumbnail = host+scrapedthumbnail
        scrapedtitle = scrapertools.htmlparser(scrapedtitle) # htmlparser convierte los carateres HTML (&#038;, ...) a su equivalente utf-8
        plot = scrapertools.htmlparser(plot)

        season = ''

        # El siguiente código hacía que algunos títulos quedasen vacios 
        # ya que no se estaba comprobando que despues de 'season' vaya un numero.
        # Ademas esta web usa la palabra 'Temporada' no 'season'.

        # if 'season' in scrapedtitle.lower():
            # season = scrapertools.find_single_match(scrapedtitle, 'season (\d+)')
            # scrapedtitle = scrapertools.find_single_match(scrapedtitle, '(.*?) season')

        # Reemplazo, aunque no parece que se esté mostrando la temporada en ninguna parte, 
        # por lo que la segunda linea está comentada, para que así se siga mostrando al menos en el titulo
        # pero dejo este reemplazo por si contentSeasonNumber sí se usase en algun caso. Lo ignoro.
        seasonPattern = '\s+Temporada\s+(\d+)'
        if re.search(seasonPattern, scrapedtitle):
            season = scrapertools.find_single_match(scrapedtitle, seasonPattern)
            # scrapedtitle = re.sub(seasonPattern, '', scrapedtitle)

        new_item = Item(
                    action = 'episodesxseason',
                    channel = item.channel,
                    plot = plot,
                    thumbnail = thumbnail,
                    title = scrapedtitle,
                    type = _type,
                    url = url
                )

        if _type.lower() == 'anime':
            new_item.contentType = "tvshow"
            new_item.contentSerieName = scrapedtitle
            new_item.contentSeasonNumber = season
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = scrapedtitle

        itemlist.append(new_item)

    # Paginacion
    next_patron = r'<a class="page-link" href="([^"]+)" rel="next">'
    next_page = scrapertools.find_single_match(data, next_patron)
    # La web convierte el 'path' de la url de paginacion en caracteres HTML,
    # lo cual hace que el parametro de paginación en la url no sea el esperado (amp;page en lugar de page)
    # por ejemplo, se espera:
    # https://www.anime-jl.net/animes?q=español&page=2
    # pero, sin usar htmlparser, se obtiene:
    # https://www.anime-jl.net/animes?q=espa%C3%B1ol&amp;page=2
    # mientras que el navegador opera sin problema, kodi no parece interpretarlo correctamente.
    next_page = scrapertools.htmlparser(next_page)
    # logger.info(next_page, True)
    
    if next_page != '':
        itemlist.append(
            Item(
                action = "list_all",
                channel = item.channel,
                thumbnail = 'https://s16.postimg.cc/9okdu7hhx/siguiente.png',
                title = "Siguiente página >>",
                url = "%s%s" % (host, next_page) if not host in next_page else next_page,
                viewType = item.viewType
            )
        )

    return itemlist


def episodios(item):
    logger.info()
    item.videolibrary = True

    return episodesxseason(item)


def episodesxseason(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)

    patron = '\[(\d+),"([^"]+)","([^"]+)",[^\]]+\]'
    matches = scrapertools.find_multiple_matches(data, patron)

    for epi_num, epi_url, epi_thumb in matches:
        title = 'Episodio %s' % epi_num
        url = "%s/%s" % (item.url, epi_url)

        itemlist.append(
            Item(
                action = 'findvideos',
                channel = item.channel,
                contentSerieName = title,
                thumbnail = item.thumbnail,
                title = title,
                url = url
            )
        )

    if item.type.lower != 'anime' and len(itemlist) == 1:
        return findvideos(itemlist[0])

    reversed(itemlist)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not (item.videolibrary or item.extra):
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentType = "tvshow",
                contentSerieName = item.contentSerieName,
                extra = "episodios",
                text_color = "yellow",
                title = 'Añadir esta serie a la videoteca',
                url = item.url
            )
        )

    return itemlist


def search(item, texto):
    logger.info()
    texto = urllib.quote_plus(texto, "") #https://docs.python.org/2/library/urllib.html#urllib.quote_plus (escapa los caracteres de la busqueda para usarlos en la URL)
    item.url = item.url + texto

    try:
        if texto != '':
            return list_all(item)
        else:
            return []

    except:
        # ya se esta importando en la cabecera
        # import sys

        for line in sys.exc_info():
            logger.error("%s" % line)

        return []


def findvideos(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = r'video\[\d+\]\s*=\s*\'<iframe.*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl in matches:
        #import base64
        #enc_url = scrapertools.find_single_match(scrapedurl, r'hs=(.*)$')
        #url = urllib.unquote(base64.b64decode(rot13(enc_url)))
        #if url != '':
        if scrapedurl != '':
            itemlist.append(
                Item(
                    action = 'play',
                    channel = item.channel,
                    infoLabels = item.infoLabels,
                    title = '%s',
                    url = scrapedurl,
                    viewType = item.viewType
                )
            )

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    return itemlist


def newest(categoria):
    logger.info()

    itemlist = []
    item = Item()

    try:
        if categoria == 'anime':
            item.url = host

        itemlist = new_episodes(item)

        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()

        return itemlist

    except:
        import sys

        for line in sys.exc_info():
            logger.error("{0}".format(line))

        return []


def rot13(s):
    d = {chr(i+c): chr((i+13) % 26 + c) for i in range(26) for c in (65, 97)}
    return ''.join([d.get(c, c) for c in s])
