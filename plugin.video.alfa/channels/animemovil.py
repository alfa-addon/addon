# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from core import httptools
from core import servertools
from core import jsontools
from core import scrapertools
from core.item import Item
from platformcode import platformtools, config, logger


__modo_grafico__ = config.get_setting('modo_grafico', 'animemovil')
__perfil__ = ''

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

    itemlist.append(Item(channel=item.channel, action="listado", title="Anime", thumbnail=item.thumbnail,
             url=host+'/api/buscador?q=&letra=ALL&genero=ALL&estado=2&offset=0&limit=20', text_color=color1, contentType="tvshow", extra="recientes"))

    itemlist.append(Item(channel=item.channel, action="list_by_json", title="En emisión", thumbnail=item.thumbnail,
                         text_color=color2, contentType="tvshow"))
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
    item.url = "%s/api/buscador?q=%s&letra=ALL&genero=ALL&estado=2&offset=0&limit=30" % (host, texto.replace(" ", "+"))
    return list_by_json(item)


def recientes(item):
    logger.info()
    item.contentType = "tvshow"
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\s{2,}','', data)

    bloque = scrapertools.find_single_match(data, '<ul class="hover">(.*?)</ul>')
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
        context = renumbertools.context(item)
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
    status = data.get('status')
    data= data.get('result')
    for it in data.get("items", []):
        scrapedtitle = it["title"]
        url = "%s/%s/" % (host, it["slug"])
        thumb = 'http://media.animemovil.com/animes/%s/wallpaper_small.jpg' % it['id']
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

    if status and itemlist:
        offset = scrapertools.find_single_match(item.url, 'offset=(\d+)')
        if offset:
            offset = int(offset) + 2
        else:
            offset = 0
        url = re.sub(r'offset=\d+', 'offset=%s' % offset, item.url)
        itemlist.append(Item(channel=item.channel, action="listado", url=url, title=">> Página Siguiente",
                             thumbnail=item.thumbnail, text_color=color2))

    return itemlist


def indices(item):
    logger.info()
    itemlist = []
    
    if "Índices" in item.title:
        itemlist.append(item.clone(title="Por Género", url="%s/anime" % host))
        itemlist.append(item.clone(title="Por Letra", url="%s/anime" % host))
        itemlist.append(item.clone(action="list_by_json", title="Lista completa de Animes",
                        url="%s/api/buscador?q=&letra=ALL&genero=ALL&estado=2&offset=0&limit=20" % host))
    else:
        data = httptools.downloadpage(item.url).data
        data = re.sub('\n|\s{2,}', '', data)
        if 'Letra' in item.title:
            bloque = scrapertools.find_single_match(data, '<select name="letra"(.*?)</select>')
            patron = '<option value="(\w)"'
        elif 'Género' in item.title:
            bloque = scrapertools.find_single_match(data, '<select name="genero"(.*?)</select>')
            patron = '<option value="(\d+.*?)/'

        matches = scrapertools.find_multiple_matches(bloque, patron)

        for title in matches:
            if "Letra" in item.title:
                url = '%s/api/buscador?q=&letra=%s&genero=ALL&estado=2&offset=0&limit=20' % (host, title)
            else:
                value = scrapertools.find_single_match(title, '(\d+)"')
                title = scrapertools.find_single_match(title, '\d+">(.*?)<')
                url = '%s/api/buscador?q=&letra=ALL&genero=%s&estado=2&offset=0&limit=20' % (host, value)

            itemlist.append(item.clone(action="list_by_json", url=url, title=title))
        
    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub('\n|\s{2,}', '', data)
    show = scrapertools.find_single_match(data, '<div class="x-title">(.*?)</div>')
    show = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub| Español| Peliculas| Audio| Latino", "", show)
    
    if not item.infoLabels["plot"]:
        item.infoLabels["plot"] = scrapertools.find_single_match(data, '<div class="x-sinopsis">\s*(.*?)</div>')

    bloque = scrapertools.find_single_match(data, '<ul class="list"(.*?)</ul>')
    matches = scrapertools.find_multiple_matches(bloque, '<li><a href="([^"]+)" title="([^"]+)"')
    for url, title in matches:
        url = host + url
        epi = scrapertools.find_single_match(title, '.+?(\d+) (?:Sub|Audio|Español)')
        #epi = scrapertools.find_single_match(title, '(?i)%s.*? (\d+) (?:Sub|Audio|Español)' % item.contentSerieName)
        new_item = item.clone(action="findvideos", url=url, title=title, extra="")
        if epi:
            if "Especial" in title:
                epi=0
            season, episode = renumbertools.numbered_for_tratk(
                item.channel, item.contentSerieName, 1, int(epi))
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


def list_by_json(item):
    logger.info()
    itemlist = []
    repeat = 1
    status = False
    if item.url =='':
        item.url = host+"/api/buscador?limit=30&estado=1&dia=%s"
        repeat = 6
    for element in range(0,repeat):
        if repeat != 1:
            data = jsontools.load(httptools.downloadpage(item.url % element).data)
        else:
            data = jsontools.load(httptools.downloadpage(item.url).data)

        status = data.get('status')
        json_data = data.get('result')
        elem_data = json_data['items']

        for item_data in elem_data:
            url = '%s/%s/' % (host, item_data['slug'])
            title = item_data['title']
            title = re.sub(r"(?i) Ova| Especiales| \(Pelicula[s]*\)| \(Película[s]*\)| Sub Español| Peliculas", "",
                           title)
            thumb = 'http://media.animemovil.com/animes/%s/wallpaper_small.jpg' % item_data['id']
            infoLabels = {'filtro': {"original_language": "ja"}.items()}
            itemlist.append(
                item.clone(action="episodios", title=title, url=url, thumbnail=thumb, text_color=color3,
                           contentTitle=title, contentSerieName=title, extra="recientes",
                           context=renumbertools.context(item), infoLabels=infoLabels))
    if status and itemlist:
        offset = scrapertools.find_single_match(item.url, 'offset=(\d+)')
        if offset:
            offset = int(offset) + 2
        else:
            offset = 0
        url = re.sub(r'offset=\d+', 'offset=%s' % offset, item.url)
        itemlist.append(Item(channel=item.channel, action="listado", url=url, title=">> Página Siguiente",
                             thumbnail=item.thumbnail, text_color=color2))
    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\s{2,}', '', data)

    akiba_url = scrapertools.find_single_match(data, '<div class="x-link"><a href="(.*?)"')
    url = httptools.downloadpage('http:'+akiba_url, follow_redirects=False).headers.get('location')
    title = '%s (%s)' % (item.title, 'akiba')
    itemlist.append(item.clone(title=title, url=url, action='play'))

    info = scrapertools.find_single_match(data, 'episodio_info=(.*?);')
    dict_info = jsontools.load(info)

    servers = dict_info['stream']['servers']
    id = dict_info['id']
    access_point = dict_info['stream']['accessPoint']
    expire = dict_info['stream']['expire']
    callback = dict_info['stream']['callback']
    signature = dict_info['stream']['signature']
    last_modify = dict_info['stream']['last_modify']

    for server in servers:
        stream_info = 'http:%s/%s/%s?expire=%s&callback=%s&signature=%s&last_modify=%s' % \
                      (access_point, id, server, expire, callback, signature, last_modify)

        try:
            dict_stream = jsontools.load(httptools.downloadpage(stream_info).data)
            if dict_stream['status']:
                kind = dict_stream['result']['kind']
                if kind == 'iframe':
                    url = dict_stream['result']['src']
                    title = '%s (%s)' % (item.title, server)
                elif kind == 'jwplayer':
                    url_style = dict_stream['result']['setup']
                    if server != 'rin':

                        if 'playlist' in url_style:
                            part = 1
                            for media_list in url_style['playlist']:
                                url = media_list['file']
                                title = '%s (%s) - parte %s' % (item.title, server, part)
                                itemlist.append(item.clone(title=title, url=url, action='play'))
                                part += 1
                        else:
                            url = url_style['file']
                            title = '%s (%s)' % (item.title, server)
                    else:
                        src_list = url_style['sources']
                        for source in src_list:
                            url = source['file']
                            quality = source['label']
                            title = '%s [%s](%s)' % (item.title, quality, server)
                            itemlist.append(item.clone(title=title, url=url, action='play'))

                elif kind == 'javascript':
                    if 'jsCode' in dict_stream['result']:
                        jscode = dict_stream['result']['jsCode']
                        url = scrapertools.find_single_match(jscode, 'xmlhttp.open\("GET", "(.*?)"')
                        title = '%s (%s)' % (item.title, server)

                if url != '':
                    itemlist.append(item.clone(title=title, url=url, action='play'))
        except:
            pass
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def newest(categoria):
    logger.info()
    item = Item()
    try:
        item.url = host
        item.extra = "novedades"
        itemlist = recientes(item)
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
