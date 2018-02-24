# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://gnula.nu/"
host_search = "https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=small&num=10&hl=es&prettyPrint=false&source=gcsc&gss=.es&sig=45e50696e04f15ce6310843f10a3a8fb&cx=014793692610101313036:vwtjajbclpq&q=%s&cse_tok=%s&googlehost=www.google.com&callback=google.search.Search.apiary10745&nocache=1519145965573&start=0"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Estrenos", action="peliculas",
                         url= host +"peliculas-online/lista-de-peliculas-online-parte-1/", viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, title="Generos", action="generos", url= host + "generos/lista-de-generos/"))
    itemlist.append(Item(channel=item.channel, title="Recomendadas", action="peliculas",
                         url= host + "peliculas-online/lista-de-peliculas-recomendadas/", viewmode="movie"))
    itemlist.append(Item(channel = item.channel, action = ""))
    itemlist.append(
        Item(channel=item.channel, title="Buscar", action="search", url = host_search))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    data = httptools.downloadpage(host).data
    url_cse = scrapertools.find_single_match(data, '<form action="([^"]+)"') + "?"
    bloque = scrapertools.find_single_match(data, '<form action=.*?</form>').replace('name="q"', "")
    matches = scrapertools.find_multiple_matches(bloque, 'name="([^"]+).*?value="([^"]+)')
    post = "q=" + texto + "&"
    for name, value in matches:
        post += name + "=" + value + "&"
    data = httptools.downloadpage(url_cse + post).data
    cse_token = scrapertools.find_single_match(data, "var cse_token='([^']+)'")
    item.url = host_search %(texto, cse_token)
    try:
        return sub_search(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron =  '(?s)clicktrackUrl":".*?q=(.*?)".*?'
    patron += 'title":"([^"]+)".*?'
    patron += 'cseImage":{"src":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedurl = scrapertools.find_single_match(scrapedurl, ".*?online/")
        scrapedtitle = scrapedtitle.decode("unicode-escape").replace(" online", "").replace("<b>", "").replace("</b>", "")
        if "ver-" not in scrapedurl:
            continue
        year = scrapertools.find_single_match(scrapedtitle, "\d{4}")
        contentTitle = scrapedtitle.replace("(%s)" %year,"").replace("Ver","").strip()
        itemlist.append(Item(action = "findvideos",
                             channel = item.channel,
                             contentTitle = contentTitle,
                             infoLabels = {"year":year},
                             title = scrapedtitle,
                             thumbnail = scrapedthumbnail,
                             url = scrapedurl
                             ))
    if itemlist:
        page = int(scrapertools.find_single_match(item.url, ".*?start=(\d+)")) + 10
        npage = (page / 10) + 1
        item_page = scrapertools.find_single_match(item.url, "(.*?start=)") + str(page)
        itemlist.append(Item(action = "sub_search",
                             channel = item.channel,
                             title = "[COLOR green]Página %s[/COLOR]" %npage,
                             url = item_page
                             ))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<spa[^>]+>Lista de g(.*?)/table')
    patron = '<strong>([^<]+)</strong> .<a href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for genero, scrapedurl in matches:
        title = scrapertools.htmlclean(genero)
        url = item.url + scrapedurl
        itemlist.append(Item(channel = item.channel,
                             action = 'peliculas',
                             title = title,
                             url = url,
                             viewmode = "movie"))
    itemlist = sorted(itemlist, key=lambda item: item.title)
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<a class="Ntooltip" href="([^"]+)">([^<]+)<span><br[^<]+'
    patron += '<img src="([^"]+)"></span></a>(.*?)<br'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, resto in matches:
        language = []
        plot = scrapertools.htmlclean(resto).strip()
        languages = scrapertools.find_multiple_matches(plot, r'\((V.)\)')
        quality = scrapertools.find_single_match(plot, r'(?:\[.*?\].*?)\[(.*?)\]')
        for lang in languages:
            language.append(lang)
        title = scrapedtitle + " " + plot
        if not scrapedurl.startswith("http"):
            scrapedurl = item.url + scrapedurl
        itemlist.append(Item(channel = item.channel,
                             action = 'findvideos',
                             title = title,
                             url = scrapedurl,
                             thumbnail = scrapedthumbnail,
                             plot = plot,
                             contentTitle = scrapedtitle,
                             contentType = "movie",
                             language=language,
                             quality=quality
                             ))
    return itemlist


def findvideos(item):
    logger.info("item=" + item.tostring())
    itemlist = []
    data = httptools.downloadpage(item.url).data
    item.plot = scrapertools.find_single_match(data, '<div class="entry">(.*?)<div class="iframes">')
    item.plot = scrapertools.htmlclean(item.plot).strip()
    item.contentPlot = item.plot
    patron = '<strong>Ver película online.*?>.*?>([^<]+)'
    scrapedopcion = scrapertools.find_single_match(data, patron)
    titulo_opcional = scrapertools.find_single_match(scrapedopcion, ".*?, (.*)").upper()
    bloque  = scrapertools.find_multiple_matches(data, 'contenedor_tab.*?/table')
    cuenta = 0
    for datos in bloque:
        cuenta = cuenta + 1
        patron = '<em>(opción %s.*?)</em>' %cuenta
        scrapedopcion = scrapertools.find_single_match(data, patron)
        titulo_opcion = "(" + scrapertools.find_single_match(scrapedopcion, "op.*?, (.*)").upper() + ")"
        if "TRAILER" in titulo_opcion or titulo_opcion == "()":
            titulo_opcion = "(" + titulo_opcional + ")"
        urls = scrapertools.find_multiple_matches(datos, '(?:src|href)="([^"]+)')
        titulo = "Ver en %s " + titulo_opcion
        for url in urls:
            itemlist.append(Item(channel = item.channel,
                                 action = "play",
                                 contentThumbnail = item.thumbnail,
                                 fulltitle = item.contentTitle,
                                 title = titulo,
                                 url = url
                                 ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist:
        if config.get_videolibrary_support():
                itemlist.append(Item(channel = item.channel, action = ""))
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     fulltitle = item.contentTitle
                                     ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
