# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core.item import Item
from core.tmdb import Tmdb
from platformcode import logger

host = "http://www.mejortorrent.com"


def mainlist(item):
    logger.info()

    itemlist = []

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_docus = get_thumb("channels_documentary.png")
    thumb_buscar = get_thumb("search.png")

    itemlist.append(Item(channel=item.channel, title="Peliculas", action="getlist",
                         url= host + "/torrents-de-peliculas.html", thumbnail=thumb_pelis))
    itemlist.append(Item(channel=item.channel, title="Peliculas HD", action="getlist",
                         url= host + "/torrents-de-peliculas-hd-alta-definicion.html",
                         thumbnail=thumb_pelis_hd))
    itemlist.append(Item(channel=item.channel, title="Series", action="getlist",
                         url= host + "/torrents-de-series.html", thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Series HD", action="getlist",
                         url= host + "/torrents-de-series-hd-alta-definicion.html",
                         thumbnail=thumb_series_hd))
    itemlist.append(Item(channel=item.channel, title="Series Listado Alfabetico", action="listalfabetico",
                         url= host + "/torrents-de-series.html", thumbnail=thumb_series_az))
    #itemlist.append(Item(channel=item.channel, title="Documentales", action="getlist",
    #                     url= host + "/torrents-de-documentales.html", thumbnail=thumb_docus))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", thumbnail=thumb_buscar))

    return itemlist


def listalfabetico(item):
    logger.info()

    itemlist = []

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                  'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(Item(channel=item.channel, action="getlist", title=letra,
                             url= host + "/series-letra-" + letra.lower() + ".html"))

    itemlist.append(Item(channel=item.channel, action="getlist", title="Todas",
                         url= host + "/series-letra..html"))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")

    item.url = host + "/secciones.php?sec=buscador&valor=%s" % (texto)
    try:
        return buscador(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def buscador(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = "<a href='(/serie-descargar-torrent[^']+)'[^>]+>(.*?)</a>"
    patron += ".*?<span style='color:gray;'>([^']+)</span>"
    patron_enlace = "/serie-descargar-torrents-\d+-\d+-(.*?)\.html"

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedurl, scrapedtitle, scrapedinfo in matches:
        title = scrapertools.remove_htmltags(scrapedtitle).decode('iso-8859-1').encode(
            'utf8') + ' ' + scrapedinfo.decode('iso-8859-1').encode('utf8')
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.debug("title=[" + title + "], url=[" + url + "]")

        itemlist.append(
            Item(channel=item.channel, action="episodios", title=title, url=url, folder=True, extra="series",
                 viewmode="movie_with_plot"))

    # busca pelis
    patron = "<a href='(/peli-descargar-torrent-[^']+)'[^>]+>(.*?)</a>"
    patron_enlace = "/peli-descargar-torrent-\d+(.*?)\.html"
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.remove_htmltags(scrapedtitle).decode('iso-8859-1').encode('utf-8')
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.debug("title=[" + title + "], url=[" + url + "]")
        itemlist.append(Item(channel=item.channel, action="play", title=title, url=url, folder=False, extra="pelicula"))

    # busca docu
    patron = "<a href='(/doc-descargar-torrent[^']+)' .*?"
    patron += "<font Color='darkblue'>(.*?)</font>.*?"
    patron += "<td align='right' width='20%'>(.*?)</td>"
    patron_enlace = "/doc-descargar-torrent-\d+-\d+-(.*?)\.html"
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedinfo in matches:
        title = scrapedtitle.decode('iso-8859-1').encode('utf8') + " " + scrapedinfo.decode('iso-8859-1').encode('utf8')
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.debug("title=[" + title + "], url=[" + url + "]")

        itemlist.append(Item(channel=item.channel, action="episodios",
                             title=title, url=url, folder=True, extra="docu",
                             viewmode="movie_with_plot"))

    return itemlist


def getlist(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.url.find("peliculas") > -1:
        patron = '<a href="(/peli-descargar-torrent[^"]+)">[^<]+'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "/peli-descargar-torrent-\d+(.*?)\.html"
        patron_title = '<a href="/peli-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        action = "show_movie_info"
        folder = True
        extra = ""
    elif item.url.find("series-letra") > -1:
        patron = "<a href='(/serie-descargar-torrent[^']+)'>()"
        patron_enlace = "/serie-descargar-torrents-\d+-\d+-(.*?)\.html"
        patron_title = '<a href="/serie-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        action = "episodios"
        folder = True
        extra = "series"
    elif item.url.find("series") > -1:
        patron = '<a href="(/serie-descargar-torrent[^"]+)">[^<]+'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "/serie-descargar-torrents-\d+-\d+-(.*?)\.html"
        patron_title = '<a href="/serie-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        action = "episodios"
        folder = True
        extra = "series"
    else:
        patron = '<a href="(/doc-descargar-torrent[^"]+)">[^<]+'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "/doc-descargar-torrent-\d+-\d+-(.*?)\.html"
        patron_title = '<a href="/doc-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        action = "episodios"
        folder = True
        extra = "docus"
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail in matches:
        title = scrapertools.get_match(scrapedurl, patron_enlace)
        title = title.replace("-", " ")
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = host + urllib.quote(scrapedthumbnail)
        plot = ""
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             folder=folder, extra=extra))

    matches = re.compile(patron_title, re.DOTALL).findall(data)

    cnt = 0
    for scrapedtitle, notused, scrapedinfo in matches:
        title = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        if title.endswith('.'):
            title = title[:-1]

        info = scrapedinfo.decode('iso-8859-1').encode('utf8')
        if info != "":
            title = '{0} {1}'.format(title, info)

        itemlist[cnt].title = title
        cnt += 1
        if cnt == len(itemlist) - 1:
            break

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="mainlist", title="No se ha podido cargar el listado"))
    else:
        # Extrae el paginador
        patronvideos = "<a href='([^']+)' class='paginar'> Siguiente >>"
        matches = re.compile(patronvideos, re.DOTALL).findall(data)

        if len(matches) > 0:
            scrapedurl = urlparse.urljoin(item.url, matches[0])
            itemlist.append(
                Item(channel=item.channel, action="getlist", title="Pagina siguiente >>", url=scrapedurl, folder=True))

    return itemlist


def episodios(item):
    #import web_pdb; web_pdb.set_trace()
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    total_capis = scrapertools.get_match(data, "<input type='hidden' name='total_capis' value='(\d+)'>")
    tabla = scrapertools.get_match(data, "<input type='hidden' name='tabla' value='([^']+)'>")
    titulo = scrapertools.get_match(data, "<input type='hidden' name='titulo' value='([^']+)'>")

    item.thumbnail = scrapertools.find_single_match(data,
                                                    "src='http://www\.mejortorrent\.com(/uploads/imagenes/" + tabla + "/[a-zA-Z0-9_ ]+.jpg)'")
    item.thumbnail = host + urllib.quote(item.thumbnail)

    # <form name='episodios' action='secciones.php?sec=descargas&ap=contar_varios' method='post'>
    data = scrapertools.get_match(data,
                                  "<form name='episodios' action='secciones.php\?sec=descargas\&ap=contar_varios' method='post'>(.*?)</form>")
    if item.extra == "series":
        patron = "<td bgcolor[^>]+><a[^>]+>([^>]+)</a></td>[^<]+"
    else:
        patron = "<td bgcolor[^>]+>([^>]+)</td>[^<]+"

    patron += "<td[^<]+<div[^>]+>Fecha: ([^<]+)</div></td>[^<]+"
    patron += "<td[^<]+"
    patron += "<input type='checkbox' name='([^']+)' value='([^']+)'"

    matches = re.compile(patron, re.DOTALL).findall(data)

    tmdb_title = re.sub(r'(\s*-\s*)?\d+.*?\s*Temporada|(\s*-\s*)?\s*Miniserie\.?|\(.*\)|\[.*\]', '', item.title).strip()
    logger.debug('tmdb_title=' + tmdb_title)
    #logger.debug(matches)
    #logger.debug(data)

    if item.extra == "series":
        oTmdb = Tmdb(texto_buscado=tmdb_title.strip(), tipo='tv', idioma_busqueda="es")
    else:
        oTmdb = Tmdb(texto_buscado=tmdb_title.strip(), idioma_busqueda="es")

    for scrapedtitle, fecha, name, value in matches:
        scrapedtitle = scrapedtitle.strip()
        if scrapedtitle.endswith('.'):
            scrapedtitle = scrapedtitle[:-1]
        #import web_pdb; web_pdb.set_trace()
        title = scrapedtitle + " (" + fecha + ")"
        patron = "<a href='(.*?)'>"

        url = host + scrapertools.find_single_match(data,patron)
        # "episodios%5B1%5D=11744&total_capis=5&tabla=series&titulo=Sea+Patrol+-+2%AA+Temporada"
        post = urllib.urlencode({name: value, "total_capis": total_capis, "tabla": tabla, "titulo": titulo})
        logger.debug("post=" + post)

        if item.extra == "series":
            epi = scrapedtitle.split("x")

            # Sólo comprobar Tmdb si el formato es temporadaXcapitulo
            if len(epi) > 1:
                temporada = re.sub("\D", "", epi[0])
                capitulo = re.search("\d+", epi[1])
                if capitulo:
                    capitulo = capitulo.group()
                else:
                    capitulo = 1

                epi_data = oTmdb.get_episodio(temporada, capitulo)
                logger.debug("epi_data=" + str(epi_data))

                if epi_data:
                    item.thumbnail = epi_data["temporada_poster"]
                    item.fanart = epi_data["episodio_imagen"]
                    item.plot = epi_data["episodio_sinopsis"]
                    epi_title = epi_data["episodio_titulo"]
                    if epi_title != "":
                        title = scrapedtitle + " " + epi_title + " (" + fecha + ")"
        else:
            try:
                item.fanart = oTmdb.get_backdrop()
            except:
                pass

            item.plot = oTmdb.get_sinopsis()

        logger.debug("title=[" + title + "], url=[" + url + "], item=[" + str(item) + "]")

        itemlist.append(
            Item(channel=item.channel, action="play", title=title, url=url, thumbnail=item.thumbnail, plot=item.plot,
                 fanart=item.fanart, extra=post, folder=False, id=value))

    return itemlist


def show_movie_info(item):
    logger.info()

    itemlist = []

    tmdb_title = re.sub(r'\(.*\)|\[.*\]', '', item.title).strip()
    logger.debug('tmdb_title=' + tmdb_title)

    try:
        oTmdb = Tmdb(texto_buscado=tmdb_title, idioma_busqueda="es")
        item.fanart = oTmdb.get_backdrop()
        item.plot = oTmdb.get_sinopsis()
    except:
        pass

    data = httptools.downloadpage(item.url).data
    logger.debug("data=" + data)

    patron = "<a href='(secciones.php\?sec\=descargas[^']+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        logger.debug("title=[" + item.title + "], url=[" + url + "], thumbnail=[" + item.thumbnail + "]")

        torrent_data = httptools.downloadpage(url).data
        link = scrapertools.get_match(torrent_data, "<a href='(\/uploads\/torrents\/peliculas\/.*?\.torrent)'>")
        link = urlparse.urljoin(url, link)
        logger.debug("link=" + link)
        itemlist.append(Item(channel=item.channel, action="play", server="torrent", title=item.title, url=link,
                             thumbnail=item.thumbnail, plot=item.plot, fanart=item.fanart, folder=False, extra="pelicula"))

    return itemlist


def play(item):
    #import web_pdb; web_pdb.set_trace()
    logger.info()
    itemlist = []

    if item.extra == "pelicula":
        itemlist.append(Item(channel=item.channel, action="play", server="torrent", title=item.title, url=item.url,
                            thumbnail=item.thumbnail, plot=item.plot, fanart=item.fanart, folder=False))
        #data = httptools.downloadpage(item.url).data
        #logger.debug("data=" + data)
        #url http://www.mejortorrent.com/peli-descargar-torrent-16443-Thor-Ragnarok.html
        #patron = host + "/peli-descargar-torrent-((.*?))-"
        #newid = scrapertools.find_single_match(item.url, patron)
		
		
		
        #params = dict(urlparse.parse_qsl(item.extra))
        #patron = host + "/secciones.php?sec=descargas&ap=contar&tabla=peliculas&id=" + newid[0] + "&link_bajar=1"
		#http://www.mejortorrent.com/secciones.php?sec=descargas&ap=contar&tabla=peliculas&id=16443&link_bajar=1
		#link=scrapertools.find_single_match(data,patron)
		#data = httptools.downloadpage(link).data
		
		
        #data = httptools.downloadpage(patron).data
        #patron = "Pincha <a href='(.*?)'>"
        #link = host + scrapertools.find_single_match(data, patron)
        #logger.info("link=" + link)
        #itemlist.append(Item(channel=item.channel, action="play", server="torrent", title=item.title, url=link,
        #                     thumbnail=item.thumbnail, plot=item.plot, folder=False))

    else:
        #data = httptools.downloadpage(item.url, post=item.extra).data
        data = httptools.downloadpage(item.url).data
        logger.debug("data=" + data)

        params = dict(urlparse.parse_qsl(item.extra))
        patron = host + "/secciones.php?sec=descargas&ap=contar&tabla=" + params["tabla"] + "&id=" + item.id
		#link=scrapertools.find_single_match(data,patron)
		#data = httptools.downloadpage(link).data
		
		
        data = httptools.downloadpage(patron).data
        patron = "Pincha <a href='(.*?)'>"
        link = host + scrapertools.find_single_match(data, patron)
        logger.info("link=" + link)
        itemlist.append(Item(channel=item.channel, action="play", server="torrent", title=item.title, url=link,
                             thumbnail=item.thumbnail, plot=item.plot, folder=False))
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'torrent':
            item.url = host + "/torrents-de-peliculas.html"

            itemlist = getlist(item)
            if itemlist[-1].title == "Pagina siguiente >>":
                itemlist.pop()
            item.url = host + "/torrents-de-series.html"
            itemlist.extend(getlist(item))
            if itemlist[-1].title == "Pagina siguiente >>":
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
