# -*- coding: utf-8 -*-

import base64
import re
import urllib
import urlparse

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

host = "http://hdfull.tv"

if config.get_setting('hdfulluser', 'hdfull'):
    account = True
else:
    account = False


def settingCanal(item):
    return platformtools.show_channel_settings()


def login():
    logger.info()

    data = agrupa_datos(httptools.downloadpage(host).data)

    patron = "<input type='hidden' name='__csrf_magic' value=\"([^\"]+)\" />"
    sid = scrapertools.find_single_match(data, patron)

    post = urllib.urlencode({'__csrf_magic': sid}) + "&username=" + config.get_setting('hdfulluser',
                                                                                       'hdfull') + "&password=" + config.get_setting(
        'hdfullpassword', 'hdfull') + "&action=login"

    httptools.downloadpage(host, post=post)


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, action="menupeliculas", title="Películas", url=host, folder=True))
    itemlist.append(Item(channel=item.channel, action="menuseries", title="Series", url=host, folder=True))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar..."))
    if not account:
        itemlist.append(Item(channel=item.channel, title="[COLOR orange][B]Habilita tu cuenta para activar los items de usuario...[/B][/COLOR]",
                             action="settingCanal", url=""))
    else:
        login()
        itemlist.append(Item(channel=item.channel, action="settingCanal", title="Configuración...", url=""))

    return itemlist


def menupeliculas(item):
    logger.info()

    itemlist = []

    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Favoritos[/B][/COLOR]",
                             url=host + "/a/my?target=movies&action=favorite&start=-28&limit=28", folder=True))
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Pendientes[/B][/COLOR]",
                             url=host + "/a/my?target=movies&action=pending&start=-28&limit=28", folder=True))

    itemlist.append(Item(channel=item.channel, action="fichas", title="ABC", url=host + "/peliculas/abc", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Últimas películas", url=host + "/peliculas", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Películas Estreno", url=host + "/peliculas-estreno",
             folder=True))
    itemlist.append(Item(channel=item.channel, action="fichas", title="Películas Actualizadas",
                         url=host + "/peliculas-actualizadas", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Rating IMDB", url=host + "/peliculas/imdb_rating",
             folder=True))
    itemlist.append(Item(channel=item.channel, action="generos", title="Películas por Género", url=host, folder=True))
    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Vistas[/B][/COLOR]",
                             url=host + "/a/my?target=movies&action=seen&start=-28&limit=28", folder=True))

    return itemlist


def menuseries(item):
    logger.info()

    itemlist = []

    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Siguiendo[/B][/COLOR]",
                             url=host + "/a/my?target=shows&action=following&start=-28&limit=28", folder=True))
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Para Ver[/B][/COLOR]",
                             url=host + "/a/my?target=shows&action=watch&start=-28&limit=28", folder=True))

    itemlist.append(Item(channel=item.channel, action="series_abc", title="A-Z", folder=True))

    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos Emitidos",
                         url=host + "/a/episodes?action=latest&start=-24&limit=24&elang=ALL", folder=True))
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Episodios Estreno",
                         url=host + "/a/episodes?action=premiere&start=-24&limit=24&elang=ALL", folder=True))
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Episodios Actualizados",
                         url=host + "/a/episodes?action=updated&start=-24&limit=24&elang=ALL", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Últimas series", url=host + "/series", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Rating IMDB", url=host + "/series/imdb_rating", folder=True))
    itemlist.append(
        Item(channel=item.channel, action="generos_series", title="Series por Género", url=host, folder=True))
    itemlist.append(Item(channel=item.channel, action="listado_series", title="Listado de todas las series",
                         url=host + "/series/list", folder=True))
    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Favoritas[/B][/COLOR]",
                             url=host + "/a/my?target=shows&action=favorite&start=-28&limit=28", folder=True))
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Pendientes[/B][/COLOR]",
                             url=host + "/a/my?target=shows&action=pending&start=-28&limit=28", folder=True))
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Vistas[/B][/COLOR]",
                             url=host + "/a/my?target=shows&action=seen&start=-28&limit=28", folder=True))

    return itemlist


def search(item, texto):
    logger.info()

    data = agrupa_datos(httptools.downloadpage(host).data)

    sid = scrapertools.get_match(data, '.__csrf_magic. value="(sid:[^"]+)"')
    item.extra = urllib.urlencode({'__csrf_magic': sid}) + '&menu=search&query=' + texto
    item.title = "Buscar..."
    item.url = host + "/buscar"

    try:
        return fichas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def series_abc(item):
    logger.info()

    itemlist = []

    az = "ABCDEFGHIJKLMNOPQRSTUVWXYZ#"

    for l in az:
        itemlist.append(
            Item(channel=item.channel, action='fichas', title=l, url=host + "/series/abc/" + l.replace('#', '9')))

    return itemlist


def items_usuario(item):
    logger.info()

    itemlist = []
    ## Carga estados
    status = jsontools.load(httptools.downloadpage(host + '/a/status/all').data)

    ## Fichas usuario
    url = item.url.split("?")[0]
    post = item.url.split("?")[1]

    old_start = scrapertools.get_match(post, 'start=([^&]+)&')
    limit = scrapertools.get_match(post, 'limit=(\d+)')
    start = "%s" % (int(old_start) + int(limit))

    post = post.replace("start=" + old_start, "start=" + start)
    next_page = url + "?" + post

    ## Carga las fichas de usuario
    data = httptools.downloadpage(url, post=post).data
    fichas_usuario = jsontools.load(data)

    for ficha in fichas_usuario:

        try:
            title = ficha['title']['es'].strip()
        except:
            title = ficha['title']['en'].strip()

        try:
            title = title.encode('utf-8')
        except:
            pass

        show = title

        try:
            thumbnail = host + "/thumbs/" + ficha['thumbnail']
        except:
            thumbnail = host + "/thumbs/" + ficha['thumb']

        try:
            url = urlparse.urljoin(host, '/serie/' + ficha['permalink']) + "###" + ficha['id'] + ";1"
            action = "episodios"
            str = get_status(status, 'shows', ficha['id'])
            if "show_title" in ficha:
                action = "findvideos"
                try:
                    serie = ficha['show_title']['es'].strip()
                except:
                    serie = ficha['show_title']['en'].strip()
                temporada = ficha['season']
                episodio = ficha['episode']
                serie = "[COLOR whitesmoke][B]" + serie + "[/B][/COLOR]"
                if len(episodio) == 1: episodio = '0' + episodio
                try:
                    title = temporada + "x" + episodio + " - " + serie + ": " + title
                except:
                    title = temporada + "x" + episodio + " - " + serie.decode('iso-8859-1') + ": " + title.decode(
                        'iso-8859-1')
                url = urlparse.urljoin(host, '/serie/' + ficha[
                    'permalink'] + '/temporada-' + temporada + '/episodio-' + episodio) + "###" + ficha['id'] + ";3"
        except:
            url = urlparse.urljoin(host, '/pelicula/' + ficha['perma']) + "###" + ficha['id'] + ";2"
            action = "findvideos"
            str = get_status(status, 'movies', ficha['id'])
        if str != "": title += str

        # try: title = title.encode('utf-8')
        # except: pass

        itemlist.append(
            Item(channel=item.channel, action=action, title=title, fulltitle=title, url=url, thumbnail=thumbnail,
                 show=show, folder=True))

    if len(itemlist) == int(limit):
        itemlist.append(
            Item(channel=item.channel, action="items_usuario", title=">> Página siguiente", url=next_page, folder=True))

    return itemlist


def listado_series(item):
    logger.info()

    itemlist = []

    data = agrupa_datos(httptools.downloadpage(item.url).data)

    patron = '<div class="list-item"><a href="([^"]+)"[^>]+>([^<]+)</a></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl + "###0;1"
        itemlist.append(
            Item(channel=item.channel, action="episodios", title=scrapedtitle, fulltitle=scrapedtitle, url=url,
                 show=scrapedtitle, contentType="tvshow"))

    return itemlist


def fichas(item):
    logger.info()
    itemlist = []
    textoidiomas=''
    infoLabels=dict()
    ## Carga estados
    status = jsontools.load(httptools.downloadpage(host + '/a/status/all').data)

    if item.title == "Buscar...":
        data = agrupa_datos(httptools.downloadpage(item.url, post=item.extra).data)
        s_p = scrapertools.get_match(data, '<h3 class="section-title">(.*?)<div id="footer-wrapper">').split(
            '<h3 class="section-title">')

        if len(s_p) == 1:
            data = s_p[0]
            if 'Lo sentimos</h3>' in s_p[0]:
                return [Item(channel=item.channel, title="[COLOR gold][B]HDFull:[/B][/COLOR] [COLOR blue]" + texto.replace('%20',
                                                                                      ' ') + "[/COLOR] sin resultados")]
        else:
            data = s_p[0] + s_p[1]
    else:
        data = agrupa_datos(httptools.downloadpage(item.url).data)

    data = re.sub(
        r'<div class="span-6[^<]+<div class="item"[^<]+' + \
        '<a href="([^"]+)"[^<]+' + \
        '<img.*?src="([^"]+)".*?' + \
        '<div class="left"(.*?)</div>' + \
        '<div class="right"(.*?)</div>.*?' + \
        'title="([^"]+)".*?' + \
        'onclick="setFavorite.\d, (\d+),',
        r"'url':'\1';'image':'\2';'langs':'\3';'rating':'\4';'title':\5;'id':'\6';",
        data
    )

    patron = "'url':'([^']+)';'image':'([^']+)';'langs':'([^']+)';'rating':'([^']+)';'title':([^;]+);'id':'([^']+)';"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedlangs, scrapedrating, scrapedtitle, scrapedid in matches:

        thumbnail = scrapedthumbnail.replace("/tthumb/130x190/", "/thumbs/")
        language = ''
        title = scrapedtitle.strip()
        show = title
        contentTitle = scrapedtitle.strip()

        if scrapedlangs != ">":
            textoidiomas, language = extrae_idiomas(scrapedlangs)
            #Todo Quitar el idioma
            title += " ( [COLOR teal][B]" + textoidiomas + "[/B][/COLOR])"

        if scrapedrating != ">":
            valoracion = re.sub(r'><[^>]+>(\d+)<b class="dec">(\d+)</b>', r'\1,\2', scrapedrating)
            infoLabels['rating']=valoracion
            title += " ([COLOR orange]" + valoracion + "[/COLOR])"

        url = urlparse.urljoin(item.url, scrapedurl)

        if "/serie" in url or "/tags-tv" in url:
            action = "episodios"
            url += "###" + scrapedid + ";1"
            type = "shows"
            contentType = "tvshow"
        else:
            action = "findvideos"
            url += "###" + scrapedid + ";2"
            type = "movies"
            contentType = "movie"

        str = get_status(status, type, scrapedid)
        if str != "": title += str

        if item.title == "Buscar...":
            tag_type = scrapertools.get_match(url, 'l.tv/([^/]+)/')
            title += " - [COLOR blue]" + tag_type.capitalize() + "[/COLOR]"

        itemlist.append(
            Item(channel=item.channel, action=action, title=title, url=url, fulltitle=title, thumbnail=thumbnail,
                 show=show, folder=True, contentType=contentType, contentTitle=contentTitle,
                 language =language, infoLabels=infoLabels))

    ## Paginación
    next_page_url = scrapertools.find_single_match(data, '<a href="([^"]+)">.raquo;</a>')
    if next_page_url != "":
        itemlist.append(Item(channel=item.channel, action="fichas", title=">> Página siguiente",
                             url=urlparse.urljoin(item.url, next_page_url), folder=True))

    return itemlist


def episodios(item):
    logger.info()
    id = "0"
    itemlist = []

    ## Carga estados
    status = jsontools.load(httptools.downloadpage(host + '/a/status/all').data)

    url_targets = item.url

    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]

    ## Temporadas
    data = agrupa_datos(httptools.downloadpage(item.url).data)

    if id == "0":
        ## Se saca el id de la serie de la página cuando viene de listado_series
        id = scrapertools.get_match(data, "<script>var sid = '([^']+)';</script>")
        url_targets = url_targets.replace('###0', '###' + id)

    str = get_status(status, "shows", id)
    if str != "" and account and item.category != "Series" and "XBMC" not in item.title:
        if config.get_videolibrary_support():
            title = " ( [COLOR gray][B]" + item.show + "[/B][/COLOR] )"
            itemlist.append(
                Item(channel=item.channel, action="episodios", title=title, fulltitle=title, url=url_targets,
                     thumbnail=item.thumbnail, show=item.show, folder=False))
        title = str.replace('green', 'red').replace('Siguiendo', 'Abandonar')
        itemlist.append(Item(channel=item.channel, action="set_status", title=title, fulltitle=title, url=url_targets,
                             thumbnail=item.thumbnail, show=item.show, folder=True))
    elif account and item.category != "Series" and "XBMC" not in item.title:
        if config.get_videolibrary_support():
            title = " ( [COLOR gray][B]" + item.show + "[/B][/COLOR] )"
            itemlist.append(
                Item(channel=item.channel, action="episodios", title=title, fulltitle=title, url=url_targets,
                     thumbnail=item.thumbnail, show=item.show, folder=False))
        title = " ( [COLOR orange][B]Seguir[/B][/COLOR] )"
        itemlist.append(Item(channel=item.channel, action="set_status", title=title, fulltitle=title, url=url_targets,
                             thumbnail=item.thumbnail, show=item.show, folder=True))

    patron = "<li><a href='([^']+)'>[^<]+</a></li>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl in matches:

        ## Episodios
        data = agrupa_datos(httptools.downloadpage(scrapedurl).data)

        sid = scrapertools.get_match(data, "<script>var sid = '(\d+)'")
        ssid = scrapertools.get_match(scrapedurl, "temporada-(\d+)")
        post = "action=season&start=0&limit=0&show=%s&season=%s" % (sid, ssid)

        url = host + "/a/episodes"

        data = httptools.downloadpage(url, post=post).data

        episodes = jsontools.load(data)

        for episode in episodes:

            thumbnail = host + "/thumbs/" + episode['thumbnail']
            language = episode['languages']
            temporada = episode['season']
            episodio = episode['episode']
            if len(episodio) == 1: episodio = '0' + episodio

            if episode['languages'] != "[]":
                idiomas = "( [COLOR teal][B]"
                for idioma in episode['languages']: idiomas += idioma + " "
                idiomas += "[/B][/COLOR])"
                idiomas = idiomas
            else:
                idiomas = ""

            if episode['title']:
                try:
                    title = episode['title']['es'].strip()
                except:
                    title = episode['title']['en'].strip()

            if len(title) == 0: title = "Temporada " + temporada + " Episodio " + episodio

            try:
                title = temporada + "x" + episodio + " - " + title.decode('utf-8') + ' ' + idiomas
            except:
                title = temporada + "x" + episodio + " - " + title.decode('iso-8859-1') + ' ' + idiomas
            # try: title = temporada + "x" + episodio + " - " + title + ' ' + idiomas
            # except: pass
            # except: title = temporada + "x" + episodio + " - " + title.decode('iso-8859-1') + ' ' + idiomas

            str = get_status(status, 'episodes', episode['id'])
            if str != "": title += str

            try:
                title = title.encode('utf-8')
            except:
                title = title.encode('iso-8859-1')

            url = urlparse.urljoin(scrapedurl, 'temporada-' + temporada + '/episodio-' + episodio) + "###" + episode[
                'id'] + ";3"

            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url,
                                 thumbnail=thumbnail, show=item.show, folder=True, contentType="episode",
                                 language=language))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=url_targets,
                             action="add_serie_to_library", extra="episodios", show=item.show))
        itemlist.append(Item(channel=item.channel, title="Descargar todos los episodios de la serie", url=url_targets,
                             action="download_all_episodes", extra="episodios", show=item.show))

    return itemlist


def novedades_episodios(item):
    logger.info()

    itemlist = []
    ## Carga estados
    status = jsontools.load(httptools.downloadpage(host + '/a/status/all').data)

    ## Episodios
    url = item.url.split("?")[0]
    post = item.url.split("?")[1]

    old_start = scrapertools.get_match(post, 'start=([^&]+)&')
    start = "%s" % (int(old_start) + 24)

    post = post.replace("start=" + old_start, "start=" + start)
    next_page = url + "?" + post

    data = httptools.downloadpage(url, post=post).data

    episodes = jsontools.load(data)

    for episode in episodes:

        thumbnail = host + "/thumbs/" + episode['thumbnail']

        temporada = episode['season']
        episodio = episode['episode']
        if len(episodio) == 1: episodio = '0' + episodio

        if episode['languages'] != "[]":
            idiomas = "( [COLOR teal][B]"
            for idioma in episode['languages']: idiomas += idioma + " "
            idiomas += "[/B][/COLOR])"
            idiomas = idiomas
        else:
            idiomas = ""

        try:
            show = episode['show']['title']['es'].strip()
        except:
            show = episode['show']['title']['en'].strip()

        show = "[COLOR whitesmoke][B]" + show + "[/B][/COLOR]"

        if episode['title']:
            try:
                title = episode['title']['es'].strip()
            except:
                title = episode['title']['en'].strip()

        if len(title) == 0: title = "Temporada " + temporada + " Episodio " + episodio

        try:
            title = temporada + "x" + episodio + " - " + show.decode('utf-8') + ": " + title.decode(
                'utf-8') + ' ' + idiomas
        except:
            title = temporada + "x" + episodio + " - " + show.decode('iso-8859-1') + ": " + title.decode(
                'iso-8859-1') + ' ' + idiomas

        str = get_status(status, 'episodes', episode['id'])
        if str != "": title += str

        try:
            title = title.encode('utf-8')
        except:
            title = title.encode('iso-8859-1')
        # try: show = show.encode('utf-8')
        # except:  show = show.encode('iso-8859-1')

        url = urlparse.urljoin(host, '/serie/' + episode[
            'permalink'] + '/temporada-' + temporada + '/episodio-' + episodio) + "###" + episode['id'] + ";3"

        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, fulltitle=title, url=url, thumbnail=thumbnail,
                 folder=True, contentType="episode"))

    if len(itemlist) == 24:
        itemlist.append(
            Item(channel=item.channel, action="novedades_episodios", title=">> Página siguiente", url=next_page,
                 folder=True))

    return itemlist


def generos(item):
    logger.info()

    itemlist = []

    data = agrupa_datos(httptools.downloadpage(item.url).data)
    data = scrapertools.find_single_match(data, '<li class="dropdown"><a href="http://hdfull.tv/peliculas"(.*?)</ul>')

    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = ""
        plot = ""

        itemlist.append(Item(channel=item.channel, action="fichas", title=title, url=url, folder=True))

    return itemlist


def generos_series(item):
    logger.info()

    itemlist = []

    data = agrupa_datos(httptools.downloadpage(item.url).data)
    data = scrapertools.find_single_match(data, '<li class="dropdown"><a href="http://hdfull.tv/series"(.*?)</ul>')

    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = ""
        plot = ""

        itemlist.append(Item(channel=item.channel, action="fichas", title=title, url=url, folder=True))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    it1 = []
    it2 = []
    ## Carga estados
    status = jsontools.load(httptools.downloadpage(host + '/a/status/all').data)
    url_targets = item.url

    ## Vídeos
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]

    if type == "2" and account and item.category != "Cine":
        title = " ( [COLOR orange][B]Agregar a Favoritos[/B][/COLOR] )"
        if "Favorito" in item.title:
            title = " ( [COLOR red][B]Quitar de Favoritos[/B][/COLOR] )"
        if config.get_videolibrary_support():
            title_label = " ( [COLOR gray][B]" + item.show + "[/B][/COLOR] )"
            it1.append(Item(channel=item.channel, action="findvideos", title=title_label, fulltitle=title_label,
                                 url=url_targets, thumbnail=item.thumbnail, show=item.show, folder=False))

            title_label = " ( [COLOR green][B]Tráiler[/B][/COLOR] )"

            it1.append(
                item.clone(channel="trailertools", action="buscartrailer", title=title_label, contentTitle=item.show, url=item.url,
                     thumbnail=item.thumbnail, show=item.show))

        it1.append(Item(channel=item.channel, action="set_status", title=title, fulltitle=title, url=url_targets,
                             thumbnail=item.thumbnail, show=item.show, folder=True))

    data_js = httptools.downloadpage("http://hdfull.tv/templates/hdfull/js/jquery.hdfull.view.min.js").data
    key = scrapertools.find_single_match(data_js, 'JSON.parse\(atob.*?substrings\((.*?)\)')

    data_js = httptools.downloadpage("http://hdfull.tv/js/providers.js").data
    try:
        data_js = jhexdecode(data_js)
    except:
        from lib.aadecode import decode as aadecode
        data_js = data_js.split(";ﾟωﾟ")
        decode_aa = ""
        for match in data_js:
            decode_aa += aadecode(match)

        data_js = re.sub(r':(function.*?\})', r':"\g<1>"', decode_aa)
        data_js = re.sub(r':(var[^,]+),', r':"\g<1>",', data_js)

    data = agrupa_datos(httptools.downloadpage(item.url).data)
    data_obf = scrapertools.find_single_match(data, "var ad\s*=\s*'([^']+)'")
    data_decrypt = jsontools.load(obfs(base64.b64decode(data_obf), 126 - int(key)))

    infolabels = {}
    year = scrapertools.find_single_match(data, '<span>A&ntilde;o:\s*</span>.*?(\d{4})')
    infolabels["year"] = year
    matches = []
    for match in data_decrypt:
        prov = eval(scrapertools.find_single_match(data_js, 'p\[%s\]\s*=\s*(\{.*?\}[\'"]\})' % match["provider"]))
        function = prov["l"].replace("code", match["code"]).replace("var_1", match["code"])

        url = scrapertools.find_single_match(function, "return\s*(.*?)[;]*\}")
        url = re.sub(r'\'|"|\s|\+', '', url)
        url = re.sub(r'var_\d+\[\d+\]', '', url)
        embed = prov["e"]

        matches.append([match["lang"], match["quality"], url, embed])

    for idioma, calidad, url, embed in matches:
        mostrar_server = True
        option = "Ver"
        option1 = 1
        if re.search(r'return ([\'"]{2,}|\})', embed):
            option = "Descargar"
            option1 = 2
        calidad = unicode(calidad, "utf8").upper().encode("utf8")
        title = option + ": %s (" + calidad + ")" + " (" + idioma + ")"
        thumbnail = item.thumbnail
        plot = item.title + "\n\n" + scrapertools.find_single_match(data,
                                                                    '<meta property="og:description" content="([^"]+)"')
        plot = scrapertools.htmlclean(plot)
        fanart = scrapertools.find_single_match(data, '<div style="background-image.url. ([^\s]+)')
        if account:
            url += "###" + id + ";" + type

        it2.append(
            item.clone(channel=item.channel, action="play", title=title, url=url, thumbnail=thumbnail,
                 plot=plot, fanart=fanart, show=item.show, folder=True, infoLabels=infolabels,
                 contentTitle=item.title, contentType=item.contentType, tipo=option, tipo1=option1, idioma=idioma))

    it2 = servertools.get_servers_itemlist(it2, lambda i: i.title % i.server.capitalize())
    it2.sort(key=lambda it: (it.tipo1, it.idioma, it.server))
    itemlist.extend(it1)
    itemlist.extend(it2)
    ## 2 = película
    if type == "2" and item.category != "Cine":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=url_targets, thumbnail = item.thumbnail,
                                 fulltitle = item.contentTitle
                                 ))

    return itemlist



def play(item):
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]
        post = "target_id=%s&target_type=%s&target_status=1" % (id, type)
        data = httptools.downloadpage(host + "/a/status", post=post).data

    devuelve = servertools.findvideosbyserver(item.url, item.server)
    if devuelve:
        item.url = devuelve[0][1]
    else:
        devuelve = servertools.findvideos(item.url, True)
        if devuelve:
            item.url = devuelve[0][1]
            item.server = devuelve[0][2]
    item.thumbnail = item.contentThumbnail
    item.fulltitle = item.contentTitle
    return [item]


def agrupa_datos(data):
    ## Agrupa los datos
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|<!--.*?-->', '', data)
    data = re.sub(r'\s+', ' ', data)
    data = re.sub(r'>\s<', '><', data)
    return data


def extrae_idiomas(bloqueidiomas):
    logger.info("idiomas=" + bloqueidiomas)
    language=[]
    textoidiomas = ''
    patronidiomas = '([a-z0-9]+).png"'
    idiomas = re.compile(patronidiomas, re.DOTALL).findall(bloqueidiomas)
    for idioma in idiomas:
        # TODO quitar esto
        textoidiomas = textoidiomas + idioma +" "
        # TODO y dejar esto
        language.append(idioma)

    return textoidiomas, language


## --------------------------------------------------------------------------------

def set_status(item):
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        # item.url = item.url.split("###")[0]

    if "Abandonar" in item.title:
        path = "/a/status"
        post = "target_id=" + id + "&target_type=" + type + "&target_status=0"

    elif "Seguir" in item.title:
        target_status = "3"
        path = "/a/status"
        post = "target_id=" + id + "&target_type=" + type + "&target_status=3"

    elif "Agregar a Favoritos" in item.title:
        path = "/a/favorite"
        post = "like_id=" + id + "&like_type=" + type + "&like_comment=&vote=1"

    elif "Quitar de Favoritos" in item.title:
        path = "/a/favorite"
        post = "like_id=" + id + "&like_type=" + type + "&like_comment=&vote=-1"

    data = httptools.downloadpage(host + path, post=post).data

    title = "[COLOR green][B]OK[/B][/COLOR]"

    return [Item(channel=item.channel, action="episodios", title=title, fulltitle=title, url=item.url,
                 thumbnail=item.thumbnail, show=item.show, folder=False)]


def get_status(status, type, id):
    if type == 'shows':
        state = {'0': '', '1': 'Finalizada', '2': 'Pendiente', '3': 'Siguiendo'}
    else:
        state = {'0': '', '1': 'Visto', '2': 'Pendiente'}

    str = "";
    str1 = "";
    str2 = ""

    try:
        if id in status['favorites'][type]:
            str1 = " [COLOR orange][B]Favorito[/B][/COLOR]"
    except:
        str1 = ""

    try:
        if id in status['status'][type]:
            str2 = state[status['status'][type][id]]
            if str2 != "": str2 = "[COLOR green][B]" + state[status['status'][type][id]] + "[/B][/COLOR]"
    except:
        str2 = ""

    if str1 != "" or str2 != "":
        str = " (" + str1 + str2 + " )"

    return str


## --------------------------------------------------------------------------------
## --------------------------------------------------------------------------------


def jhexdecode(t):
    r = re.sub(r'_\d+x\w+x(\d+)', 'var_' + r'\1', t)
    r = re.sub(r'_\d+x\w+', 'var_0', r)

    def to_hx(c):
        h = int("%s" % c.groups(0), 16)
        if 19 < h < 160:
            return chr(h)
        else:
            return ""

    r = re.sub(r'(?:\\|)x(\w{2})', to_hx, r).replace('var ', '')

    f = eval(scrapertools.get_match(r, '\s*var_0\s*=\s*([^;]+);'))
    for i, v in enumerate(f):
        r = r.replace('[[var_0[%s]]' % i, "." + f[i])
        r = r.replace(':var_0[%s]' % i, ":\"" + f[i] + "\"")
        r = r.replace(' var_0[%s]' % i, " \"" + f[i] + "\"")
        r = r.replace('(var_0[%s]' % i, "(\"" + f[i] + "\"")
        r = r.replace('[var_0[%s]]' % i, "." + f[i])
        if v == "": r = r.replace('var_0[%s]' % i, '""')

    r = re.sub(r':(function.*?\})', r":'\g<1>'", r)
    r = re.sub(r':(var[^,]+),', r":'\g<1>',", r)

    return r


def obfs(data, key, n=126):
    chars = list(data)
    for i in range(0, len(chars)):
        c = ord(chars[i])
        if c <= n:
            number = (ord(chars[i]) + key) % n
            chars[i] = chr(number)

    return "".join(chars)
