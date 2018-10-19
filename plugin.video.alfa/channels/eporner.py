# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import jsontools
from platformcode import logger


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Últimos videos", action="videos", url="http://www.eporner.com/0/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url="http://www.eporner.com/categories/"))
    itemlist.append(item.clone(title="Pornstars", action="pornstars_list", url="http://www.eporner.com/pornstars/"))
    itemlist.append(item.clone(title="Buscar", action="search", url="http://www.eporner.com/search/%s/"))

    return itemlist


def search(item, texto):
    logger.info()

    item.url = item.url % texto
    item.action = "videos"

    try:
        return videos(item)
    except:
        import traceback
        logger.error(traceback.format_exc())
        return []


def pornstars_list(item):
    logger.info()
    itemlist = []
    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        itemlist.append(item.clone(title=letra, url=urlparse.urljoin(item.url, letra), action="pornstars"))

    return itemlist


def pornstars(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="mbtit" itemprop="name"><a href="([^"]+)" title="([^"]+)">[^<]+</a></div> '
    patron += '<a href="[^"]+" title="[^"]+"> <img src="([^"]+)" alt="[^"]+" style="width:190px;height:152px;" /> </a> '
    patron += '<div class="mbtim"><span>Videos: </span>([^<]+)</div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumbnail, count in matches:
        itemlist.append(
            item.clone(title="%s (%s videos)" % (title, count), url=urlparse.urljoin(item.url, url), action="videos",
                       thumbnail=thumbnail))

    # Paginador
    patron = "<span style='color:#FFCC00;'>[^<]+</span></a> <a href='([^']+)' title='[^']+'><span>[^<]+</span></a>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    if matches:
        itemlist.append(item.clone(title="Pagina siguiente", url=urlparse.urljoin(item.url, matches[0])))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="categoriesbox" id="[^"]+"> <div class="ctbinner"> <a href="([^"]+)" title="[^"]+"> <img src="([^"]+)" alt="[^"]+"> <h2>([^"]+)</h2> </a> </div> </div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title in matches:
        itemlist.append(
            item.clone(title=title, url=urlparse.urljoin(item.url, url), action="videos", thumbnail=thumbnail))

    return sorted(itemlist, key=lambda i: i.title)


def videos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data


               #     <div class="mb hdy" onmouseenter="show_video_prev(1920028,320,180,1,0);" id="vf1920028">
               #    <div class="mvhdico"><span>1080p</span></div>
               #    <a href="/hd-porn/ap7rgEHO2mc/VIXEN-Kendra-Sunderland-Passionate-Sex-On-A-Beach/" title="VIXEN Kendra Sunderland Passionate Sex On A Beach" id="ahh1920028">
               #       <div id="tbn1920028" class="mbimg">
               #          <div class="mbcontent"> <img id="t1920028" src="https://static-eu-cdn.eporner.com/thumbs/static4/1/19/192/1920028/14_240.jpg" onmouseout='endm("t1920028", 14, 1);' onmouseover='startm("t1920028", 0, 1);' alt="VIXEN Kendra Sunderland Passionate Sex On A Beach" /> </div>
               #       </div>
               #       <div class="mbtit">VIXEN Kendra Sunderland Passionate Sex On A Beach</div>
               #    </a>
               #    <div class="mbstats">
               #       <div class="mbtim">12:27</div>
               #       <div class="mbrate">86%</div>
               #       <div class="mbvie">18,271</div>
               #    </div>
               # </div>

    patron = '<a href="([^"]+)" title="([^"]+)" id="[^"]+">.*?<img id="[^"]+" src="([^"]+)".*?<div class="mbtim">(.*?)</div>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, title, thumbnail, duration in matches:
        title = "[COLOR yellow]" + duration + "[/COLOR] " +  title
        itemlist.append(item.clone(title=title, url=urlparse.urljoin(item.url, url),
                                   action="play", thumbnail=thumbnail, contentThumbnail=thumbnail,
                                   contentType="movie", contentTitle=title))

    # Paginador        <a href='/2/' title='Next page'><span style='color:#FFCC00;'>NEXT &raquo;</span></a> </div>
    patron = "<a href='([^']+)' title='Next page'><span style='color:#FFCC00;'>NEXT &raquo;</span></a> "
    matches = re.compile(patron, re.DOTALL).findall(data)
    if matches:
        itemlist.append(item.clone(title="Página siguiente", url=urlparse.urljoin(item.url, matches[0])))

    return itemlist


def int_to_base36(num):
    """Converts a positive integer into a base36 string."""
    assert num >= 0
    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'.lower()

    res = ''
    while not res or num > 0:
        num, i = divmod(num, 36)
        res = digits[i] + res
    return res


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = "EP: { vid: '([^']+)', hash: '([^']+)'"

    vid, hash = re.compile(patron, re.DOTALL).findall(data)[0]

    hash = int_to_base36(int(hash[0:8], 16)) + int_to_base36(int(hash[8:16], 16)) + int_to_base36(
        int(hash[16:24], 16)) + int_to_base36(int(hash[24:32], 16))

    url = "https://www.eporner.com/xhr/video/%s?hash=%s" % (vid, hash)
    data = httptools.downloadpage(url).data
    jsondata = jsontools.load(data)

    for source in jsondata["sources"]["mp4"]:
        url = jsondata["sources"]["mp4"][source]["src"]
        title = source.split(" ")[0]

        itemlist.append(["%s %s [directo]" % (title, url[-4:]), url])

    return sorted(itemlist, key=lambda i: int(i[0].split("p")[0]))
