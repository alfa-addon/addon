# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,re
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.sxyprn.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/blog/all/0.html?fl=all&sm=latest"))
    itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/popular/top-viewed.html"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/popular/top-rated.html"))
    itemlist.append( Item(channel=item.channel, title="Sitios" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
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
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
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
        itemlist.append( Item(channel=item.channel, action="play", title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = scrapedtitle))
                              # 
    next_page = scrapertools.find_single_match(data, "<div class='ctrl_el ctrl_sel'>.*?<a href='([^']+)'")
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist
# https://www.sxyprn.com/cdn8/c8/nj1q9l31z6131t13zh562cze1e3x0/ERLyduuQGjVMXyrG_TKbMw/1568218449/bs5cby9d136r7id4ao7b883y7nb/3x5idy7x7yfgec9l7va5112z7gb.vid    
# https://www.sxyprn.com/cdn8/c8/bt1c9i38zj1b191hzl5g23zi1h3w0/fMvCX5Hmm0M7H0994MAD-Q/1568218381/5g5jb79n1e6s7tdwa07l8b3f7gb/nv5ud97b7vf9e69z7faq18287rb.vid
# https://c8.trafficdeposit.com/vidi/c1i963czt1c101rz4592szk1l350s/buNE54kwnno2po_2QOMk_w/1568218228/5b9167da7837b/5d77fe97a127b.vid
def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    url = scrapertools.find_single_match(data, 'data-vnfo=.*?":"([^"]+)"')
    url = url.replace("\/", "/").replace("/cdn/", "/cdn8/")
    url = urlparse.urljoin(item.url,url)
    itemlist.append( Item(channel=item.channel, action="play", title = item.title, url=url))
    return itemlist

