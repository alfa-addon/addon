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

host = 'http://www.perfectgirls.net'

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

#http://www.perfectgirls.net/search/anissa/

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s/" % texto

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

# <h3>Categories:</h3>
# <ul class="additional_list categories">
# <li class="additional_list__item"><a href="/category/5/Amateur__Homemade">Amateur, Homemade (21522 clips)</a></li>

    patron  = '<li class="additional_list__item"><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        url = urlparse.urljoin(item.url,scrapedurl) + "/1"
#        scrapedurl = "http://qwertty.net"+scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=url , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'Agregadas</h3>(.*?)<script>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <div class="list__item"><div class="list__item_link"><a href="/487898/Smiling_step_daughter_wants_to_try_out_sex_with_her_horny_step_dad__in_the_bedroom" title="Smiling step daughter wants to try out sex with her horny step dad, in the bedroom"><div class="list__item_link_image_container" />
# <img class="lazy thumb rotateable" alt="Smiling step daughter wants to try out sex with her horny step dad, in the bedroom" src="data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=" data-ext=".1" data-original="http://cdn-z3.perfectgirls.net/thumbs/487/898/thumb12.1.jpg" data-altsrc="http://cdn-z3.perfectgirls.net/thumbs/487/898/thumb12.1.jpg"  onmouseover="javascript:mstart(this);" onmouseout="javascript:mstop();" />
# </div>
# <span>Smiling step daughter wants to try out sex with her horny ...</span><time>9:00</time><div class="hd">HD</div></a></div>
# </div>


    patron  = '<div class="list__item_link"><a href="([^"]+)" title="([^"]+)">.*?data-original="([^"]+)".*?<time>([^"]+)</time>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail,time in matches:
        plot = ""
        contentTitle = scrapedtitle
        title = "[COLOR yellow]" + time + "[/COLOR]  " + scrapedtitle

#        scrapedtitle = scrapedtitle.replace("Ver Pel&iacute;cula", "")
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = "https://hqcollect.tv" + scrapedurl
#        scrapedurl = scrapedurl.replace("playvideo_", "")
        url = urlparse.urljoin(item.url,scrapedurl)
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=url, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#        <li class="pagination__item pagination__next"> <a class="btn_wrapper__btn" href="/2017-10-11">Next</a></li>
#        <li class="pagination__item pagination__next"> <a class="btn_wrapper__btn" href="2">Next</a></li>

# "Next page >>"
    next_page = scrapertools.find_single_match(data, '<a class="btn_wrapper__btn" href="([^"]+)">Next</a></li>')
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


# <source src="http://dl2.n3.6.cdn.perfectgirls.net/videos/aIlzTCOam4T2DQPiwCmmgw==,1507795118/487/898/487898.mp4" res="360" label="360p" type="video/mp4"/>
# <source src="http://dl1.n3.6.cdn.perfectgirls.net/videos/FojbLdWyqZKBksgeorxPrQ==,1507795118/487/898/487898-hd.mp4" res="720" label="720p" type="video/mp4" default/>

    patron  = '<source src="([^"]+)" res="\d+" label="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle  in matches:
#        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append(item.clone(action="play", title=scrapedtitle, fulltitle = item.title, url=scrapedurl))
    return itemlist
'''
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
'''
