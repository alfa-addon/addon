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

def mainlist(item):
    logger.info()
    itemlist = []


    if item.url=="":
        item.url = "http://www.peliculasdk.com/genero/adultos"

    data = scrapertools.cachePage(item.url)


# <div class="cont_peliculas">
# <div class="peliculas_box" style="position:relative"> <a href="http://www.peliculasdk.com/private-specials-206-cuckold-and-proud-of-it/"><img src="http://peliculasdk.net/images/15315798611974283h.jpg" alt="Private Specials 206: Cuckold And Proud Of It"></a><br>
# <div class="titulope">Private Specials 206: Cuckold And Proud Of It</div>
# <div class="info">
# <div style="color:#f90375">Audio: </div>
# <div style="color:#c7d301">Calidad: </div>
# <div style="color:#8691e0">Género: <a href="http://www.peliculasdk.com/genero/adultos/" rel="category tag">Adultos</a></div>
# <div class="imdb">IMDb </div>
# </div>
# </div></div>



    patron  = '<div class="cont_peliculas">.*?<a href="([^<]+)"><img src="(.*?)" alt="([^<]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        #  dat = scrapertools.cachePage(str(scrapedurl))
        #  patron  = 'class="tab_content"><script>(.*?)</div>'
        #  matche = re.compile(patron,re.DOTALL).findall(dat)
         #
        #  for match in matche:
        #      url = scrapertools.find_single_match(match,'open([^<]+)</script>')
        #      url = url.replace("(","").replace(")","").replace("\"","")
        #      url = "https://openload.co/embed/" + url +"/"

        itemlist.append( Item(channel=item.channel, action="deo", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# <div class="paginacion"><div class="pagenavi">
# <span class="current">1</span><a href="http://www.peliculasdk.com/genero/adultos/page/2" class="single_page" title="2">2</a><a href="http://www.peliculasdk.com/genero/adultos/page/3" class="single_page" title="3">3</a><a href="http://www.peliculasdk.com/genero/adultos/page/4" class="single_page" title="4">4</a><a href="http://www.peliculasdk.com/genero/adultos/page/5" class="single_page" title="5">5</a><a href="http://www.peliculasdk.com/genero/adultos/page/6" class="single_page" title="6">6</a><span class="expand">...</span><a href="http://www.peliculasdk.com/genero/adultos/page/107" class="last" title="Ultima">107</a>
# <a href="http://www.peliculasdk.com/genero/adultos/page/2">Siguiente &raquo;</a></div>
# </div>

#  "Next Page >>"
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)">Siguiente &raquo;</a>')
#    next_page_url = "http://sexody.com" + next_page_url
    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="mainlist" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

    return itemlist

def deo(item):
    logger.info()

    itemlist = []
    data = scrapertools.cache_page(item.url)
    data = re.sub(r"<!--.*?-->", "", data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

# <div id="verpelicula">
# <div id="titutab">Ver película Harlow Harrison&#8217;s Whore Dreams (<a href="http://www.peliculasdk.com/idioma/ingles" rel="tag">Inglés</a>)</div>
# <ul class="tabs">
# <li><a href="#tab1"><span class="re">1</span><span class="in"></span><span class="c">Opción 1</span></a></li>
# </ul>
# <div class="tab_container">
# <div id="tab1" class="tab_content"><script>mango("qqmnktnttfmqotpl")</script></div>
# </div>
# </div>
# <center><script type="text/javascript">
# var ad_idzone = "1842312",
# ad_width = "468",
# ad_height = "60";
# </script>


    bloque_tab = scrapertools.find_single_match(data, '<div id="verpelicula">(.*?)<div class="tab_container">')
    patron = '<li><a href="#([^<]+)"><span class="re">\d<\/span><span class="([^<]+)"><\/span><span class=.*?>([^<]+)<\/span>'
    check = re.compile(patron, re.DOTALL).findall(bloque_tab)

    servers_data_list = []

    patron = '<div id="(tab\d+)" class="tab_content"><script type="text/rocketscript">(\w+)\("([^"]+)"\)</script></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if len(matches) == 0:
        patron = '<div id="(tab\d+)" class="tab_content"><script>(\w+)\("([^"]+)"\)</script></div>'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for check_tab, server, id in matches:
#        scrapedplot = scrapertools.get_match(data, '<span class="clms">(.*?)</div></div>')
        # plotformat = re.compile('(.*?:) </span>', re.DOTALL).findall(scrapedplot)
        # scrapedplot = scrapedplot.replace(scrapedplot, bbcode_kodi2html("[COLOR white]" + scrapedplot + "[/COLOR]"))
        #
        # for plot in plotformat:
        #     scrapedplot = scrapedplot.replace(plot, bbcode_kodi2html("[COLOR red][B]" + plot + "[/B][/COLOR]"))
        # scrapedplot = scrapedplot.replace("</span>", "[CR]")
        # scrapedplot = scrapedplot.replace(":", "")
        scrapedplot = ""
        if check_tab in str(check):
            idioma, calidad = scrapertools.find_single_match(str(check), "" + check_tab + "', '(.*?)', '(.*?)'")

            servers_data_list.append([server, id, idioma, calidad])

    url = "http://www.peliculasdk.com/Js/videod.js"
    data = scrapertools.cachePage(url)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = data.replace('<iframe width="100%" height="400" scrolling="no" frameborder="0"', '')

    patron = 'function (\w+)\(id\).*?'
    patron += 'data-src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for server, url in matches:

        for enlace, id, idioma, calidad in servers_data_list:

            if server == enlace:

                video_url = re.sub(r"embed\-|\-.*?x.*?\.html|u\'|\'\(", "", str(url))
                video_url = re.sub(r"'\+codigo\+'", "", video_url)
                video_url = video_url.replace('embed//', 'embed/')
                video_url = video_url + id
                if "goo.gl" in video_url:
                    try:
                        from unshortenit import unshorten
                        url = unshorten(video_url)
                        video_url = scrapertools.get_match(str(url), "u'([^']+)'")
                    except:
                        continue

                servertitle = scrapertools.get_match(video_url, 'http.*?://(.*?)/')
                servertitle = servertitle.replace("embed.", "")
                servertitle = servertitle.replace("player.", "")
                servertitle = servertitle.replace("api.video.", "")
                servertitle = re.sub(r"hqq.tv|hqq.watch", "netutv", servertitle)
                servertitle = servertitle.replace("anonymouse.org", "netu")
                title = servertitle
                logger.debug('servertitle: %s' % servertitle)
                server = servertools.get_server_name(servertitle)
                logger.debug('server: %s'%server)
                itemlist.append(
                    Item(channel=item.channel, title=title, url=video_url, action="play",
                         thumbnail=item.category,
                         plot=scrapedplot, fanart=item.show, server=server, language=idioma, quality=calidad))
    # if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
    #     infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
    #                   'title': item.fulltitle}
    #     itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
    #                          action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
    #                          text_color="0xFFff6666",
    #                          thumbnail='http://imgur.com/0gyYvuC.png'))

    return itemlist


def play(item):
    logger.info()

    itemlist = servertools.find_video_items(data=item.url)
    data = scrapertools.cache_page(item.url)

    listavideos = servertools.findvideos(data)

    for video in listavideos:
        videotitle = scrapertools.unescape(video[0])
        url = item.url
        server = video[2]

        # xbmctools.addnewvideo( item.channel , "play" , category , server ,  , url , thumbnail , plot )
        itemlist.append(
            Item(channel=item.channel, action="play", server=server, title="Trailer - " + videotitle, url=url,
                 thumbnail=item.thumbnail, plot=item.plot, fulltitle=item.title,
                 fanart="http://s23.postimg.org/84vkeq863/movietrailers.jpg", folder=False))

    return itemlist


# Verificación automática de canales: Esta función debe devolver "True" si está ok el canal.
def test():
    from servers import servertools
    # mainlist
    mainlist_items = mainlist(Item())
    # Da por bueno el canal si alguno de los vídeos de "Novedades" devuelve mirrors
    peliculas_items = peliculas(mainlist_items[0])
    bien = False
    for pelicula_item in peliculas_items:
        mirrors = servertools.find_video_items( item=pelicula_item )
        if len(mirrors)>0:
            bien = True
            break

    return bien
