# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per animeleggendari
# ------------------------------------------------------------

import re

from channels import autoplay
from channels import filtertools, support
from core import servertools, httptools, scrapertools, tmdb
from platformcode import logger, config
from core.item import Item

host = "https://animeleggendari.com"

# Richiesto per Autoplay
IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango']
list_quality = ['default']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'animeleggendari')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'animeleggendari')

def mainlist(item):
    logger.info('[animeleggendari.py] mainlist')
    
    # Richiesto per Autoplay
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = [Item(channel=item.channel,
                     action="lista_anime",
                     title="[B]Anime Leggendari[/B]",
                     url="%s/category/anime-leggendari/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Anime [B]ITA[/B]",
                     url="%s/category/anime-ita/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Anime [B]SUB ITA[/B]",
                     url="%s/category/anime-sub-ita/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="Conclusi",
                     url="%s/category/serie-anime-concluse/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="lista_anime",
                     title="In Corso",
                     url="%s/category/anime-in-corso/" % host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="generi",
                     title="Generi >",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[B]Cerca...[/B]",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]
                     
    # Autoplay visualizza voce menu
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def search(item, texto):
    logger.info('[animeleggendari.py] search')
    
    item.url = host + "/?s=" + texto
    try:
        return lista_anime(item)
        
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def generi(item):
    logger.info('[animeleggendari.py] generi')
    itemlist = []

    data = httptools.downloadpage(item.url).data.replace('\n','').replace('\t','')
    logger.info("[animeleggendari.py] generi= "+data)
    
    blocco =scrapertools.find_single_match(data, r'Generi.*?<ul.*?>(.*?)<\/ul>')
    logger.info("[animeleggendari.py] blocco= "+blocco)
    patron = '<a href="([^"]+)">([^<]+)<'

    matches = re.compile(patron, re.DOTALL).findall(blocco)
    logger.info("[animeleggendari.py] matches= "+str(matches))

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.replace('Anime ','')
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_anime",
                 title=title,
                 url=scrapedurl))

    return itemlist

def lista_anime(item):
    logger.info('[animeleggendari.py] lista_anime')
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<a class="[^"]+" href="([^"]+)" title="([^"]+)"><img[^s]+src="([^"]+)"[^>]+'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip()).replace("streaming", "")
        if 'top 10 anime da vedere' in scrapedtitle.lower(): continue

        lang = scrapertools.find_single_match(scrapedtitle, r"((?:SUB ITA|ITA))")
        cleantitle = scrapedtitle.replace(lang, "").replace('(Streaming & Download)', '')
        cleantitle = cleantitle.replace('OAV', '').replace('OVA', '').replace('MOVIE', '')
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 contentType="tvshow" if 'movie' not in scrapedtitle.lower() and 'ova' not in scrapedtitle.lower() else "movie",
                 text_color="azure",
                 title=scrapedtitle.replace('(Streaming & Download)', '').replace(lang, '[B][' + lang + '][/B]'),
                 fulltitle=cleantitle,
                 url=scrapedurl,
                 show=cleantitle,
                 thumbnail=scrapedthumbnail,
                 folder=True))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    patronvideos = r'<a class="next page-numbers" href="([^"]+)">'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_anime",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist

def episodios(item):
    logger.info('[animeleggendari.py] episodios')
    itemlist = []

    data = httptools.downloadpage(item.url).data
    blocco = scrapertools.find_single_match(data, r'(?:<p style="text-align: left;">|<div class="pagination clearfix">\s*)(.*?)</span></a></div>')

    # Il primo episodio è la pagina stessa
    itemlist.append(
        Item(channel=item.channel,
             action="findvideos",
             contentType=item.contentType,
             title="Episodio: 1",
             text_color="azure",
             fulltitle="%s %s %s " % (support.color(item.title, "deepskyblue"), support.color("|", "azure"), support.color("1", "orange")),
             url=item.url,
             thumbnail=item.thumbnail,
             folder=True))
    if blocco != "":
        patron = r'<a href="([^"]+)".*?><span class="pagelink">(\d+)</span></a>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl, scrapednumber in matches:
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title="Episodio: %s" % scrapednumber,
                     text_color="azure",
                     fulltitle="%s %s %s " % (support.color(item.title, "deepskyblue"), support.color("|", "azure"), support.color(scrapednumber, "orange")),
                     url=scrapedurl,
                     thumbnail=item.thumbnail,
                     folder=True))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodi",
                 show=item.show))

    return itemlist

def findvideos(item):
    logger.info('[animeleggendari.py] findvideos')

    data = httptools.downloadpage(item.url).data
    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        server = re.sub(r'[-\[\]\s]+', '', videoitem.title)
        videoitem.title = "".join(["[%s] " % support.color(server.capitalize(), 'orange'), item.title])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        
    # Richiesto per Verifica se i link esistono
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
        
    # Richiesto per FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
        
    # Autoplay
    autoplay.start(itemlist, item)
    
    return itemlist
