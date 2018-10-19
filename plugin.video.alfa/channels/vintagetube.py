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



    patron  = '<h2 class="s">(.*?)</ul>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
#       url = scrapertools.find_single_match(match,'video_url: \'([^\']+)\'')
        url = scrapertools.find_single_match(match,'data-id="(.*?)"')
        url = "http://www.pornhive.tv/en/out/" + str(url)

        itemlist.append(item.clone(action="play", title=url, url=url))

    return itemlist

'''


host = 'http://www.vintagetube.club'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Ultimos" , action="peliculas", url=host + "/tube/last-1/"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/tube/popular-1/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))

    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")

#               http://www.vintagetube.club/search/boobs/popular-1/
    item.url = "http://www.vintagetube.club/search/%s" % texto
    item.url =     item.url + "/popular-1/"

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
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="flli clfl listcat">(.*?)</ul>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


                        # <div class="prev prev-ct">
                        #     <a href="/tags/forced/popular-1/">
                        #         <img src="http://vintagetube.club/content/15/640_Flogging_Flogging.jpg" />
                        #         <span class="prev-tit">forced</span>
                        #     </a>
                        # </div>

    patron  = '<div class="prev prev-ct">.*?<a href="(.*?)">.*?<img src="(.*?)".*?<span class="prev-tit">(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
        scrapedtitle = str(scrapedtitle)
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
#    data = scrapertools.get_match(data,'<ul class="fotos-detail clfl">(.*?)</ul>')

# div class="prev">
#     <a href="/xxx.php?tube=/videos/aja-renee-morgan-in-old-school-porn-star-bonks-sweetheart/">
#         <img src="http://cdn.vintagetube.club/content/29/548_old_a.jpg">
#         <span class="prev-tit">Aja, Renee Morgan in old school porn star bonks a sweetheart with strap-on</span>
#     </a>
#     <div class="prev-views">Views: <span>11769</span></div>
#     <div class="prev-dur"><span>6:46</span></div>
# </div>

    patron = '<div class="prev">.*?<a href="(.*?)">.*?<img src="(.*?)">.*?<span class="prev-tit">(.*?)</span>.*?<div class="prev-dur"><span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        scrapedplot = ""
#        scrapedthumbnail = "https:" + scrapedthumbnail
#        scrapedtitle = scrapedtitle.replace("Ver Pel\ícula", "")
        scrapedtitle = "[COLOR yellow]" + (scrapedtime) + "[/COLOR] " + str(scrapedtitle)
#        scrapedthumbnail = scrapedthumbnail.replace("/uploads", "http://qwertty.net/uploads")
        scrapedurl = scrapedurl.replace("/xxx.php?tube=", "")
        scrapedurl = host + scrapedurl
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedurl , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

# "Next page >>"        #<li><span class="page">2</span></li>

    current_page = scrapertools.find_single_match(data,'<li><span class="page">(.*?)</span></li>')
    next_page = int(current_page) + 1
    url = item.url
    url_page = current_page + "/"
    url = url.replace(url_page, "")
    next_page_url = url + str(next_page)+"/"
    itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data

#  <iframe frameborder=0 scrolling="no"  src='https://www.playercdn.com/ec/embed.php?b64=PGlmcmFtZSBzcmM9Ii8vd3d3LnBsYXllcmNkbi5jb20vZWMvaTIucGhwP3VybD1hSFIwY0RvdkwzZDNkeTU0ZG1sa1pXOXpMbU52YlM5MmFXUmxiekV4TmpFMk56YzFMMkZxWVY5eVpXNWxaVjl0YjNKbllXNWZhVzVmYjJ4a1gzTmphRzl2YkY5d2IzSnVYM04wWVhKZlpuVmphM05mWVY5amFHbGphMTkzYVhSb1gzTjBjbUZ3TFc5dSIgc2Nyb2xsaW5nPSJubyIgbWFyZ2lud2lkdGg9IjAiIG1hcmdpbmhlaWdodD0iMCIgZnJhbWVib3JkZXI9IjAiIGFsbG93ZnVsbHNjcmVlbj48L2lmcmFtZT4.'></iframe>

    scrapedurl = scrapertools.find_single_match(data,'<iframe frameborder=0 scrolling="no"  src=\'(.*?)\'')

    if scrapedurl == "":
        scrapedurl=item.url

# <iframe src="http://www.playercdn.com/ec/i2.php?url=aHR0cDovL3d3dy54dmlkZW9zLmNvbS92aWRlbzE4NDI1OTUzL2dlcm1hbl9zdGVwLWRhZF9jYXVnaHRfbm90X2hpc19kYXVnaHRlcl9tYXN0dXJiYXRpb24uLi5fLV9hYnVzZXJwb3JuLmNvbQ==" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" allowfullscreen></iframe>
    data = httptools.downloadpage(scrapedurl).data
    scrapedurl = scrapertools.find_single_match(data,'<iframe src="(.*?)"')

# <source src="http://vid3-l3.xvideos-cdn.com/videos/mp4/a/4/e/xvideos.com_a4e83a1ae0511c100ea8949f58cbae0d.mp4?e=1512157446&ri=1024&rs=85&h=5ff2ad292d8368044e9496ff5af12a01" type='video/mp4'>

    data = httptools.downloadpage(scrapedurl).data
    media_url = scrapertools.find_single_match(data,'<source src="(.*?)"')



    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title=media_url, fulltitle=media_url, url=media_url,
                         thumbnail=item.thumbnail, plot=item.plot, show=item.title, server="directo", folder=False))

    return itemlist

    # itemlist.append(item.clone(channel=item.channel, action="play", title=scrapedurl, url=scrapedurl , plot="" , folder=True) )
    # return itemlist


'''
def play(item):
    logger.info("pelisalacarta.vintagetube play")
    data = scrapertools.cachePage(item.url)
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.title
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist
'''
