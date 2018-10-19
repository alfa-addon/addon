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

## italiafilm                                             \'([^\']+)\'


host = 'http://streamxxx.tv'


def mainlist(item):
    logger.info()
    itemlist = []


    itemlist.append( Item(channel=item.channel, title="MOVIES" , action="peliculas", url=host + "/category/movies-xxx/"))
    itemlist.append( Item(channel=item.channel, title="      Italianas" , action="peliculas", url=host + "/category/film-porno-italian/"))
    itemlist.append( Item(channel=item.channel, title="      Internacional" , action="peliculas", url=host + "/category/international-movies/"))

    itemlist.append( Item(channel=item.channel, title="CLIPS" , action="peliculas", url=host + "/category/clips/"))
    itemlist.append( Item(channel=item.channel, title="      Canal" , action="catalogo", url=host))
    itemlist.append( Item(channel=item.channel, title="      Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s&cat=" % texto

    try:
        return peliculas(item)

#        return sub_search(item, texto.replace("+", " "))
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []




def catalogo(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<li id="menu-item-569330"(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


# <li id="menu-item-534894" class="menu-item menu-item-type-taxonomy menu-item-object-category current-menu-item menu-item-has-children menu-item-534894"><a href="http://streamxxx.tv/category/clips/" class="st-is-cat st-term-5562">VIDEOS <span class="fa fa-caret-down st-dropdown-arrow-down"></span></a>
# <ul class="sub-menu">
# 	<li id="menu-item-587378" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-587378"><a href="http://streamxxx.tv/category/clips/hd-clips/" class="st-is-cat st-term-19">HD Clips</a></li>
# 	<li id="menu-item-587379" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-587379"><a href="http://streamxxx.tv/category/clips/full-hd-clips/" class="st-is-cat st-term-21385">FULL-HD Clips</a></li>
# 	<li id="menu-item-587380" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-587380"><a href="http://streamxxx.tv/category/clips/4k-clips/" class="st-is-cat st-term-21413">4K Clips</a></li>
# 	<li id="menu-item-534895" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-534895"><a href="http://streamxxx.tv/category/clips/italian-clips/" class="st-is-cat st-term-232">Italian clips</a></li>
# 	<li id="menu-item-569330" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-569330"><a href="/tag/brazzers/">Brazzers</a></li>
# 	<li id="menu-item-569331" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-569331"><a href="/tag/reality-kings/">Reality Kings</a></li>
# 	<li id="menu-item-569332" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-569332"><a href="/tag/naughty-america/">Naughty America</a></li>
# 	<li id="menu-item-569334" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-569334"><a href="/tag/bangbros/">BangBros</a></li>
# 	<li id="menu-item-569335" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-569335"><a href="/tag/mofos/">Mofos</a></li>
# 	<li id="menu-item-587381" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587381"><a href="/tag/team-skeet/">Team Skeet</a></li>
# 	<li id="menu-item-587386" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587386"><a href="/?s=fakehub">Fakehub</a></li>
# 	<li id="menu-item-587382" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587382"><a href="/tag/pornpros/">Porn Pros</a></li>
# 	<li id="menu-item-587388" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587388"><a href="/?s=21sextury">21sextury</a></li>
# 	<li id="menu-item-587387" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587387"><a href="/?s=porndoe">Porndoe</a></li>
# 	<li id="menu-item-587383" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587383"><a href="/tag/girls-do-porn/">Girls Do Porn</a></li>
# 	<li id="menu-item-587384" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587384"><a href="/?s=nubiles">Nubiles</a></li>
# 	<li id="menu-item-587389" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587389"><a href="/?s=sexyhub">Sexyhub</a></li>
# 	<li id="menu-item-587390" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587390"><a href="/?s=dogfart">Dogfart</a></li>
# 	<li id="menu-item-587391" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587391"><a href="/?s=babes">Babes</a></li>
# 	<li id="menu-item-587392" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587392"><a href="/?s=teen+mega+world">Teen Mega World</a></li>
# 	<li id="menu-item-587394" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587394"><a href="/tag/mom-pov/">Mom-pov</a></li>
# 	<li id="menu-item-587393" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587393"><a href="/?s=dorcel">Dorcel</a></li>
# 	<li id="menu-item-587385" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587385"><a href="/?s=tushy">Tushy</a></li>
# 	<li id="menu-item-587395" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-587395"><a href="/?s=Xtime">Xtime</a></li>
# </ul>
# </li>

    patron  = '<a href="([^"]+)">([^"]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
#    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<a href="/top-tags/%20">TOP TAGS(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <li id="menu-item-540680" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-has-children menu-item-540680"><a href="/top-tags/%20">TOP TAGS <span class="fa fa-caret-down st-dropdown-arrow-down"></span></a>
# <ul class="sub-menu">
# 	<li id="menu-item-540681" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540681"><a href="/tag/anal/">ANAL</a></li>
# 	<li id="menu-item-540682" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540682"><a href="/tag/big-butts/">BIG ASS</a></li>
# 	<li id="menu-item-540683" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540683"><a href="/tag/big-dicks/">BIG DICKS</a></li>
# 	<li id="menu-item-540684" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540684"><a href="/tag/big-tits/">BUSTY</a></li>
# 	<li id="menu-item-540685" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540685"><a href="/tag/double-penetration/">DP</a></li>
# 	<li id="menu-item-540686" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540686"><a href="/tag/feet/">FEETS</a></li>
# 	<li id="menu-item-540687" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540687"><a href="/tag/fetish/">FETISH</a></li>
# 	<li id="menu-item-540688" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540688"><a href="/tag/handjobs/">HANDJOBS</a></li>
# 	<li id="menu-item-540689" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540689"><a href="/tag/lesbian/">LESBIAN</a></li>
# 	<li id="menu-item-540690" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540690"><a href="/tag/milf-cougar/">MILFS</a></li>
# 	<li id="menu-item-540691" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540691"><a href="/tag/oral/">ORAL</a></li>
# 	<li id="menu-item-540692" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540692"><a href="/tag/p-o-v-point-of-view/">P.O.V.</a></li>
# 	<li id="menu-item-540693" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540693"><a href="/tag/legal-teen/">TEENS</a></li>
# 	<li id="menu-item-540694" class="menu-item menu-item-type-custom menu-item-object-custom menu-item-540694"><a href="/tag/threesomes-more/">THREESOMES</a></li>
# </ul>
# </li>


    patron  = '<a href="([^"]+)">([^"]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""

        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


    patron  = '<article id="post-\d+".*?<a href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

#                "Next page >>"                       <li><a class="next page-numbers" href="http://streamxxx.tv/tag/big-tits/page/2/">Next</a></li>
    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next</a>')

    itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

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
