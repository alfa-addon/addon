# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,re
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import jsontools as json

host = 'https://www.sxyprn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/blog/all/0.html?fl=all&sm=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/popular/top-viewed.html"))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/popular/top-rated.html"))
    itemlist.append(item.clone(title="Sitios" , action="categorias", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = host + "/%s.html" % texto
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    if "Sitios" in item.title:
        patron = "<a href='([^']+)' target='_blank'><div class='top_sub_el top_sub_el_sc'>.*?"
        patron += "<span class='top_sub_el_key_sc'>([^<]+)</span>"
        patron += "<span class='top_sub_el_count'>(\d+)</span>"
    else:
        patron = "<a class='tdn' href='([^']+)'.*?"
        patron += "<span class='htag_el_tag'>([^<]+)</span>"
        patron += "<span class='htag_el_count'>(\d+) videos</span>"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " (" + cantidad + ")"
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist



def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = "<img class=.*?"
    patron += " src='([^']+)'.*?"
    patron += "<span class='duration_small'.*?'>([^<]+)<.*?"
    patron += "<span class='shd_small'.*?>([^<]+)<.*?"
    patron += "post_time' href='([^']+)' title='([^']+)'"
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedtime,quality,scrapedurl,scrapedtitle in matches:
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (scrapedtime,quality,scrapedtitle)
        thumbnail = "https:" + scrapedthumbnail
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append(item.clone(action="play", title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
                              # 
    next_page = scrapertools.find_single_match(data, "<div class='ctrl_el ctrl_sel'>.*?<a href='([^']+)'")
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def play(item):
    from lib import alfa_assistant
    logger.info()
    itemlist = []
    video_urls = []
    alfa_assistant.open_alfa_assistant()
    data = alfa_assistant.get_source_by_page_finished(item.url, 4, closeAfter=True)
    for visited in  data["urlsVisited"]:
        if "/cdn8/" in visited["url"]:
            url = visited["url"]
            url = httptools.downloadpage(url, follow_redirects=False).headers["location"]
            if not url.startswith("https"):
                url = "https:%s" % url
            itemlist.append(item.clone(action="play", contentTitle = item.title, url=url))
    alfa_assistant.close_alfa_assistant()
    return itemlist




# def play(item):
    # itemlist = []
    # data = httptools.downloadpage(item.url).data
    # data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    # url = scrapertools.find_single_match(data, 'data-vnfo=.*?":"([^"]+)"')
    # url = url.replace("\/", "/").replace("/cdn/", "/cdn8/")
    # url = urlparse.urljoin(item.url,url)
    # logger.debug(url)
    # url = httptools.downloadpage(url, follow_redirects=False).headers["location"]
    # itemlist = servertools.find_video_items(item.clone(url = url, contentTitle = item.title))
    # return itemlist


