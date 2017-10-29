# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from core import httptools
from core import jsontools
from core import scrapertools
from core.item import Item
from platformcode import platformtools, config, logger


__modo_grafico__ = config.get_setting('modo_grafico', 'animemovil')
__perfil__ = int(config.get_setting('perfil', "animemovil"))

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

host = "http://animemovil.com"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel, action="recientes", title="Episodios Recientes", thumbnail=item.thumbnail,
                         url=host, text_color=color1, contentType="tvshow", extra="recientes"))
    itemlist.append(Item(channel=item.channel, action="listado", title="Animes", thumbnail=item.thumbnail,
                         url="%s/_API/?src=animesRecientes&offset=0" % host, text_color=color1))
    itemlist.append(Item(channel=item.channel, action="emision", title="En emisión", thumbnail=item.thumbnail,
                         url="%s/anime/emision" % host, text_color=color2, contentType="tvshow"))
    itemlist.append(Item(channel=item.channel, action="indices", title="Índices", thumbnail=item.thumbnail,
                         text_color=color2))


    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail=item.thumbnail, text_color=color3))

    itemlist.append(item.clone(title="Configurar canal", action="openconfig", text_color=color5, folder=False))
    if renumbertools.context:
        itemlist = renumbertools.show_option(item.channel, itemlist)
    return itemlist


def openconfig(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    item.url = "%s/?s=%s" % (host, texto.replace(" ", "+"))
    try:
        return recientes(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def recientes(item):
    logger.info()
    item.contentType = "tvshow"
    itemlist = []

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<ul class="emision"(.*?)</ul>')
    patron = '<li><a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title, thumb in matches:
        url = host + url

        try:
            contentTitle = re.split(r"(?i) \d+ (?:Sub Español|Audio Español|Español Latino)", title)[0]
        except:
            contentTitle = ""
        contentTitle = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub| Español| Peliculas| Audio| Latino", "", contentTitle)

        tipo = "tvshow"
        show = contentTitle
        action = "episodios"
        context = renumbertools.context
        if item.extra == "recientes":
            action = "findvideos"
            context = ""
        if not item.extra and (url.endswith("-pelicula/") or url.endswith("-pelicula")):
            tipo = "movie"
            show = ""
            action = "peliculas"
        if not thumb.startswith("http"):
            thumb = "http:%s" % thumb
        
        infoLabels = {'filtro': {"original_language": "ja"}.items()}
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumb, text_color=color3,
                                   contentTitle=contentTitle, contentSerieName=show, infoLabels=infoLabels,
                                   thumb_=thumb, contentType=tipo, context=context))

    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        if item.extra and itemlist:
            for it in itemlist:
                it.thumbnail = it.thumb_
    except:
        pass

    return itemlist


def listado(item):
    logger.info()
    itemlist = []

    data = jsontools.load(httptools.downloadpage(item.url).data)

    for it in data.get("items", []):
        scrapedtitle = it["title"]
        url = "%s/%s" % (host, it["url"])
        thumb = "http://img.animemovil.com/w440-h250-c/%s" % it["img"]
        title = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub| Español| Peliculas| Audio| Latino", "", scrapedtitle)

        tipo = "tvshow"
        show = title
        action = "episodios"
        if url.endswith("-pelicula/") or url.endswith("-pelicula"):
            tipo = "movie"
            show = ""
            action = "peliculas"
        
        infoLabels = {'filtro': {"original_language": "ja"}.items()}

        itemlist.append(item.clone(action=action, title=scrapedtitle, url=url, thumbnail=thumb, text_color=color3,
                                   contentTitle=title, contentSerieName=show, infoLabels=infoLabels,
                                   context=renumbertools.context(item), contentType=tipo))
            
    
    try:
        from core import tmdb
        tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    except:
        pass

    if data["buttom"] and itemlist:
        offset = int(scrapertools.find_single_match(item.url, 'offset=(\d+)')) + 1
        url = re.sub(r'offset=\d+', 'offset=%s' % offset, item.url)
        itemlist.append(Item(channel=item.channel, action="listado", url=url, title=">> Página Siguiente",
                             thumbnail=item.thumbnail, text_color=color2))

    return itemlist


def indices(item):
    logger.info()
    itemlist = []
    
    if "Índices" in item.title:
        itemlist.append(item.clone(title="Por Género", url="%s/anime/generos/" % host))
        itemlist.append(item.clone(title="Por Letra", url="%s/anime/" % host))
        itemlist.append(item.clone(action="completo", title="Lista completa de Animes",
                        url="%s/anime/lista/" % host))
    else:
        data = httptools.downloadpage(item.url).data
        bloque = scrapertools.find_single_match(data, '<div class="letras">(.*?)</div>')

        patron = '<a title="([^"]+)"'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for title in matches:
            if "Letra" in item.title:
                url = "%s/_API/?src=animesLetra&offset=0&letra=%s" % (host, title)
            else:
                url = "%s/_API/?src=animesGenero&offset=0&genero=%s" % (host, title)
            itemlist.append(item.clone(action="listado", url=url, title=title))
        
    return itemlist


def completo(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<ul class="listadoAnime">(.*?)</ul>')
    patron = '<li><a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title, thumb in matches:
        url = host + url
        scrapedtitle = title
        thumb = thumb.replace("s90-c", "w440-h250-c")
        title = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub Español| Peliculas", "", scrapedtitle)

        tipo = "tvshow"
        show = title
        action = "episodios"
        if url.endswith("-pelicula/") or url.endswith("-pelicula"):
            tipo = "movie"
            show = ""
            action = "peliculas"
        infoLabels = {'filtro': {"original_language": "ja"}.items()}
        itemlist.append(Item(channel=item.channel, action=action, title=scrapedtitle, url=url, thumbnail=thumb,
                             text_color=color3, contentTitle=title, contentSerieName=show, extra="completo",
                             context=renumbertools.context(item), contentType=tipo, infoLabels=infoLabels))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data

    show = scrapertools.find_single_match(data, '<title>\s*([^<]+)\s*</title>')
    show = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub| Español| Peliculas| Audio| Latino", "", show)
    
    if not item.infoLabels["plot"]:
        item.infoLabels["plot"] = scrapertools.find_single_match(data, '<div class="InfoSipnosis">.*?<p>(.*?)</p>')

    bloque = scrapertools.find_single_match(data, 'ul class="lista"(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(bloque, '<li><a href="([^"]+)" title="([^"]+)"')
    for url, title in matches:
        url = host + url
        epi = scrapertools.find_single_match(title, '(?i)%s.*? (\d+) (?:Sub|Audio|Español)' % item.contentSerieName)
        new_item = item.clone(action="findvideos", url=url, title=title, extra="")
        if epi:
            season, episode = renumbertools.numbered_for_tratk(
                item.channel, show, 1, int(epi))
            new_item.infoLabels["episode"] = episode
            new_item.infoLabels["season"] = season

            new_item.title = "%sx%s %s" % (season, episode, title)
        itemlist.append(new_item)

    if item.infoLabels.get("tmdb_id") or item.extra == "recientes" or item.extra == "completo":
        try:
            from core import tmdb
            tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
        except:
            pass

    if config.get_videolibrary_support() and itemlist:
        itemlist.append(Item(channel=item.channel, title="Añadir serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", contentTitle=item.contentTitle,
                             contentSerieName=item.contentSerieName, text_color=color4, fanart=item.fanart,
                             thumbnail=item.thumbnail))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    if item.extra == "completo":
        try:
            from core import tmdb
            tmdb.set_infoLabels_item(item, __modo_grafico__)
        except:
            pass

    data = httptools.downloadpage(item.url).data
    if not item.infoLabels["plot"]:
        item.infoLabels["plot"] = scrapertools.find_single_match(data, '<div class="InfoSipnosis">.*?<p>(.*?)</p>')

    bloque = scrapertools.find_single_match(data, 'ul class="lista"(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(bloque, '<li><a href="([^"]+)" title="([^"]+)"')
    if len(matches) == 1:
        item.url = host + matches[0][0]
        itemlist = findvideos(item)
    else:
        for url, title in matches:
            itemlist.append(item.clone(action="findvideos", title=title, url=url, extra=""))

    return itemlist


def emision(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    bloques = scrapertools.find_multiple_matches(data, '<div class="horario">.*?</i>\s*(.*?)</span>(.*?)</ul>')
    patron = '<li><a href="([^"]+)" title="([^"]+)".*?src="([^"]+)"'
    for dia, b in bloques:
        matches = scrapertools.find_multiple_matches(b, patron)
        if matches:
            itemlist.append(item.clone(action="", title=dia, text_color=color1))
        for url, title, thumb in matches:
            url = host + url
            scrapedtitle = "    %s" % title
            title = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub Español| Peliculas", "", title)
            if not thumb.startswith("http"):
                thumb = "http:%s" % thumb

            infoLabels = {'filtro': {"original_language": "ja"}.items()}
            itemlist.append(item.clone(action="episodios", title=scrapedtitle, url=url, thumbnail=thumb, text_color=color3,
                                       contentTitle=title, contentSerieName=title, extra="recientes",
                                       context=renumbertools.context(item), infoLabels=infoLabels))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    id = scrapertools.find_single_match(data, '"id":"([^"]+)"')
    bloque = scrapertools.find_single_match(data, 'ul class="controles">(.*?)</ul>')
    patron = '<li title="([^"]+)" id="[^"]*" host="([^"]+)">'
    matches = scrapertools.find_multiple_matches(data, patron)
    for title, server in matches:
        if title == "Vizard":
            continue
        title = "%s - %s" % (title, item.title)
        post = "host=%s&id=%s" % (server, id)
        itemlist.append(item.clone(action="play", url="http://server-2-stream.animemovil.com/V2/", title=title,
                                   post=post))

    downl = scrapertools.find_single_match(data, '<div class="descargarCap">.*?<a href="([^"]+)"')
    if downl:
        downl = downl.replace("&amp;", "&")
        itemlist.append(item.clone(action="play", title="Descarga - %s" % item.title, url=downl, server="directo"))
                
    if not itemlist:
        itemlist.append(Item(channel=item.channel, title="No hay vídeos disponibles", action=""))
    if item.extra == "recientes":
        url = scrapertools.find_single_match(data, '<a class="CapList".*?href="([^"]+)"')
        if url:
            url = host + url
            itemlist.append(item.clone(action="episodios", title="Ir a lista de capítulos", url=url, text_color=color1))
    elif item.contentType == "movie" and config.get_library_support():
        if "No hay vídeos disponibles" not in itemlist[0].title:
            itemlist.append(Item(channel=item.channel, title="Añadir película a la biblioteca", url=item.url,
                                 action="add_pelicula_to_library", contentTitle=item.contentTitle, text_color=color4,
                                 thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist


def play(item):
    logger.info()

    if item.server:
        return [item]

    itemlist = []

    data = jsontools.load(httptools.downloadpage(item.url, item.post).data)
    if data["jwplayer"] == False:
        content = data["eval"]["contenido"]
        urls = scrapertools.find_multiple_matches(content, 'file\s*:\s*"([^"]+)"')
        if not urls:
            urls = scrapertools.find_multiple_matches(content, '"GET","([^"]+)"')    
        for url in urls:
            if "mediafire" in url:
                data_mf = httptools.downloadpage(url).data
                url = scrapertools.find_single_match(data_mf, 'kNO\s*=\s*"([^"]+)"')
            ext = url[-4:]
            itemlist.insert(0, ["%s [directo]" % ext, url])
    else:
        if data["jwplayer"].get("sources"):
            for source in data["jwplayer"]["sources"]:
                label = source.get("label", "")
                ext = source.get("type", "")
                if ext and "/" in ext:
                    ext = ".%s " % ext.rsplit("/", 1)[1]
                url = source.get("file")
                if "server-3-stream" in url:
                    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location")
                itemlist.insert(0, ["%s%s [directo]" % (ext, label), url])
        elif data["jwplayer"].get("file"):
            label = data["jwplayer"].get("label", "")
            url = data["jwplayer"]["file"]
            ext = data["jwplayer"].get("type", "")
            if ext and "/" in ext:
                ext = "%s " % ext.rsplit("/", 1)[1]
            if "server-3-stream" in url:
                url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location")
            itemlist.insert(0, [".%s%s [directo]" % (ext, label), url])

    return itemlist


def newest(categoria):
    logger.info()
    item = Item()
    try:
        item.url = "http://skanime.net/"
        item.extra = "novedades"
        itemlist = recientes(item)
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
