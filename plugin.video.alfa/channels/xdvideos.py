# -*- coding: utf-8 -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger

host = "http://xdvideos.org/"
hosts = "http://xdvideos.org/dragon-ball-super/"


def mainlist(item):
   logger.info()
   thumb_series = get_thumb("channels_tvshow.png")

   itemlist = list()

   itemlist.append(Item(channel=item.channel, action="categorias",
                        title="Categorias", url=host, thumbnail=thumb_series))
   itemlist.append(Item(channel=item.channel, action="episodios", title="Dragon Ball Super", url=hosts,
                        thumbnail=thumb_series))
   return itemlist


def categorias(item):
   logger.info()

   itemlist = []

   data = httptools.downloadpage(item.url).data
   data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
   patron = '<ul id="nav">(.+)>Problemas'
   data = scrapertools.find_single_match(data, patron)
   patron_cat = '<li id="menu-item-[^"]+" class=".+?"><a href="([^"]+)">([^"]+)<\/a><ul class="sub-menu">'
   matches = scrapertools.find_multiple_matches(data, patron_cat)
   for url, name in matches:
       if name != 'Clasicos':
           title = name
           itemlist.append(item.clone(title=title, url=url,
                                      action="lista", show=title))
   return itemlist


def lista(item):
   logger.info()
   itemlist = []

   data = httptools.downloadpage(item.url).data
   data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
   category = item.title
   patron = '<li id="menu-item-[^"]+" class="menu-item menu-item-type-post_type menu-item-object-page current-menu-item page_item page-item-[^"]+ current_page_item menu-item-has-children menu-item-[^"]+"><a href="[^"]+">[^"]+<\/a>(.+?)<\/a><\/li><\/ul><\/li>'
   content = scrapertools.find_single_match(data, patron)
   patron_lista = '<a href="([^"]+)">([^"]+)<\/a>'
   match_series = scrapertools.find_multiple_matches(content, patron_lista)
   for url, title in match_series:
       if "(" in title:
           show_dual = title.split("(")
           show = show_dual[1]
           if ")" in show:
               show = show.rstrip(")")
       else:
           show = title
       itemlist.append(item.clone(title=title, url=url,
                                  action="episodios", show=show, plot=show))
   tmdb.set_infoLabels(itemlist)
   return itemlist


def episodios(item):
   logger.info()
   itemlist = []

   data = httptools.downloadpage(item.url).data
   data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

   scrapedshow = scrapertools.find_single_match(
       data, '(?s)<h1 class="post-title">([^"]+)<\/h1>')

   scrapedthumbnail = scrapertools.find_single_match(
       data, '(?s)<h1 class="post-title">*?<img .+? src="([^"]+)"')

   data = scrapertools.find_single_match(
       data, '(?s)<div class="post-content">(.+?)<ul class="single-share">')

   patron_caps = '<a href="([^"]+)">([^"]+)<\/a>'
   matches = scrapertools.find_multiple_matches(data, patron_caps)

   for url, name in matches:
       if ("temporada" in url) and (("capitulo" in url) or ("episodio" in url)):
           if ("capitulo" in url):
               season, chapter = scrapertools.find_single_match(
                   url, 'temporada-([0-9]+)-?.+capitulo-([0-9]+)')
           if ("episodio" in url):
               season, chapter = scrapertools.find_single_match(
                   url, 'temporada-([0-9]+)-?.+episodio-([0-9]+)')
           title = season.zfill(2) + "x" + chapter.zfill(2) + " " + name
       else:
           title = name

       itemlist.append(
           item.clone(title=title, url=url, action="findvideos", show=scrapedshow, thumbnail=scrapedthumbnail))

   return itemlist


def findvideos(item):
   logger.info()

   itemlist = []

   data = httptools.downloadpage(item.url).data
   itemlist.extend(servertools.find_video_items(data=data))
   scrapedthumbnail = scrapertools.find_single_match(data, 'src="([^"]+)"')
   for videoitem in itemlist:
       videoitem.channel = item.channel
       videoitem.thumbnail = scrapedthumbnail

   return itemlist


