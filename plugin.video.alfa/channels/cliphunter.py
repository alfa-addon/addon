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
from core import jsontools

## italiafilm                                             \'([^\']+)\'

host = 'https://www.cliphunter.com'

def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/categories/All"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular/ratings/yesterday"))
#    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top-rated/"))


    itemlist.append( Item(channel=item.channel, title="Pornstars" , action="catalogo", url=host + "/pornstars/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto

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
#    data = scrapertools.get_match(data,'<div class="paper paperSpacings xs-fullscreen photoGrid">(.*?)<div id="GenericModal" class="modal chModal">')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <a href="/pornstars/Ella+Knox">
# 		<img src='https://y1.pichunter.com/3633179_12_t.jpg'/>
# 	        <div class="caption"><span>Ella Knox</span></div>
# </a>

    patron  = '<a href="([^"]+)">\s*<img src=\'([^\']+)\'/>.*?<span>([^"]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""

#        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "/movies"

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )



    return itemlist

def categorias(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<div class="category-item">(.*?)<div id="goupBlock"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

# <a href="/categories/All" title="All">
#                 <img src="http://p4a.gexo.com/30254/3025421_15.jpg"/>
#                 <div class="caption"><span>All</span></div>
#             </a>


    patron  = '<a href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)"/>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
#    data = scrapertools.get_match(data,'<div class="mov-container1">(.*?)<div class="clearfix">')


# <li itemscope itemtype="http://schema.org/Movie" mId="3038912" class=" long">
#             <a class="t" href="/w/3038912/Jenny_Baby_gets_plowed_in_hardcore_fashion" >
#                 <img class="i" src="https://p4a.gexo.com/30272/3027214_15.jpg" tc="30" vdur="1092"/>
#                 <div class="tr">18:12</div>
#                 <div class="sharpCorner"><div class="tl adjusted">HD</div></div>            </a>
#             <span class="al_v mdi-image-photo-camera visible-xxs"></span>
#                                     <a href="/w/3038912/Jenny_Baby_gets_plowed_in_hardcore_fashion" class="vttl long">Jenny Baby gets plowed in hardcore fashion</a>
#
#             <div class="info long">
#                 Porn quality: ? %
#             </div>
#                     </li>



    patron  = '<img class=".*?" src="([^"]+)".*?<div class="tr">(.*?)</div>.*?<a href="([^"]+)\s*" class="vttl.*?">(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail,scrapedtime,scrapedurl,scrapedtitle  in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
#        year = " (%s)" % year
#        title = scrapedtitle
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail, plot=plot, contentTitle = title, infoLabels={'year':year} ))


#			"Next page >>"		<li class="arrow"><a rel="next" href="/categories/All/2">&raquo;</a></li>


    next_page_url = scrapertools.find_single_match(data,'<li class="arrow"><a rel="next" href="([^"]+)">&raquo;</a>')

    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title=next_page_url , text_color="blue", url=next_page_url , folder=True) )


    # else:
    #         patron  = '<a href="([^"]+)" title="Next Page"'
    #         next_page = re.compile(patron,re.DOTALL).findall(data)
    #         next_page = item.url + next_page[0]
    #         itemlist.append( Item(channel=item.channel, action="peliculas", title="Next page >>" , text_color="blue", url=next_page ) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#  \'([^\']+)/\'    <meta itemprop="contentUrl" content="https://cdn-fck.tnaflix.com/tnamp4/922fec57511179b06c2f/Brazzers_Big_Tits_at_Work_Eva_Angelina_Ramon_Camera_Cums_In_Handy.mp4?key=c62fd67fe0ada667127298bcb9e40371?secure=EQdpT0ExwdSiP6btIwawQg==,1511524930" />

# {"3016249_p360.mp4":{"fmt":"mp4","h":360,"w":640,"br":764,"flash":1,"url":"aqqvr$==cil2b&cyzvaplqdx&cfn=nfb=30162=3016249_v360&nv4?xz(1097460^xr(1680^qqy(1512041918^amra(1d991m4gb9d022835005c11mb0m07695"},
# "3016249_p540.mp4":{"fmt":"mp4","h":540,"w":960,"br":1241,"flash":1,"url":"aqqvr$==cil2b&cyzvaplqdx&cfn=nfb=30162=3016249_v540&nv4?xz(1782655^xr(2730^qqy(1512041918^amra(g869c7m6ci399d8gdii4b3i8793bid3c"},
# "3016249_p720.mp4":{"fmt":"mp4","h":720,"w":1280,"br":1241,"flash":1,"url":"aqqvr$==cil2b&cyzvaplqdx&cfn=nfb=30162=3016249_v720&nv4?xz(1782655^xr(2730^qqy(1512041918^amra(36dc1bmc8g698d943749157dc733i74b"}};
#                                                                             a b c d e f g h i j k l m n o p q r s t u v w y x z $ = & ? ( ^
#                                                                             h     e   o f   d     n a m   u t s       p   l r i : / . ? = &
#                                                                                           cyzvaplqdx
#                                                                             https://cdn2b.cliphunter.com/mob/30162/3016249_p720.mp4?ri=1782655&rs=2730&ttl=1512041918&hash=36ec1bac8f698e943749157ec733d74b
#                                                                             https://cdn2b.cliphunter.com/mob/30162/3016249_p360.mp4?ri=1097460&rs=1680&ttl=1512041918&hash=1e991a4fb9e022835005c11ab0a07695


    patron  = '"url"\:"(.*?)"'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("=", "/")
        title = scrapedurl
        scrapedurl = replace_all(scrapedurl, rep1)
        scrapedurl = replace_all(scrapedurl, rep2)
        scrapedurl = replace_all(scrapedurl, rep3)

    itemlist.append(Item(channel=item.channel, action="play", title=item.title, fulltitle=item.fulltitle, url=scrapedurl,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))
#    itemlist.append(item.clone(action="play", title=title, fulltitle = item.title, url=scrapedurl))

    return itemlist

#                                   a b c d e f g h i j k l m n o p q r s t u v w y x z $ = & ? ( ^
#                                   h     e   o f   d     n a m   u t s       p   l r i : / . ? = &

rep1 = {'a':'h', 'm':'a', 'n':'m', 'd':'e', 'f':'o', 'i':'d', 'p':'u', 'q':'t',
        'r':'s','v':'p', 'x':'r', 'z':'i', '$':':', '&':'.', '(':'=', '^':'&'}
rep2 = {'g':'f', 'l':'n'}
rep3 = {'y':'l'}

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text
