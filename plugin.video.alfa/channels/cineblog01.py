# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cineblog01
# ------------------------------------------------------------

import re
import urlparse

from channels import autoplay, filtertools
from core import scrapertoolsV2, httptools, servertools, tmdb
from core.item import Item
from lib import unshortenit
from platformcode import logger, config

#impostati dinamicamente da getUrl()
host = ""
headers = ""

permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
host = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'streamango', 'wstream']
list_quality = ['HD', 'SD']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'cineblog01')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'cineblog01')

#esclusione degli articoli 'di servizio'
blacklist = ['BENVENUTI ', 'Richieste Serie TV', 'CB01.UNO &#x25b6; TROVA L&#8217;INDIRIZZO UFFICIALE ', 'Aggiornamento Quotidiano Serie TV', 'OSCAR 2019 ▶ CB01.UNO: Vota il tuo film preferito! 🎬']


def mainlist(item):
    logger.info("[cineblog01.py] mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="video",
                     title="[B]Film[/B]",
                     url=host,
                     contentType="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Menù HD[/B]",
                     extra='Film HD Streaming',
                     url=host,
                     contentType="movie",
                     thumbnail="http://jcrent.com/apple%20tv%20final/HD.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Film per Genere[/B]",
                     extra='Film per Genere',
                     url=host,
                     contentType="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Film per Anno[/B]",
                     extra='Film per Anno',
                     url=host,
                     contentType="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR blue] > Cerca Film[/COLOR]",
                     contentType="movie",
                     url=host,
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
               
                Item(channel=item.channel,
                     action="video",
                     title="[B]Serie TV[/B]",
                     url=host + '/serietv/',
                     contentType="episode",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Serie-Tv per Lettera[/B]",
                     extra='Serie-Tv per Lettera',
                     url=host + '/serietv/',
                     contentType="episode",
                     thumbnail="http://jcrent.com/apple%20tv%20final/HD.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Serie-Tv per Genere[/B]",
                     extra='Serie-Tv per Genere',
                     url=host + '/serietv/',
                     contentType="episode",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="menu",
                     title="[B] > Serie-Tv per Anno[/B]",
                     extra='Serie-Tv per Anno',
                     url=host + '/serietv/',
                     contentType="episode",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR blue] > Cerca Serie TV[/COLOR]",
                     contentType="episode",
                     url=host + '/serietv/',
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                
                ]

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu(item):
    itemlist= []
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t','',data)
    block =  scrapertoolsV2.get_match(data, item.extra + r'<span.*?><\/span>.*?<ul.*?>(.*?)<\/ul>')
    patron = r'href="([^"]+)">(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(block)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(
                channel=item.channel,
                title=scrapedtitle,
                contentType=item.contentType,
                action='video',
                url=host + scrapedurl
            )
        )
    return itemlist

def search(item, text):
    logger.info("[cineblog01.py] " + item.url + " search " + text)

    try:
        item.url = item.url + "/?s=" + text
        return video(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(categoria):
    logger.info("[cineblog01.py] newest")
    itemlist = []
    item = Item()
    if categoria == "peliculas":
        item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
        item.extra = "movie"
        try:
            # Carica la pagina 
            data = httptools.downloadpage(item.url).data
            logger.info("[cineblog01.py] DATA: "+data)
            blocco = scrapertoolsV2.get_match(data, r'Ultimi 100 film aggiunti:.*?<\/td>')
            patron = r'<a href="([^"]+)">([^<]+)<\/a>'
            matches = re.compile(patron, re.DOTALL).findall(blocco)

            for scrapedurl, scrapedtitle in matches:
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="movie",
                         fulltitle=scrapedtitle,
                         show=scrapedtitle,
                         title=scrapedtitle,
                         text_color="azure",
                         url=scrapedurl,
                         extra=item.extra,
                         viewmode="movie_with_plot"))
        except:
            import sys
            for line in sys.exc_info():
                logger.error("{0}".format(line))
            return []
    return itemlist


def video(item):
    logger.info("[cineblog01.py] video")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t','',data)
    block = scrapertoolsV2.get_match(data, r'<div class="sequex-page-left">(.*?)<aside class="sequex-page-right">')

    if item.contentType == 'movie' or '/serietv/' not in item.url:
        action = 'findvideos'     
        logger.info("### FILM ###")
        patron = r'type-post.*?>.*?<img src="([^"]+)".*?<h3.*?<a href="([^"]+)">([^<]+)<\/a>.*?<strong>([^<]+)<.*?br \/>\s+(.*?)   '
        matches = re.compile(patron, re.DOTALL).findall(block)

        logger.info("### MATCHES ###" + str(matches))
        for scrapedthumb, scrapedurl, scrapedtitle, scrapedinfo, scrapedplot in matches:
            title = re.sub(r'(?:\[HD/?3?D?\]|\[Sub-ITA\])', '', scrapedtitle)
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'\((\d{4})\)')
            quality = scrapertoolsV2.find_single_match(scrapedtitle, r'\[(.*?)\]')
            genre = scrapertoolsV2.remove_htmltags(scrapertoolsV2.find_single_match(scrapedinfo, '([A-Z]+) &'))
            duration = scrapertoolsV2.find_single_match(scrapedinfo,'DURATA ([0-9]+)&')

            infolabels = {}
            if year:
                title = title.replace("(%s)" % year, '').strip()
                infolabels['Year'] = year
            if duration:
                infolabels['Duration'] = int(duration)*60
            if genre:
                infolabels['Genre'] = genre
            if quality:
                longtitle = '[B]' + title + '[/B] [COLOR blue][' + quality + '][/COLOR]'
            else:
                longtitle = '[B]' + title + '[/B]'

            infolabels['Plot'] = scrapertoolsV2.decodeHtmlentities(scrapedplot) + '...'
            
            if not scrapedtitle in blacklist:
                itemlist.append(
                    Item(channel=item.channel,
                        action="findvideos",
                        contentType=item.contentType,
                        title=longtitle,
                        fulltitle=title,
                        show=title,
                        url=scrapedurl,
                        infoLabels=infolabels,
                        thumbnail=scrapedthumb
                        )
                )
    else:
        action = 'episodios'
        patron = 'type-post.*?>(.*?)<div class="card-action">'
        matches = re.compile(patron, re.DOTALL).findall(block)

        for match in matches:
            patron = r'<img src="([^"]+)".*?<h3.*?<a href="([^"]+)">([^<]+)<\/a>.*?<p>(.*?)\(([0-9]+).*?\).*?<\/p>([^<>]*)(?:<\/p>)?'
            matches = re.compile(patron, re.DOTALL).findall(match)
            for scrapedthumb, scrapedurl, scrapedtitle, scrapedgenre, scrapedyear, scrapedplot in matches:
                longtitle = '[B]' + scrapedtitle + '[/B]'
                title = scrapedtitle
                infolabels = {}
                infolabels['Year'] = scrapedyear
                infolabels['Genre'] = scrapertoolsV2.remove_htmltags(scrapedgenre)
                infolabels['Plot'] = scrapertoolsV2.decodeHtmlentities(scrapedplot)
                if not scrapedtitle in blacklist:
                    itemlist.append(
                        Item(channel=item.channel,
                            action=action,
                            contentType=item.contentType,
                            title=longtitle,
                            fulltitle=title,
                            show=title,
                            url=scrapedurl,
                            infoLabels=infolabels,
                            thumbnail=scrapedthumb
                            )
                    )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    patron =  "<a class='page-link'" + ' href="([^"]+)"><i class="fa fa-angle-right">'
    next_page = scrapertoolsV2.find_single_match(data, patron)
    logger.info('NEXT '+next_page) 

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                action="video",
                contentType=item.contentType,
                title="[COLOR blue]" + config.get_localized_string(30992) + " >[/COLOR]",
                url=next_page))
      
    return itemlist


def episodios(item):
    logger.info("[cineblog01.py] episodios")
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t','',data)
    block = scrapertoolsV2.get_match(data, r'<article class="sequex-post-content">(.*?)<\/article>').replace('&#215;','x').replace(' &#8211; ','')
    logger.info(block)
    blockSeason = scrapertoolsV2.find_multiple_matches(block, '<div class="sp-head[a-z ]*?" title="Espandi">([^<>]*?)</div>(.*?)<div class="spdiv">\[riduci\]</div>')
    for season, block in blockSeason:
        patron = r'(?:<p>)?([0-9]+x[0-9]+)(.*?)(?:</p>|<br)'
        matches = re.compile(patron, re.DOTALL).findall(block)
        for scrapedtitle, scrapedurl in matches:
            title = '[B]' + scrapedtitle + '[/B] - ' + item.title + (' (SUB ITA)' if 'SUB ITA' in season else ' (ITA)')
            itemlist.append(
                    Item(channel=item.channel,
                        action="findvideos",
                        contentType=item.contentType,
                        title=title,
                        fulltitle=item.fulltitle,
                        show=item.fulltitle,
                        url=scrapedurl,
                        )
                    )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow][B]'+config.get_localized_string(30161)+'[/B][/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", show=item.show))

    return itemlist

def findvideos(item):
    if item.contentType == "episode":
        return findvid_serie(item)
    def load_links(itemlist, re_txt, color, desc_txt, quality=""):
        streaming = scrapertoolsV2.find_single_match(data, re_txt)
        patron = '<td><a[^h]href="([^"]+)"[^>]+>([^<]+)<'
        matches = re.compile(patron, re.DOTALL).findall(streaming)
        for scrapedurl, scrapedtitle in matches:
            logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
            title = "[COLOR " + color + "]" + desc_txt + ":[/COLOR] " + item.fulltitle + " [COLOR grey]" + QualityStr + "[/COLOR] [COLOR blue][" + scrapedtitle + "][/COLOR]"
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=title,
                     url=scrapedurl,
                     server=scrapedtitle,
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=quality,
                     contentType=item.contentType,
                     folder=False))

    logger.info("[cineblog01.py] findvid_film")

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Extract the quality format
    patronvideos = '>([^<]+)</strong></div>'
    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    QualityStr = ""
    for match in matches:
        QualityStr = scrapertoolsV2.decodeHtmlentities(match.group(1))[6:]

    # Estrae i contenuti - Streaming
    load_links(itemlist, '<strong>Streaming:</strong>(.*?)<table class="cbtable" height="30">', "orange", "Streaming", "SD")

    # Estrae i contenuti - Streaming HD
    load_links(itemlist, '<strong>Streaming HD[^<]+</strong>(.*?)<table class="cbtable" height="30">', "yellow", "Streaming HD", "HD")

    autoplay.start(itemlist, item)

    # Estrae i contenuti - Streaming 3D
    load_links(itemlist, '<strong>Streaming 3D[^<]+</strong>(.*?)<table class="cbtable" height="30">', "pink", "Streaming 3D")

    # Estrae i contenuti - Download
    load_links(itemlist, '<strong>Download:</strong>(.*?)<table class="cbtable" height="30">', "aqua", "Download")

    # Estrae i contenuti - Download HD
    load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<table class="cbtable" width="100%" height="20">', "azure",
               "Download HD")

    if len(itemlist) == 0:
        itemlist = servertools.find_video_items(item=item)

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow][B]'+config.get_localized_string(30161)+'[/B][/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.fulltitle))

    return itemlist

def findvid_serie(item):
    def load_vid_series(html, item, itemlist, blktxt):
        if len(blktxt) > 2:
            vtype = blktxt.strip()[:-1] + " - "
        else:
            vtype = ''
        patron = '<a href="([^"]+)"[^=]+="_blank"[^>]+>(.*?)</a>'
        # Estrae i contenuti 
        matches = re.compile(patron, re.DOTALL).finditer(html)
        for match in matches:
            scrapedurl = match.group(1)
            scrapedtitle = match.group(2)
            title = item.title + " [COLOR blue][" + vtype + scrapedtitle + "][/COLOR]"
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     title=title,
                     url=scrapedurl,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     contentType=item.contentType,
                     folder=False))

    logger.info("[cineblog01.py] findvid_serie")

    itemlist = []
    lnkblk = []
    lnkblkp = []

    data = item.url

    # First blocks of links
    if data[0:data.find('<a')].find(':') > 0:
        lnkblk.append(data[data.find(' - ') + 3:data[0:data.find('<a')].find(':') + 1])
        lnkblkp.append(data.find(' - ') + 3)
    else:
        lnkblk.append(' ')
        lnkblkp.append(data.find('<a'))

    # Find new blocks of links
    patron = r'<a\s[^>]+>[^<]+</a>([^<]+)'
    matches = re.compile(patron, re.DOTALL).finditer(data)
    for match in matches:
        sep = match.group(1)
        if sep != ' - ':
            lnkblk.append(sep)

    i = 0
    if len(lnkblk) > 1:
        for lb in lnkblk[1:]:
            lnkblkp.append(data.find(lb, lnkblkp[i] + len(lnkblk[i])))
            i = i + 1

    for i in range(0, len(lnkblk)):
        if i == len(lnkblk) - 1:
            load_vid_series(data[lnkblkp[i]:], item, itemlist, lnkblk[i])
        else:
            load_vid_series(data[lnkblkp[i]:lnkblkp[i + 1]], item, itemlist, lnkblk[i])

    return itemlist

def play(item):
    logger.info("[cineblog01.py] play")
    itemlist = []

    ### Handling new cb01 wrapper
    if host[9:] + "/film/" in item.url:
        iurl = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location", "")
        logger.info("/film/ wrapper: %s" % iurl)
        if iurl:
            item.url = iurl

    if '/goto/' in item.url:
        item.url = item.url.split('/goto/')[-1].decode('base64')

    item.url = item.url.replace('http://cineblog01.uno', 'http://k4pp4.pw')

    logger.debug("##############################################################")
    if "go.php" in item.url:
        data = httptools.downloadpage(item.url).data
        try:
            data = scrapertoolsV2.get_match(data, 'window.location.href = "([^"]+)";')
        except IndexError:
            try:
                # data = scrapertoolsV2.get_match(data, r'<a href="([^"]+)">clicca qui</a>')
                # In alternativa, dato che a volte compare "Clicca qui per proseguire":
                data = scrapertoolsV2.get_match(data, r'<a href="([^"]+)".*?class="btn-wrapper">.*?licca.*?</a>')
            except IndexError:
                data = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get(
                    "location", "")
        data, c = unshortenit.unwrap_30x_only(data)
        logger.debug("##### play go.php data ##\n%s\n##" % data)
    elif "/link/" in item.url:
        data = httptools.downloadpage(item.url).data
        from lib import jsunpack

        try:
            data = scrapertoolsV2.get_match(data, r"(eval\(function\(p,a,c,k,e,d.*?)</script>")
            data = jsunpack.unpack(data)
            logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
        except IndexError:
            logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

        data = scrapertoolsV2.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
        data, c = unshortenit.unwrap_30x_only(data)
        if data.startswith('/'):
            data = urlparse.urljoin("http://swzz.xyz", data)
            data = httptools.downloadpage(data).data
        logger.debug("##### play /link/ data ##\n%s\n##" % data)
    else:
        data = item.url
        logger.debug("##### play else data ##\n%s\n##" % data)
    logger.debug("##############################################################")

    try:
        itemlist = servertools.find_video_items(data=data)

        for videoitem in itemlist:
            videoitem.title = item.show
            videoitem.fulltitle = item.fulltitle
            videoitem.show = item.show
            videoitem.thumbnail = item.thumbnail
            videoitem.contentType = item.contentType
            videoitem.channel = item.channel
    except AttributeError:
        logger.error("vcrypt data doesn't contain expected URL")

    return itemlist