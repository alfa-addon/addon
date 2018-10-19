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

host = 'http://www.sluttyhd.com'



def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Peliculas" , action="peliculas", url=host + "/fullpornmovies/"))
#    itemlist.append( Item(channel=item.channel, title="TOP" , action="peliculas", url="http://tubepornclassic.com/top-rated/"))
#    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url="http://tubepornclassic.com/most-popular/"))
    itemlist.append( Item(channel=item.channel, title="Videos" , action="peliculas", url=host))

    itemlist.append( Item(channel=item.channel, title="Big Tits" , action="peliculas", url=host + "/?s=big+tits"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    item.url = item.url + "&submit=Search"

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


    patron  = '<li id="menu-item-\d+.*?><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

# <div class="post-column clearfix">
# <article id="post-17519" class="post-17519 post type-post status-publish format-standard has-post-thumbnail hentry category-fullpornmovies tag-cherie-deville tag-isiah-maxwell tag-rachael-madori tag-sara-luvv tag-tyler-knight tag-tyler-nixon">
# <a href="http://www.sluttyhd.com/interracial-family-needs-full-movie-2017/" rel="bookmark">
# <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" style="background:url('http://www.hdx.to/pics/Interracial_Family_Needs_Full_Movie_2017.jpg') no-repeat center center;-webkit-background-size:cover;-moz-background-size:cover;-o-background-size:cover;background-size:cover;width:400px;height:210px;" class="attachment-post-thumbnail  wp-post-image nelioefi" alt=""/>
# </a>
# <header class="entry-header">
# <h2 class="entry-title"><a href="http://www.sluttyhd.com/interracial-family-needs-full-movie-2017/" rel="bookmark">Interracial Family Needs &#8211; Full Movie (2017)</a></h2>
# <div class="entry-meta"><span class="meta-date"><a href="http://www.sluttyhd.com/interracial-family-needs-full-movie-2017/" title="12:10" rel="bookmark"><time class="entry-date published updated" datetime="2017-05-09T12:10:02+00:00">9. May 2017</time></a></span><span class="meta-author"> <span class="author vcard"><a class="url fn n" href="" title="View all posts by " rel="author"></a></span></span><span class="meta-category"> <a href="http://www.sluttyhd.com/fullpornmovies/" rel="category tag">Movies</a></span><span class="meta-comments"> <a href="http://www.sluttyhd.com/interracial-family-needs-full-movie-2017/#respond">Leave a comment</a></span></div>
# </header>
# <div class="entry-content entry-excerpt clearfix">
# </div>
# <div class="read-more">
# <a href="http://www.sluttyhd.com/interracial-family-needs-full-movie-2017/" class="more-link">Watch &raquo;</a>
# </div>
# </article>
# </div>

    patron  = '<div class="post-column clearfix">.*?style="background:url\(\'(.*?)\'\).*?<a href="([^"]+)" rel="bookmark">([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
#        scrapedthumbnail = ""
#        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)

        itemlist.append( Item(channel=item.channel, action="findvideos", title=scrapedurl , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )


# <ul class="pagination pagination-centered wp-pagenavi-pagination">
# <li><span class='pages'>Page 1 of 771</span></li><li><span class='current'>1</span></li><li><a class="page larger" href="http://www.sluttyhd.com/page/2/">2</a></li><li><a class="page larger" href="http://www.sluttyhd.com/page/3/">3</a></li><li><a class="page larger" href="http://www.sluttyhd.com/page/4/">4</a></li><li><a class="page larger" href="http://www.sluttyhd.com/page/5/">5</a></li><li><span class='extend'>...</span></li><li><a class="larger page" href="http://www.sluttyhd.com/page/10/">10</a></li><li><a class="larger page" href="http://www.sluttyhd.com/page/20/">20</a></li><li><a class="larger page" href="http://www.sluttyhd.com/page/30/">30</a></li><li><span class='extend'>...</span></li>
# <li><a class="nextpostslink" rel="next" href="http://www.sluttyhd.com/page/2/">&raquo;</a></li>
# <li><a class="last" href="http://www.sluttyhd.com/page/771/">Last &raquo;</a></li>
# </ul>


    next_page_url = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">')
#    <a class="next page-numbers" href="http://www.sluttyhd.com/fullpornmovies/page/2/">

    if next_page_url!="":
#        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Next page >>" , text_color="blue", url=next_page_url , folder=True) )

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)

#<script type='text/javascript'> str='@3C@69@66@72@61@6D@65@20@73@72@63@3D@22@68@74@74@70@73@3A@2F@2F@6F@70@65@6E@6C@6F@61@64@2E@63@6F@2F@65@6D@62@65@64@2F@4D@52@4C@5F@56@4F@54@6B@50@62@41@2F@77@77@77@2E@73@6C@75@74@74@79@68@64@2E@63@6F@6D@5F@4D@65@6C@61@6E@69@65@5F@48@69@63@6B@73@5F@53@68@6F@77@69@6E@67@5F@6F@66@66@5F@68@65@72@5F@64@65@6C@69@63@69@6F@75@73@5F@62@69@67@5F@74@69@74@73@5F@2D@5F@4D@65@6C@61@6E@69@65@5F@48@69@63@6B@73@22@20@73@63@72@6F@6C@6C@69@6E@67@3D@22@6E@6F@22@20@66@72@61@6D@65@62@6F@72@64@65@72@3D@22@30@22@20@77@69@64@74@68@3D@22@37@30@30@22@20@68@65@69@67@68@74@3D@22@34@33@30@22@20@61@6C@6C@6F@77@66@75@6C@6C@73@63@72@65@65@6E@3D@22@74@72@75@65@22@20@77@65@62@6B@69@74@61@6C@6C@6F@77@66@75@6C@6C@73@63@72@65@65@6E@3D@22@74@72@75@65@22@20@6D@6F@7A@61@6C@6C@6F@77@66@75@6C@6C@73@63@72@65@65@6E@3D@22@74@72@75@65@22@3E@3C@2F@69@66@72@61@6D@65@3E'; document.write(unescape(str.replace(/@/g,'%'))); </script></p>


    variable = scrapertools.find_single_match(data,'<a class="<p><script type=\'text/javascript\'> str=(.*?);')
    resuelta = re.sub("@[A-F0-9][A-F0-9]", lambda m: m.group()[1:].decode('hex'), variable)

#<iframe src="https://openload.co/embed/MRL_VOTkPbA/www.sluttyhd.com_Melanie_Hicks_Showing_off_her_delicious_big_tits_-_Melanie_Hicks" scrolling="no" frameborder="0" width="700" height="430" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"></iframe>

    scrapedurl = scrapertools.find_single_match(variable,'<iframe src="([^"]+)"')
    scrapedplot = ""
    scrapedthumbnail = ""
    itemlist.append( Item(channel=item.channel, action="play", title=variable , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
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
