# -*- coding: utf-8 -*-

import re
import urlparse

from core import channeltools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "thumbzilla"

host = 'https://www.thumbzilla.com'
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFF6E2802', '0xFFFAA171', '0xFFE9D7940'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__ - 1]
else:
    color1 = color2 = color3 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=__channel__, action="videos", title="Más Calientes", url=host,
                         viewmode="movie", thumbnail=get_thumb("/channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Nuevas", url=host + '/newest',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Tendencias", url=host + '/trending',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Mejores Videos", url=host + '/top',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Populares", url=host + '/popular',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Videos en HD", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Caseros", url=host + '/hd',
                         action="videos", viewmode="movie_with_plot", viewcontent='homemade',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Categorías", action="categorias",
                         url=host + '/categories/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=get_thumb("channels_adult.png")))

    itemlist.append(Item(channel=__channel__, title="Buscador", action="search", url=host,
                         thumbnail=get_thumb("channels_adult.png"), extra="buscar"))
    return itemlist


# REALMENTE PASA LA DIRECCION DE BUSQUEDA

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "video/search?q={0}".format(texto))
    # item.url = item.url % tecleado
    item.extra = "buscar"
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def videos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

# <li>
# 	<a class="js-thumb" href="/video/ph5b50336551d47/18-y-o-gf-fucks-me-like-a-pornstar-cumshot">
# 					<img id="3866773749175120371" src="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92)0.jpg" data-original="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92)0.jpg" width="320" height="180" data-indexthumb="3866773749175120371" data-id="175120371" data-defaultThumb="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92)0.jpg" data-thumb="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92){index}.jpg" />
# 				<noscript>
# 			<img id="3866773749175120371"
#                  class="lazy"
#                  data-src="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92)0.jpg"
#                  src=""
#                  width="320"
#                  height="180"
#                  data-indexthumb="3866773749175120371"
#                  data-id="175120371"
#                  data-defaultThumb="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92)0.jpg"
#                  data-thumb="https://ci.phncdn.com/videos/201807/19/175120371/original/(m=eafTGgaaayrGbid)(mh=PkjDmjPSmVitYQ92){index}.jpg" />
# 		</noscript>
#
# 		<span class="hoverInfo videos">
# 			<span><i class="views"></i>5.88K</span>
# 			<span><i class="rating"></i>86%</span>
# 		</span>
# 		<span class="info">
# 			<span class="title">18 y/o GF fucks me like a pornstar...cumshot</span>
# 			<span class="duration">5:45</span>
# 							<span class="hd">HD</span>
# 					</span>
# 	</a>
# </li>

    patron = '<a class="[^"]+" href="([^"]+)">'  # url
    patron += '<img id="[^"]+".*?src="([^"]+)".*?'  # img
    patron += '<span class="title">([^<]+)</span>.*?'  # title
    patron += '<span class="duration">([^<]+)</span>'  # time
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedthumbnail, scrapedtitle, time in matches:
        title = "[%s] %s" % (time, scrapedtitle)

        itemlist.append(Item(channel=item.channel, action='play', title=title, thumbnail=scrapedthumbnail,
                             url=host + scrapedurl, contentTile=scrapedtitle, fanart=scrapedthumbnail))

    paginacion = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />').replace('amp;', '')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="videos",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # logger.info(data)
    patron = 'class="checkHomepage"><a href="([^"]+)".*?'  # url
    patron += '<span class="count">([^<]+)</span>'  # title, vids

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, vids in matches:
        scrapedtitle = scrapedurl.replace('/categories/', '').replace('-', ' ').title()
        title = "%s (%s)" % (scrapedtitle, vids.title())
        thumbnail = item.thumbnail
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(Item(channel=item.channel, action="videos", fanart=thumbnail,
                             title=title, url=url, thumbnail=thumbnail,
                             viewmode="movie_with_plot", folder=True))

    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    # logger.info(data)

# <li><a class="qualityButton" data-quality="https://dm.phncdn.com/videos/201807/21/175417891/240P_400K_175417891.mp4?ttl=1532284143&ri=1228800&rs=552&hash=72a069b1aaf2fbd4f63f01b3879493eb">240P</a></li>
# <li><a class="qualityButton" data-quality="https://dm.phncdn.com/videos/201807/21/175417891/480P_600K_175417891.mp4?ttl=1532284143&ri=1228800&rs=1128&hash=53fd8e919fad1181df81256230350c57">480P</a></li>
# <li><a class="qualityButton active" data-quality="https://dm.phncdn.com/videos/201807/21/175417891/720P_1500K_175417891.mp4?ttl=1532284143&ri=1228800&rs=2096&hash=aaf7607b9432378cbec89c983e89b9fe">720P</a></li>

#    patron = '<li><a class="qualityButton.*?data-quality="([^"]+)">([^"]+)</a></li>'
    patron = '<li><a class="qualityButton active" data-quality="([^"]+)">([^"]+)</a></li>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl,calidad in matches:
    #    scrapedurl = scrapedurl.replace('\\', '')
        title = "[COLOR yellow](%s)[/COLOR] %s" % (calidad, item.contentTile)
    #    server = servertools.get_server_from_url(scrapedurl)
        itemlist.append(item.clone(channel=item.channel, action="play", title=item.title , url=scrapedurl , folder=True) )
#        itemlist.append(item.clone(action='play', title=scrapedurl, server=scrapedurl, mediatype='movie', url=scrapedurl))

    return itemlist
