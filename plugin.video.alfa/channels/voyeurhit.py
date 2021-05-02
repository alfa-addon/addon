# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from core import jsontools as json

host = 'https://voyeurhit.com'    # https://voyeurhit.com  https://hdzog.com  https://txxx.com 
url_api = host + "/api/json/videos/%s/str/%s/60/%s.%s.1.all..%s.json"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Ultimas" , action="lista", url=url_api % ("14400", "latest-updates", "", "", "")))
    itemlist.append(item.clone(title="Mejor valoradas" , action="lista", url=url_api % ("14400", "top-rated", "", "", "month")))
    itemlist.append(item.clone(title="Mas popular" , action="lista", url=url_api % ("14400", "most-popular", "", "", "month")))
    # itemlist.append(item.clone(title="Mas vistos" , action="lista",  url=url_api % ("14400", "most-viewed", "", "", "month") ))
    itemlist.append(item.clone(title="Mas comentado" , action="lista",  url=url_api % ("14400", "most-commented", "", "", "month") ))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/api/json/categories/14400/str.all.json"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "%s/api/videos.php?params=259200/str/relevance/60/search..1.all..&s=%s&sort=latest-updates&date=all&type=all&duration=all" % (host,texto)
    
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    headers = {'Referer': "%s" % host}
    data = httptools.downloadpage(item.url, headers=headers).data
    JSONData = json.load(data)
    for cat in  JSONData["categories"]:
        scrapedtitle = cat["title"]
        dir = cat["dir"]
        num = cat["total_videos"]
        url = url_api % ("14400", "latest-updates", "categories", dir, "day")
        thumbnail = ""
        scrapedplot = ""
        title = "%s (%s)" %(scrapedtitle,num)
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail, plot=scrapedplot) )
    return  sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    headers = {'Referer': "%s" % host}
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["videos"]:
        video_id = Video["video_id"]
        dir = Video["dir"]
        scrapedtitle = Video["title"]
        duration = Video["duration"]
        scrapedthumbnail =  Video["scr"]
        scrapedhd =  Video["props"]
        scrapedurl = "%s/embed/%s" %(host,video_id)
        if scrapedhd:
            title = "[COLOR yellow]%s[/COLOR] [COLOR tomato]HD[/COLOR] %s" % (duration, scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (duration, scrapedtitle)
        thumbnail = scrapedthumbnail.replace("\/", "/")
        plot = ""
        itemlist.append(item.clone(action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, 
                        fanart=thumbnail, plot=plot, contentTitle=title) )
    total= int(JSONData["total_count"])
    page = int(scrapertools.find_single_match(item.url,'(\d+).all..'))
    url_page = scrapertools.find_single_match(item.url,'(.*?).\d+.all..')
    post = scrapertools.find_single_match(item.url,'all..(.*)')
    next_page = (page+ 1)
    if (page*60) < total:
        next_page = "%s.%s.all..%s" %(url_page,next_page,post)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


