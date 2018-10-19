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

    ([^<]+)
  \'([^\']+)\'
'''




host = 'http://pornboss.org'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="CLIPS" , action="peliculas", url=host + "/category/clips/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))

    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/category/movies/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist



def search(item, texto):
    logger.info("pelisalacarta.gmobi mainlist")
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


def categorias(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

# <div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>
# <ul class="uk-nav uk-nav-parent-icon uk-nav-side" data-uk-nav="{}">
# <li><a href="http://pornboss.org/category/movies/anal/" class="">Anal</a></li>
# <li><a href="http://pornboss.org/category/movies/big-tits/" class="">Big Tits</a></li><li><a href="http://pornboss.org/category/movies/feature/" class="">Feature</a></li><li><a href="http://pornboss.org/category/movies/foreign/" class="">Foreign</a></li><li><a href="http://pornboss.org/category/movies/gonzo/" class="">Gonzo</a></li><li><a href="http://pornboss.org/category/movies/lesbian/" class="">Lesbian</a></li><li><a href="http://pornboss.org/category/movies/milf/" class="">MILF</a></li><li><a href="http://pornboss.org/category/movies/teen/" class="">Teen</a></li>
# </ul>
# </div>
    dataM = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Movies</h3>(.*?)</div>')

    patron  = '<a href="([^<]+)" class="">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(dataM)
    scrapertools.printMatches(matches)

    itemlist.append( Item(channel=item.channel, title="PELICULAS" , text_color="gold", action="", url=""))

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title="       "+scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#    return itemlist

    dataC = scrapertools.get_match(data,'<div class="uk-panel uk-panel-box widget_nav_menu"><h3 class="uk-panel-title">Clips</h3>(.*?)</div>')

    patron  = '<a href="([^<]+)" class="">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(dataC)
    scrapertools.printMatches(matches)

    itemlist.append( Item(channel=item.channel, title="CLIPS" , text_color="gold", action="", url=""))

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title="       "+scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)


# <div class="uk-article-title">
#     <h1 style="float:left; width:662px; font-size: 18px; line-height: 18px; color: #555555; "><a href="http://pornboss.org/jules-jordan-august-taylor/" title="Jules Jordan &#8211; August Taylor">Jules Jordan &#8211; August Taylor</a></h1>
# 	    <div style="width:120px; text-align:right; float: right !important; font-size:10px; color: #999999;">
# 		::: 01.Mai 2018 :::
# 		</div>
# 	</div>
#     <a href="http://pornboss.org/2011/out.php" target="_blank"><img class="center cover" src="https://picpig.org/images/2018/05/01/69432535_57911.md.jpg" alt="Jules Jordan &#8211; August Taylor" border="0" width="450" /></a>
# <br>
# Jules Jordan &#8211; August Taylor
# <br>
# August Taylor Big Tit Slut Gets A Double Dicking With Deep Penetration Released: April 29, 2018 Voluptuous vixen August Taylor gets double teamed by Jules &#038; Chris! August is looking super fine in her black lingerie with metal chains holding it together, thigh high heels, and a choker with a padlock on it. She runs her hands across her body as she shows off for the camera, pulling out, then putting back her huge tits in the process. We follow August as she wanders around the house, stretching and posing with what appears to be a butt plug already in her asshole. She makes her way downstairs where she finds Jules &#038; Chris waiting for her on the couch and sprawls herself across them to give them unlimited access to her entire body. Jules removes the butt plug and gives it to August who happily sucks and licks it clean before she pulls out both their cocks and starts servicing them. She gags herself on both those big dicks until they can&#8217;t take it anymore and Jules starts pounding her pretty pussy. Jules &#038; Chris switch off between her mouth and pussy, but this whore says she wants it in [&#8230;]
# <br><br>
# <em><strong>Size:</strong> 321.84 MB / <strong>Duration:</strong> 39:33 / <strong>Screen:</strong> <a href="https://picpig.org/image/EO5h0" target="_blank">SHOW</a></em>
# <br><div class="su-spoiler su-spoiler-style-simple su-spoiler-icon-plus su-spoiler-closed"><div onclick="ddl_redirect();return false;"class="su-spoiler-title"><span class="su-spoiler-icon"></span>STREAM & DOWNLOAD</div><div class="su-spoiler-content su-clearfix" style="display:none">
# <blockquote>    <a href='http://streamcloud.eu/cs6xyi83l0i8/JulesJordan.18.04.29.August.Taylor.XXX.SD.MP4-KLEENEX.mp4.html' target='_blank'><img src='/player.jpg'/></a>
#
#     <br>    <br><br>    <img src='/uldllinks.png'/>
#     <br>
#     <pre><a href='http://ul.to/2oxhnqso' target='_blank'>http://ul.to/2oxhnqso</a></pre>
#
#     <br><br>    <img src='/sodllinks.png'/>
#     <br>
#     <pre><a href='http://www.share-online.biz/dl/4X2G228P3Z' target='_blank'>http://www.share-online.biz/dl/4X2G228P3Z</a></pre>
#
#     <br><br>    <img src='/rgdllinks.png'/>
#     <br>
#     <pre><a href='https://rapidgator.net/file/f3ee65ed8104c5d0510f0462f80dbe0d/jules_jordan_august_taylor.rar' target='_blank'>https://rapidgator.net/file/f3ee65ed8104c5d0510f0462f80dbe0d/jules_jordan_august_taylor.rar</a></pre>
#
#     <br><br>    <img src='/cryptdllinks.png'/>
#     <br>
#     <pre><img src='https://tolink.to/f/fo5ae887fbbdcaa/s' width='16' height='16' title='Ordner Status' /> <a href='https://tolink.to/f/fo5ae887fbbdcaa' target='_blank'>https://tolink.to/f/fo5ae887fbbdcaa</a></pre>
# </blockquote>
# </div></div>
#
# </article>



    patron  = '<div class="uk-article-title">.*?title="([^<]+)".*?<img class="center cover" src="([^<]+)" alt.*?<strong>Duration:</strong>(.*?) / <strong>Screen:</strong>.*?<blockquote>.*?<a href=\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedtitle,scrapedthumbnail,scrapedtime,scrapedurl in matches:
        scrapedplot = ""
        scrapedtitle = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
#        scrapedurl = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# <ul class="uk-pagination">
# <li class="uk-active"><span>1</span></li><li><a href="http://pornboss.org/category/movies/page/2/">2</a></li><li><a href="http://pornboss.org/category/movies/page/3/">3</a></li><li><a href="http://pornboss.org/category/movies/page/4/">4</a></li><li><span>...</span></li>
# <li><a href="http://pornboss.org/category/movies/page/143/">143</a></li>
# <li><a href="http://pornboss.org/category/movies/page/2/"><i class="uk-icon-angle-double-right"></i></a></li></ul>

#

    next_page_url = scrapertools.find_single_match(data,'<li><a href="([^"]+)"><i class="uk-icon-angle-double-right"></i>')
#    next_page_url = "http://www.elreyx.com/"+str(next_page_url)

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist
'''
def findvideos(item):
    logger.info("pelisalacarta.pornboss findvideos")
    itemlist = []
    data = scrapertools.cachePage(item.url)



    patron  = 'class="btn btn-primary btn-block qtips btn-hoster"(.*?)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist
'''
def play(item):
    logger.info()
#    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videochannel=item.channel
    return itemlist
