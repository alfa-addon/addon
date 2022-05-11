# -*- coding: utf-8 -*-
#------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from core import jsontools as json
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

#  https://hclips.com  https://hotmovs.com  https://hdzog.com  https://upornia.com  https://vjav.com  https://voyeurhit.com  https://txxx.com 
canonical = {
             'channel': 'hclips', 
             'host': config.get_setting("current_host", 'hclips', default=''), 
             'host_alt': ["https://hclips.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
url_api = "%s/api/json/videos/86400/str/%s/60/%s.%s.1.all..day.json"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=url_api % (host, "latest-updates", "", "")))
    itemlist.append(Item(channel=item.channel, title="Popular" , action="lista", url=url_api %  (host, "most-popular", "", "")))
    itemlist.append(Item(channel=item.channel, title="Longitud" , action="lista", url=url_api %  (host, "longest", "", "")))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="canal", url=host + "/api/json/channels/14400/str/most-viewed/80/..1.json"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/api/json/categories/14400/str.all.json"))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "%s/api/videos.php?params=259200/str/relevance/60/search..1.all..day&s=%s" % (host,texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["categories"]:
        scrapedtitle = Video["title"]
        dir = Video["dir"]
        vidnum = Video["total_videos"]
        url = url_api %(host, "latest-updates", "categories", dir)
        scrapedplot = ""
        title = "%s (%s)" % (scrapedtitle, vidnum)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                               thumbnail="", plot=scrapedplot) )
    return itemlist


def canal(item):
    logger.info()
    itemlist = []
    headers = {'Referer': "%s" % host}
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["channels"]:
        scrapedtitle = Video["title"]
        dir = Video["dir"]
        thumbnail= Video["cf4"]
        vidnum = Video["statistics"]
        url = "%s/api/json/videos/86400/str/latest-updates/20/channel.%s.1.all...json" % (host,dir)
        vidnum = scrapertools.find_single_match(vidnum, '"videos":"(\d+)"')
        thumbnail = thumbnail.replace("\/", "/")
        scrapedplot = ""
        title = "%s (%s)" % (scrapedtitle, vidnum)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=url,
                               thumbnail=thumbnail, plot=scrapedplot) )
    total= int(JSONData["total_count"])
    page = int(scrapertools.find_single_match(item.url,'(\d+).json'))
    url_page = scrapertools.find_single_match(item.url,'(.*?).\d+.json')
    next_page = (page+ 1)
    if (page*80) < total:
        next_page = "%s.%s.json" %(url_page,next_page)
        itemlist.append(Item(channel=item.channel, action="canal", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    headers = {'Referer': "%s" % host}
    data = httptools.downloadpage(item.url, headers=headers).data
    JSONData = json.load(data)
    for Video in  JSONData["videos"]:
        tit = Video["title"]
        id = Video["video_id"]
        veo = Video["dir"]
        time= Video["duration"]
        thumbnail = Video["scr"]
        quality = Video["props"]
        url = "%s/embed/%s/" % (host,id)
        title = "[COLOR yellow]%s[/COLOR] %s" % (time,tit)
        if "hd" in quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,tit)
        contentTitle = title
        thumbnail = thumbnail.replace("\/", "/")
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                              thumbnail=thumbnail, plot=plot, contentTitle = contentTitle))
    total= int(JSONData["total_count"])
    page = int(scrapertools.find_single_match(item.url,'(\d+).all..'))
    url_page = scrapertools.find_single_match(item.url,'(.*?).\d+.all..')
    post = scrapertools.find_single_match(item.url,'all..(.*)')
    next_page = (page+ 1)
    if (page*60) < total:
        next_page = "%s.%s.all..%s" %(url_page,next_page,post)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = servertools.find_video_items(Item(channel=item.channel, url = item.url, contentTitle = item.contentTitle))
    return itemlist


def play(item):
    logger.info(item)
    itemlist = servertools.find_video_items(Item(channel=item.channel, url = item.url, contentTitle = item.contentTitle))
    return itemlist