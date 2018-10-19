# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para italiafilm
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------

import urlparse,urllib2,urllib,re
import os, sys

from core import jsontools as json
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
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

host = 'http://peliculasm.tv'

def mainlist(item):
    logger.info()
    itemlist = []

    # if item.url=="":
    #     item.url = "http://www.peliculaseroticas.net/"


    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/peliculas-recien-agregadas/"))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist

#http://gnula.mobi/?s=sicario

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/buscar.php?q=%s" % texto

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
#    data = scrapertools.get_match(data,'<div class="sbi-header">Películas por género</div>(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


#      <li><a class="icob icoa pore brdr5px fx" title="Películas de Accion" href="http://peliculasm.tv/peliculas-accion/">Películas de Accion</a></li>
    patron  = '<li><a class="icob icoa pore brdr5px fx".*?href="(.*?)">.*?de (.*?)</a>'
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

    patron  = '<a href="([^"]+)" title="Ver .*? ([^"]+) \((\d+)\)">.*?<img src="([^"]+)".*?</span>.*?<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedyear,scrapedthumbnail,calidad in matches:
        plot = ""
        contentTitle = scrapedtitle
        title = scrapedtitle + " (" + scrapedyear + ") " + "[COLOR yellow]" + calidad + "[/COLOR]"
#        scrapedtitle = scrapedtitle.replace("Ver Pel&iacute;cula", "")
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedurl = "https://hqcollect.tv" + scrapedurl
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        year = scrapedyear
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=scrapedurl, thumbnail=scrapedthumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))


#        <span class="current">1</span><a href="?pagina=2" title="Pagina 2">2</a>
# "Next page >>"
    try:
        patron  = '<span class="current">\d+</span>.*?<a href="([^"]+)" title="Pagina'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        next_page = item.url + next_page[0]
        itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )

    except: pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

 #    <ul class="tabs menu bold bxshd1 cntclsx f_left_lia fs14px liabrdr10px lnht30px txt_cen white clf mgbot10px">
 # 		 <li><a href="#ms1">VER CASTELLANO</a></li>
 #             <li><a href="#ms2">VER CASTELLANO</a></li>
 #             <li><a href="#ms3">VER LATINO</a></li>
 #             <li><a href="#ms4">VER LATINO</a></li></ul>
 #   <div class="tab_container">
 # <div id="ms1" class="tab_content br1px brdr10px bkcnt pd15px fs11px"><div style="text-align:center;"><iframe webkitallowfullscreen mozallowfullscreen allowfullscreen scrolling=auto data-src="http://ww2.peliculasm.tv/reproductor/pload.php?id=t32hR9xVl08/" scrolling="no" frameborder="0" width="620" height="360" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe></div></div>
 # <div id="ms2" class="tab_content br1px brdr10px bkcnt pd15px fs11px"><div style="text-align:center;"><iframe webkitallowfullscreen mozallowfullscreen allowfullscreen scrolling=auto data-src="https://goo.gl/NQHPo3" height="450" width="720" webkitAllowFullScreen mozallowfullscreen allowfullscreen frameborder="0" scrolling="no"></iframe></div></div>
 # <div id="ms3" class="tab_content br1px brdr10px bkcnt pd15px fs11px"><div style="text-align:center;"><iframe webkitallowfullscreen mozallowfullscreen allowfullscreen scrolling=auto data-src="http://ww2.peliculasm.tv/reproductor/pload.php?id=2PgD4_v9QWk/" scrolling="no" frameborder="0" width="620" height="360" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe></div></div>
 # <div id="ms4" class="tab_content br1px brdr10px bkcnt pd15px fs11px"><div style="text-align:center;"><iframe webkitallowfullscreen mozallowfullscreen allowfullscreen scrolling=auto data-src="https://goo.gl/AHWBQl" height="450" width="720" webkitAllowFullScreen mozallowfullscreen allowfullscreen frameborder="0" scrolling="no"></iframe></div></div> </div>
 # 			</div> <!--</pel_tra_bnr>-->
 # 					</div>

    patron  = 'data-src="(.*?)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl  in matches:
#        scrapedplot = ""
#        scrapedurl = ""
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
#        scrapedtitle = scrapedtitle + "  " + idioma + "  " + str(calidad)
#        scrapedurl = scrapedurl.replace("playvideo_", "")
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        itemlist.append(item.clone(action="play", title=scrapedurl, fulltitle = item.title, url=scrapedurl))
    return itemlist

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
