# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Kodi on Demand - Kodi Addon
# Canale per cineblog01
# ------------------------------------------------------------
import re
import urlparse

from channels import autoplay
from core import scrapertools, httptools, servertools, tmdb
from core.item import Item
from lib import unshortenit
from platformcode import logger, config

#impostati dinamicamente da getUrl()
host = ""
headers = ""

permUrl = httptools.downloadpage('https://www.cb01.uno/', follow_redirects=False).headers
host = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
headers = [['Referer', host]]

list_servers = ['openload', 'streamango', 'wstream']
list_quality = ['HD', 'SD']

#esclusione degli articoli 'di servizio'
blacklist = ['Aggiornamento Quotidiano Serie TV', 'Richieste Serie TV', 'CB01.UNO ▶ TROVA L’INDIRIZZO UFFICIALE', 'COMING SOON!', 'OSCAR 2019 ▶ CB01.UNO: Vota il tuo film preferito! 🎬']


def mainlist(item):
    logger.info("[cineblog01.py] mainlist")

    autoplay.init(item.channel, list_servers, list_quality)

    # Main options
    itemlist = [Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Novita'[/COLOR]",
                     url=host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="peliculas",
                     title="[COLOR azure]Alta Definizione [HD][/COLOR]",
                     url="%s/tag/film-hd-altadefinizione/" % host,
                     extra="movie",
                     thumbnail="http://jcrent.com/apple%20tv%20final/HD.png"),
                Item(channel=item.channel,
                     action="menuhd",
                     title="[COLOR azure]Menù HD[/COLOR]",
                     url=host,
                     extra="movie",
                     thumbnail="http://files.softicons.com/download/computer-icons/disks-icons-by-wil-nichols/png/256x256/Blu-Ray.png"),
                Item(channel=item.channel,
                     action="menugeneros",
                     title="[COLOR azure]Per Genere[/COLOR]",
                     url=host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="menuanyos",
                     title="[COLOR azure]Per Anno[/COLOR]",
                     url=host,
                     extra="movie",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Film[/COLOR]",
                     extra="movie",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"),
                Item(channel=item.channel,
                     action="listserie",
                     title="[COLOR azure]Serie Tv - Novita'[/COLOR]",
                     url="%s/serietv/" % host,
                     extra="tvshow",
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR yellow]Cerca Serie Tv[/COLOR]",
                     extra="tvshow",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("[cineblog01.py] newest")
    itemlist = []
    item = Item()
    if categoria == "film":
        item.url = host + '/lista-film-ultimi-100-film-aggiunti/'
        item.extra = "movie"
        try:
            # Carica la pagina 
            data = httptools.downloadpage(item.url).data
            blocco = scrapertools.get_match(data, 'Ultimi 100 film aggiunti:.*?<\/div>')
            patron = '<a href="([^"]+)">([^<]+)<\/a>'
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


def peliculas(item):
    logger.info("[cineblog01.py] peliculas")
    itemlist = []

    if item.url == "":
        item.url = host

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patronvideos = '<div class="span4".*?<a.*?<p><img src="([^"]+)".*?'
    patronvideos += '<div class="span8">.*?<a href="([^"]+)"> <h1>([^"]+)</h1></a>.*?'
    patronvideos += '<strong>([^<]*)[<br />,</strong>].*?<br />([^<+]+)'
    matches = re.compile(patronvideos, re.DOTALL).finditer(data)

    for match in matches:
        scrapedtitle = scrapertools.unescape(match.group(3))
        if not scrapedtitle in blacklist:
            scrapedurl = urlparse.urljoin(item.url, match.group(2))
            scrapedthumbnail = urlparse.urljoin(item.url, match.group(1))
            scrapedthumbnail = scrapedthumbnail.replace(" ", "%20")
            scrapedplot = scrapertools.unescape("[COLOR orange]" + match.group(4) + "[/COLOR]\n" + match.group(5).strip())
            scrapedplot = scrapertools.htmlclean(scrapedplot).strip()

            cleantitle = re.sub(r'(?:\[HD/?3?D?\]|\[Sub-ITA\])', '', scrapedtitle)
            year = scrapertools.find_single_match(scrapedtitle, r'\((\d{4})\)')
            infolabels = {}
            if year:
                cleantitle = cleantitle.replace("(%s)" % year, '').strip()
                infolabels['year'] = year

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="movie",
                     title=scrapedtitle,
                     fulltitle=cleantitle,
                     text_color="azure",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     plot=scrapedplot,
                     infoLabels=infolabels,
                     show=cleantitle,
                     extra=item.extra))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Next page mark
    #next_page = scrapertools.find_single_match(data, r"<link rel='next' href='(.*?)' />")
    #if not next_page:
    next_page = scrapertools.find_single_match(data, r'<li class="active_page"><a href="[^"]+">\d+</a></li>\s<li><a href="([^"]+)">\d+</a></li>')

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist

def menugeneros(item):
    logger.info("[cineblog01.py] menugeneros")
    return menulist(item, '<select name="select2"(.*?)</select>')


def menuhd(item):
    logger.info("[cineblog01.py] menuhd")
    return menulist(item, '<select name="select1"(.*?)</select>')


def menuanyos(item):
    logger.info("[cineblog01.py] menuvk")
    return menulist(item, '<select name="select3"(.*?)</select>')


def menulist(item, re_txt):
    itemlist = []

    data = httptools.downloadpage(item.url).data

    # Narrow search by selecting only the combo
    bloque = scrapertools.get_match(data, re_txt)

    # The categories are the options for the combo  
    patron = '<option value="([^"]+)">([^<]+)</option>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)
    scrapertools.printMatches(matches)

    for url, titulo in matches:
        scrapedtitle = titulo
        scrapedurl = urlparse.urljoin(item.url, url)
        scrapedthumbnail = ""
        scrapedplot = ""
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 extra=item.extra,
                 plot=scrapedplot))

    return itemlist


# Al llamarse "search" la función, el launcher pide un texto a buscar y lo añade como parámetro
def search(item, texto):
    logger.info("[cineblog01.py] " + item.url + " search " + texto)

    try:

        if item.extra == "movie":
            item.url = host + "/?s=" + texto
            return peliculas(item)
        if item.extra == "tvshow":
            item.url = host + "/serietv/?s=" + texto
            return listserie(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def listserie(item):
    logger.info("[cineblog01.py] listaserie")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data

    # Estrae i contenuti 
    patronvideos = '<div class="span4">\s*<a href="([^"]+)"><img src="([^"]+)".*?<div class="span8">.*?<h1>([^<]+)</h1></a>(.*?)<br><a'
    matches = re.compile(patronvideos, re.DOTALL).finditer(data)

    for match in matches:
        scrapedtitle = scrapertools.unescape(match.group(3))
        if not scrapedtitle in blacklist:
            scrapedurl = match.group(1)
            scrapedthumbnail = match.group(2)
            scrapedplot = scrapertools.unescape(match.group(4))
            scrapedplot = scrapertools.htmlclean(scrapedplot).strip()
            itemlist.append(
                Item(channel=item.channel,
                     action="season_serietv",
                     contentType="tvshow",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     extra=item.extra,
                     plot=scrapedplot))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Next page mark
    next_page = scrapertools.find_single_match(data, "<link rel='next' href='(.*?)' />")

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="listserie",
                 title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
                 url=next_page,
                 extra=item.extra,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


def season_serietv(item):
    def load_season_serietv(html, item, itemlist, season_title):
        if len(html) > 0 and len(season_title) > 0:
            itemlist.append(
                Item(channel=item.channel,
                     action="episodios",
                     title="[COLOR azure]%s[/COLOR]" % season_title,
                     contentType="episode",
                     url=html,
                     extra="tvshow",
                     show=item.show))

    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    # data = scrapertools.decodeHtmlentities(data)
    data = scrapertools.get_match(data, '<td bgcolor="#ECEAE1">(.*?)</table>')

    #   for x in range(0, len(scrapedtitle)-1):
    #        logger.debug('%x: %s - %s',x,ord(scrapedtitle[x]),chr(ord(scrapedtitle[x])))
    blkseparator = chr(32) + chr(226) + chr(128) + chr(147) + chr(32)
    data = data.replace(blkseparator, ' - ')

    starts = []
    season_titles = []
    patron = '^(?:seri|stagion)[i|e].*$'
    matches = re.compile(patron, re.MULTILINE | re.IGNORECASE).finditer(data)
    for match in matches:
        if match.group() != '':
            season_titles.append(match.group())
            starts.append(match.end())

    i = 1
    len_season_titles = len(season_titles)

    while i <= len_season_titles:
        inizio = starts[i - 1]
        fine = starts[i] if i < len_season_titles else -1

        html = data[inizio:fine]
        season_title = season_titles[i - 1]
        load_season_serietv(html, item, itemlist, season_title)
        i += 1

    return itemlist


def episodios(item):
    itemlist = []

    if item.extra == "tvshow":
        itemlist.extend(episodios_serie_new(item))

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios" + "###" + item.extra,
                 show=item.show))

    return itemlist


def episodios_serie_new(item):
    def load_episodios(html, item, itemlist, lang_title):
        # for data in scrapertools.decodeHtmlentities(html).splitlines():
        patron = '((?:.*?<a href=".*?"[^=]+="_blank"[^>]+>.*?<\/a>)+)'
        matches = re.compile(patron).findall(html)
        for data in matches:
            # Estrae i contenuti 
            scrapedtitle = data.split('<a ')[0]
            scrapedtitle = re.sub(r'<[^>]*>', '', scrapedtitle).strip()
            if scrapedtitle != 'Categorie':
                scrapedtitle = scrapedtitle.replace('&#215;', 'x')
                if scrapedtitle.find(' - ') > 0:
                    scrapedtitle = scrapedtitle[0:scrapedtitle.find(' - ')]
                itemlist.append(
                    Item(channel=item.channel,
                         action="findvideos",
                         contentType="episode",
                         title="[COLOR azure]%s[/COLOR]" % (scrapedtitle + " (" + lang_title + ")"),
                         url=data,
                         thumbnail=item.thumbnail,
                         extra=item.extra,
                         fulltitle=scrapedtitle + " (" + lang_title + ")" + ' - ' + item.show,
                         show=item.show))

    logger.info("[cineblog01.py] episodios")

    itemlist = []

    lang_title = item.title
    if lang_title.upper().find('SUB') > 0:
        lang_title = 'SUB ITA'
    else:
        lang_title = 'ITA'

    html = item.url
    load_episodios(html, item, itemlist, lang_title)

    return itemlist


def findvideos(item):
    if item.contentType == "movie":
        return findvid_film(item)
    if item.contentType == "episode":
        return findvid_serie(item)
    return []


def findvid_film(item):
    def load_links(itemlist, re_txt, color, desc_txt, quality=""):
        streaming = scrapertools.find_single_match(data, re_txt)
        patron = '<td><a[^h]href="([^"]+)"[^>]+>([^<]+)<'
        matches = re.compile(patron, re.DOTALL).findall(streaming)
        for scrapedurl, scrapedtitle in matches:
            logger.debug("##### findvideos %s ## %s ## %s ##" % (desc_txt, scrapedurl, scrapedtitle))
            title = "[COLOR " + color + "]" + desc_txt + ":[/COLOR] " + item.title + " [COLOR grey]" + QualityStr + "[/COLOR] [COLOR blue][" + scrapedtitle + "][/COLOR]"
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
    # data = scrapertools.decodeHtmlentities(data)

    # Extract the quality format
    patronvideos = '>([^<]+)</strong></div>'
    matches = re.compile(patronvideos, re.DOTALL).finditer(data)
    QualityStr = ""
    for match in matches:
        QualityStr = scrapertools.unescape(match.group(1))[6:]

    # Estrae i contenuti - Streaming
    load_links(itemlist, '<strong>Streaming:</strong>(.*?)<table height="30">', "orange", "Streaming", "SD")

    # Estrae i contenuti - Streaming HD
    load_links(itemlist, '<strong>Streaming HD[^<]+</strong>(.*?)<table height="30">', "yellow", "Streaming HD", "HD")

    autoplay.start(itemlist, item)

    # Estrae i contenuti - Streaming 3D
    load_links(itemlist, '<strong>Streaming 3D[^<]+</strong>(.*?)<table height="30">', "pink", "Streaming 3D")

    # Estrae i contenuti - Download
    load_links(itemlist, '<strong>Download:</strong>(.*?)<table height="30">', "aqua", "Download")

    # Estrae i contenuti - Download HD
    load_links(itemlist, '<strong>Download HD[^<]+</strong>(.*?)<table width="100%" height="20">', "azure",
               "Download HD")

    if len(itemlist) == 0:
        itemlist = servertools.find_video_items(item=item)

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
    patron = '<a\s[^>]+>[^<]+</a>([^<]+)'
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
            data = scrapertools.get_match(data, 'window.location.href = "([^"]+)";')
        except IndexError:
            try:
                # data = scrapertools.get_match(data, r'<a href="([^"]+)">clicca qui</a>')
                # In alternativa, dato che a volte compare "Clicca qui per proseguire":
                data = scrapertools.get_match(data, r'<a href="([^"]+)".*?class="btn-wrapper">.*?licca.*?</a>')
            except IndexError:
                data = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get(
                    "location", "")
        data, c = unshortenit.unwrap_30x_only(data)
        logger.debug("##### play go.php data ##\n%s\n##" % data)
    elif "/link/" in item.url:
        data = httptools.downloadpage(item.url).data
        from lib import jsunpack

        try:
            data = scrapertools.get_match(data, "(eval\(function\(p,a,c,k,e,d.*?)</script>")
            data = jsunpack.unpack(data)
            logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
        except IndexError:
            logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

        data = scrapertools.find_single_match(data, 'var link(?:\s)?=(?:\s)?"([^"]+)";')
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

