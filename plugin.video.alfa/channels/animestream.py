# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per animestream
# ----------------------------------------------------------
import re, urlparse

from core import httptools, scrapertools
from core.item import Item
from platformcode import logger, config



host = "http://www.animestream.it/"

hostcategoria = host + "/Ricerca-Tutti-pag1"


def mainlist(item):
    logger.info("kod.animestram mainlist")

    itemlist = [Item(channel=item.channel,
                     action="lista_anime",
                     title="[COLOR azure]Anime[/COLOR]",
                     url=Crea_Url(),
                     thumbnail=AnimeThumbnail,
                     fanart=AnimeFanart),
                Item(channel=item.channel,
                     action="categoria",
                     title="[COLOR azure]Categorie[/COLOR]",
                     url=hostcategoria,
                     thumbnail=CategoriaThumbnail,
                     fanart=CategoriaFanart),
                Item(channel=item.channel,
                     action="search",
                     title="[COLOR orange]Cerca...[/COLOR]",
                     extra="anime",
                     thumbnail=CercaThumbnail,
                     fanart=CercaFanart)]

    return itemlist


def lista_anime(item):
    logger.info("kod.animestram lista_anime")
    itemlist = []

    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(item.url, patron):
        logger.debug(
            "kod.animestram lista_anime scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    # Paginazione
    # ===========================================================
    pagina = scrapedSingle(item.url, '<div class="navc">.*?</div>', '<b.*?id="nav".*>.*?</b>[^<]+<.*?>(.*?)</a>')
    if len(pagina) > 0:
        paginaurl = Crea_Url(pagina[0], "ricerca")
        logger.debug("kod.animestram lista_anime Paginaurl: " + paginaurl)
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_anime",
                 title=AvantiTxt,
                 url=paginaurl,
                 thumbnail=AvantiImg,
                 folder=True))
    # ===========================================================

    return itemlist


def lista_anime_categoria(item):
    logger.info("kod.animestram lista_anime_categoria")
    itemlist = []

    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(item.url, patron):
        logger.debug(
            "kod.animestram lista_anime_categoria scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    # Paginazione
    # ===========================================================
    pagina = scrapedSingle(item.url, '<div class="navc">.*?</div>', '<b.*?id="nav".*>.*?</b>[^<]+<.*?>(.*?)</a>')
    if len(pagina) > 0:
        paginaurl = Crea_Url(pagina[0], "ricerca", item.title)
        logger.debug("kod.animestram Paginaurl: " + paginaurl)
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_anime_categoria",
                 title=AvantiTxt,
                 url=paginaurl,
                 thumbnail=AvantiImg,
                 folder=True))
    # ===========================================================
    return itemlist


def search(item, texto):
    logger.info("kod.animestram search " + texto)
    itemlist = []

    url = Crea_Url("1", "ricerca", "", texto)
    patron = 'class="anime"[^<]+<.*?window.location=\'(.*?)\'.*?url\((.*?)\);">[^=]+[^<]+[^>]+[^<]+<h4>(.*?)</h4>'

    for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(url, patron):
        logger.debug(
            "scrapedurl: " + scrapedurl + " scrapedthumbnail:" + scrapedthumbnail + "scrapedtitle:" + scrapedtitle)
        scrapedthumbnail = scrapedthumbnail.replace("(", "")
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                 fulltitle=scrapedtitle,
                 show=scrapedtitle,
                 fanart=urlparse.urljoin(host, scrapedthumbnail)))

    return itemlist


def categoria(item):
    logger.info("kod.animestram categoria")
    itemlist = []
    patron = '<option value="(.*?)">.*?</option>'

    for scrapedCategoria in scrapedAll(item.url, patron):
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedCategoria)
        cat = Crea_Url("", "ricerca", scrapedtitle.replace(' ', "%20"))
        if len(scrapedtitle) > 0:
            itemlist.append(
                Item(channel=item.channel,
                     action="lista_anime_categoria",
                     title=scrapedtitle,
                     url=cat,
                     thumbnail="",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     fanart=AnimeFanart))

    return itemlist


def episodios(item):
    logger.info("kod.animestram episodios")
    itemlist = []

    patron = 'class="episodio">\s*<.*?href=([^>]+)><img.*?src=(.*?)width[^<]+<[^<]+<[^<]+<[^<]+<.*?>(.*?)</a>'
    patronvideos = '<a id="nav" href="([^"]+)">></a>'
    url = urlparse.urljoin(host, item.url)

    while True:
        for scrapedurl, scrapedthumbnail, scrapedtitle in scrapedAll(url, patron):
            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="episode",
                     title=scrapedtitle,
                     url=scrapedurl,
                     thumbnail=urlparse.urljoin(host, scrapedthumbnail),
                     fulltitle=item.show + ' | ' + scrapedtitle,
                     show=item.show,
                     fanart=urlparse.urljoin(host, scrapedthumbnail)))

        data = httptools.downloadpage(urlparse.urljoin(host, item.url)).data
        matches = re.compile(patronvideos, re.DOTALL).findall(data)

        if len(matches) > 0:
            url = urlparse.urljoin(url, matches[0])
        else:
            break

    if config.get_videolibrary_support() and len(itemlist) != 0:
        itemlist.append(
            Item(channel=item.channel,
                 title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
                 url=item.url,
                 action="add_serie_to_library",
                 extra="episodios",
                 show=item.show))

    return itemlist


def findvideos(item):
    logger.info("kod.animestram findvideos")
    itemlist = []

    patron = '<source.*?src="(.*?)".*?>'
    for scrapedurl in scrapedAll(urlparse.urljoin(host, item.url), patron):
        url = urlparse.urljoin(host, scrapedurl)
        logger.debug("kod.animestram player url Video:" + url)
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title=item.title,
                 url=url,
                 thumbnail=item.thumbnail,
                 plot=item.plot,
                 fanart=item.fanart,
                 contentType=item.contentType,
                 folder=False))

    return itemlist


def scrapedAll(url="", patron=""):
    data = httptools.downloadpage(url).data
    MyPatron = patron
    matches = re.compile(MyPatron, re.DOTALL).findall(data)
    scrapertools.printMatches(matches)

    return matches


def scrapedSingle(url="", single="", patron=""):
    data = httptools.downloadpage(url).data
    paginazione = scrapertools.find_single_match(data, single)
    matches = re.compile(patron, re.DOTALL).findall(paginazione)
    scrapertools.printMatches(matches)

    return matches


def Crea_Url(pagina="1", azione="ricerca", categoria="", nome=""):
    # esempio
    # chiamate.php?azione=ricerca&cat=&nome=&pag=
    Stringa = host + "chiamate.php?azione=" + azione + "&cat=" + categoria + "&nome=" + nome + "&pag=" + pagina
    logger.debug("kod.animestram CreaUrl " + Stringa)

    return Stringa


AnimeThumbnail = "http://img15.deviantart.net/f81c/i/2011/173/7/6/cursed_candies_anime_poster_by_careko-d3jnzg9.jpg"
AnimeFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CategoriaThumbnail = "http://static.europosters.cz/image/750/poster/street-fighter-anime-i4817.jpg"
CategoriaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
CercaThumbnail = "http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search"
CercaFanart = "https://i.ytimg.com/vi/IAlbvyBdYdY/maxresdefault.jpg"
AvantiTxt = config.get_localized_string(30992)
AvantiImg = "http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"
