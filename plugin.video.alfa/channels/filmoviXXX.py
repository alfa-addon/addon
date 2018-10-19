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
from core import jsontools

## italiafilm                                             \'([^\']+)\'



def mainlist(item):
    logger.info()
    itemlist = []

    if item.url=="":
        item.url = "http://www.filmovix.net/videoscategory/porno/"

#    data = scrapertools.cachePage(item.url)
    data = httptools.downloadpage(item.url).data
    data = scrapertools.get_match(data,'<h1 class="cat_head">XXX</h1>(.*?)<h3> Novo dodato </h3>')
#    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)


        	# <li class="clearfix">
            #
            #                  <a class="video_thumb" href="http://www.filmovix.net/videos/eves-gift-2001-18/" rel="bookmark" title="Eve&#8217;s Gift (2001) (18+)">
            #  			 <img width="123" height="150" src="http://www.filmovix.net/wp-content/uploads/2016/10/918e7063dfa3e518a7f625cb0b753849-123x150.jpg" class=" wp-post-image" alt="" />
            #
            #
            #  </a>
            #
            #
            #      <p class="title"><a href="http://www.filmovix.net/videos/eves-gift-2001-18/" rel="bookmark" title="Eve&#8217;s Gift (2001) (18+)">Eve&#8217;s Gift (2001) (18+)</a></p>
            #
            #      <!--<p class="author">  by </p>
            #      <p></p>-->
            #
            # 	 </li>


    patron  = '<li class="clearfix">.*?src="([^"]+)".*?<p class="title"><a href="([^"]+)" rel="bookmark" title="([^"]+)">'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedthumbnail,scrapedurl,scrapedtitle in matches:
#        url = urlparse.urljoin(item.url,scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle
#        title = "[COLOR yellow]" + time + "  [/COLOR]" + scrapedtitle
#        title = scrapedtitle + " (" + scrapedyear + ") " + " " + calidad + " "
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, infoLabels={'year':year} ))


#        <a class="nextpostslink" rel="next" href="http://www.filmovix.net/videoscategory/porno/page/2/">
# "Next page >>"

    else:
        patron  = '<a class="nextpostslink" rel="next" href="([^"]+)">'
        next_page = re.compile(patron,re.DOTALL).findall(data)
        itemlist.append( Item(channel=item.channel, action="mainlist", title="Next page >>" , text_color="blue", url=next_page[0] ) )
    return itemlist
