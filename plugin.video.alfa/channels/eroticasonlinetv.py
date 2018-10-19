# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb

## italiafilm

'''
([^<]+) para extraer el texto entre dos tags “uno o más caracteres que no sean <" ^ cualquier caracter que no sea <
"([^"]+)" para extraer el valor de un atributo
\d+ para saltar números
\s+ para saltar espacios en blanco
(.*?) cuando la cosa se pone complicada

    "([^"]+)"
    \'([^\']+)\'


      + "[COLOR red]" + calidad + "[/COLOR]"



    next_page = int(current_page) + 1

    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist




    patron  = '<li class="border-radius-5 box-shadow">(.*?)</li>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match,'<a href="([^"]+)"')
        title = scrapertools.find_single_match(match,'title="([^"]+)"')
        thumbnail = scrapertools.find_single_match(match,'<img src="([^"]+)"')
        duracion = scrapertools.find_single_match(match,'<div class="time-infos">([^"]+)<span class="time-img">')
#        idioma = scrapertools.find_multiple_matches(match,'<img src="[^"]+" title="([^"]+)"')
#        plot = scrapertools.find_single_match(match,'<p><strong>Sinopsis:</strong> (.*?)</p>')
#        calidad = calidad.replace("Ahora en ", "")
#        genero = scrapertools.find_single_match(match,'<strong>Genero</strong>:\s+([^"]+)</div>')
#        idioma = scrapertools.find_single_match(match,'<strong>Idioma</strong>:([^"]+)</div>')
#        year = scrapertools.find_single_match(match,'</strong>:\s+(\d+)</div>')
#        calidad = scrapertools.find_single_match(match,'<strong>Calidad</strong>:(.*?)</div>')
#        thumbnail = host + thumbnail

#        title = title.replace("Ver Película","").replace("ver película","").replace("ver pelicula","").replace("Online Gratis","")
#        title = scrapertools.htmlclean(title).strip()
        plot = ""
        title = title + " (" + duracion + ")"




'''

host = 'http://www.peliculaseroticasonline.tv'

def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

#http://www.peliculaseroticasonline.tv/?s=anissa

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    # <div class="row">
	# 		<a href="http://gnula.mobi/16160/pelicula/sicario-2015/" title="Sicario (2015)">
	# 			<img src="http://image.tmdb.org/t/p/w300/voDX6lrA37mtk1pVVluVn9KI0us.jpg" title="Sicario (2015)" alt="Sicario (2015)" />
	# 		</a>
	# </div>

    patron = '<div class="row">.*?<a href="([^"]+)" title="([^"]+)">.*?<img src="(.*?)" title'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url,name,img   in matches:
        itemlist.append(item.clone(title=name, url=url, action="findvideos", show=name, thumbnail=img))

# <a href="http://gnula.mobi/page/2/?s=la" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i></a></div>

    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" aria-hidden="true"></i>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search", title="Next page >>" , url=paginacion))

    return itemlist



def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<h3>Categories:</h3>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

#                <li class="cat-item cat-item-1"><a href="http://www.peliculaseroticasonline.tv/genero/erotico/">Cine Erotico</a>
#                <li class="cat-item cat-item-110"><a href="http://www.peliculaseroticasonline.tv/genero/hardcore/" title="El Porno Duro o Porno Hardcore es un género Pornográfico en el que se muestran escenas de actos sexuales explícitos, donde es posible ver, generalmente con detalle">Hardcore</a>


    patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)".*?>([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        scrapedurl = "http://qwertty.net"+scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <div class="movie-poster">
#                               <a href="http://www.peliculaseroticasonline.tv/cheater-cheater-xxx-2018/">
#                                  <span class="center-icons"><span class="icon-hd tooltip-w" title="Calidad HD ">HD</span></span>
#                                  <div class="imagen"> <img src="http://www.peliculaseroticasonline.tv/wp-content/uploads/2018/09/Cheater-Cheater-2018-214x300.jpg" alt="Cheater Cheater XxX (2018)" /></div>
#                               </a>

    patron  = '<div class="movie-poster"><a href="([^"]+)".*?<img src="([^"]+)" alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        plot = ""
        contentTitle = scrapedtitle
#        title = "[COLOR yellow]" + time + "[/COLOR]  " + scrapedtitle


        url = urlparse.urljoin(item.url,scrapedurl)
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=scrapedtitle , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#        <div class="naviright"><a href="http://www.peliculaseroticasonline.tv/page/2/">Siguiente &raquo;</a>


# "Next page >>"
    next_page = scrapertools.find_single_match(data, '<div class="naviright"><a href="([^"]+)">Siguiente &raquo;</a>')
    if next_page:
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ))

    # except: pass
    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data


# <div id="option1" class="tab_part  "> <iframe src="/player/player.php?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9tMXJaUXppR2NnNC9DaGVhdGVyX0NoZWF0ZXIubXA0" frameborder="0" allowfullscreen></iframe></div>
# <div id="option2" class="tab_part  "> <iframe src="/player/player.php?id=aHR0cHM6Ly9vcGVubG9hZC5jby9lbWJlZC9tMXJaUXppR2NnNC9DaGVhdGVyX0NoZWF0ZXIubXA0" frameborder="0" allowfullscreen></iframe></div>
# <div id="tabdescarga" class="tab_part "> <iframe src="/player/videomega.php" frameborder="0" allowfullscreen></iframe></div>


    patron  = '<div id="option.*?<iframe src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl  in matches:
        url = scrapedurl.replace("/player/player.php?id=", "")
        url = decode_url(url)

#        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist


def decode_url(txt):
    _0x52f6x15 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~'
    reto = ''; n = 0
    # En las dos siguientes líneas, ABCEM ocupan 2 bytes cada letra! El replace lo deja en 1 byte. !!!!: АВСЕМ (10 bytes) ABCEM (5 bytes)
    txt = re.sub('[^АВСЕМA-Za-z0-9\.\,\~]', '', txt)
    txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M')

    while n < len(txt):
        a = _0x52f6x15.index(txt[n])
        n += 1
        b = _0x52f6x15.index(txt[n])
        n += 1
        c = _0x52f6x15.index(txt[n])
        n += 1
        d = _0x52f6x15.index(txt[n])
        n += 1

        a = a << 2 | b >> 4
        b = (b & 15) << 4 | c >> 2
        e = (c & 3) << 6 | d
        reto += chr(a)
        if c != 64: reto += chr(b)
        if d != 64: reto += chr(e)

    return urllib.unquote(reto)

def play(item):
    logger.info()
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
