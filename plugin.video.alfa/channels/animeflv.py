# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import renumbertools
from core import httptools
from core import jsontools
from core import servertools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools

IDIOMAS = {'LAT': 'LAT','SUB': 'VOSE'}
list_language = list(IDIOMAS.values())
list_servers = ['directo', 'rapidvideo', 'streamango', 'yourupload', 'mailru', 'netutv', 'okru']
list_quality = ['default']

clone = False
# clone = config.get_setting("use_clone", channel="animeflv")
# from lib import alfa_assistant
# if alfa_assistant.is_alfa_installed():
    # clone = True
OGHOST = "https://www3.animeflv.net/"
CLONEHOST = "https://www10.animeflv.cc/"
if clone:
    HOST = CLONEHOST
else:
    HOST = OGHOST


def mainlist(item):
    logger.info()
    if clone:
        order = '3'
    else:
        order = 'title'

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios",
                         url=HOST, thumbnail="https://i.imgur.com/w941jbR.png"))
    
    itemlist.append(Item(channel=item.channel, action="novedades_anime", title="Últimos animes",
                         url=HOST, thumbnail="https://i.imgur.com/hMu5RR7.png"))
    
    itemlist.append(Item(channel=item.channel, action="listado", title="Animes",
                         url=HOST + "browse?order=%s" % order, thumbnail='https://i.imgur.com/50lMcjW.png'))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Género",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/Xj49Wa7.png',
                         extra="genre"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Tipo",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/0O5U8Y0.png',
                         extra="type"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Año",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/XzPIQBj.png',
                         extra="year"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Estado",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/7LKKjSN.png',
                         extra="status"))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail='https://i.imgur.com/4jH5gpT.png'))
    
    itemlist = renumbertools.show_option(item.channel, itemlist)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def get_source(url, patron=None):

    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    
    if patron:
        data = scrapertools.find_single_match(data, patron)

    return data


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "+")
    post = "value=%s&limit=100" % texto

    if clone:
        item.url = "{}browse?q={}".format(HOST, texto)
    else:
        item.url = urlparse.urljoin(HOST, "api/animes/search")

    try:
        if clone:
            response = httptools.downloadpage(item.url).data
            response = scrapertools.find_single_match(response, 'class="ListAnimes.+?</ul>')
            patron = '(?is)article class.+?a href="(.+?)".+?img src="(.+?)".+?class="type.+?>(.+?)<.+?class="Title".*?>(.+?)<.+?class="des".*?>(.+?)</p'
            matches = scrapertools.find_multiple_matches(response, patron)
            for url, thumb, _type, title, plot in matches:
                _type = _type.lower()
                url = urlparse.urljoin(HOST, url)
                it = Item(
                        action = "episodios",
                        contentType = "tvshow",
                        channel = item.channel,
                        plot = plot,
                        thumbnail = thumb,
                        title = title,
                        url = url
                    )
                if "película" in _type:
                    it.contentType = "movie"
                    it.contentTitle = title
                else:
                    it.contentSerieName = title
                    it.context = renumbertools.context(item)
                itemlist.append(it)
        else:
            dict_data = httptools.downloadpage(item.url, post=post).json
            for e in dict_data:
                if e["id"] != e["last_id"]:
                    _id = e["last_id"]
                else:
                    _id = e["id"]
                url = "%sanime/%s/%s" % (HOST, _id, e["slug"])
                title = e["title"]
                #if "&#039;" in title:
                #    title = title.replace("&#039;","")
                #if "&deg;" in title:
                #    title = title.replace("&deg;","")
                thumbnail = "%suploads/animes/covers/%s.jpg" % (HOST, e["id"])
                new_item = item.clone(action="episodios", title=title, url=url, thumbnail=thumbnail)
                if e["type"] != "movie":
                    new_item.contentSerieName = title
                    new_item.context = renumbertools.context(item)
                else:
                    new_item.contentType = "movie"
                    new_item.contentTitle = title
                itemlist.append(new_item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def search_section(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)

    if clone:
        repls = {'genre': 'genres', 'year': 'year', 'type': 'Tipo', 'status': 'status', 'order': 'order'}
        item.extra = repls[item.extra]
        patron = '<span class="mu.+?b>(.+?)</.+?dropdown-menu(.+?)</ul'
        data = scrapertools.find_multiple_matches(data, patron)
        order = '3'
        for _type, selections_list in data:
            _type = _type.lower()
            logger.info('extra: {}, _type: {}'.format(item.extra, _type))
            if 'genero' in _type and 'genre' in item.extra:
                matches = scrapertools.find_multiple_matches(selections_list, 'value="([^"]+)".+?>\s+(.*?)</label>')
            elif 'año' in _type and 'year' in item.extra:
                matches = scrapertools.find_multiple_matches(selections_list, 'value="([^"]+)".+?>\s+(.*?)</label>')
            elif 'tipo' in _type and item.extra in ['type', 'Tipo']:
                matches = scrapertools.find_multiple_matches(selections_list, 'value="([^"]+)".+?>\s+(.*?)</label>')
            elif 'estado' in _type and 'status' in item.extra:
                matches = scrapertools.find_multiple_matches(selections_list, 'value="([^"]+)".+?>\s+(.*?)</label>')
            elif 'orden' in _type and 'order' in item.extra:
                matches = scrapertools.find_multiple_matches(selections_list, 'value="([^"]+)".+?>\s+(.*?)</label>')
    else:
        patron = 'id="{}_select"[^>]+>(.*?)</select>'.format(item.extra)
        matches = re.compile('<option value="([^"]+)">(.*?)</option>', re.DOTALL).findall(data)
        order = 'title'

    for _id, title in matches:
        url = "{}?{}={}&order={}".format(item.url, item.extra, _id, order)
        
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url,
                             context=renumbertools.context(item)))
    return itemlist


def newest(categoria):
    itemlist = []
    if categoria == 'anime':
        itemlist = novedades_episodios(Item(url=HOST))
    return itemlist


def novedades_episodios(item):
    logger.info()
    itemlist = []

    patr = '<h2>Últimos episodios</h2>.+?<ul class="ListEpisodios[^>]+>(.*?)</ul>'
    data = get_source(item.url, patron=patr)
    
    patron = '<a href="([^"]+)"[^>]+>.+?<img src="([^"]+)".+?"Capi">(.*?)</span>'
    patron += '<strong class="Title">(.*?)</strong>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumbnail, str_episode, show in matches:
        try:
            episode = int(str_episode.replace("Episodio ", ""))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)

        title = "%s: %sx%s" % (show, season, str(episode).zfill(2))
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)

        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url,
                        contentSerieName=show, thumbnail=thumbnail)

        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def novedades_anime(item):
    logger.info()
    itemlist = []
    
    patr = '<ul class="ListAnimes[^>]+>(.*?)</ul>'
    data = get_source(item.url, patron=patr)
    

    patron = 'href="([^"]+)".+?<img src="([^"]+)".+?'
    patron += '<span class=.+?>(.*?)</span>.+?<h3.+?>(.*?)</h3>.+?'
    patron += '(?:</p><p>(.*?)</p>.+?)?</article></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumbnail, _type, title, plot in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        plot=plot)
        
        if _type != "Película":
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    
    data = get_source(item.url)

    if clone:
        url_pagination = scrapertools.find_single_match(data, "(?is)<li\s*?class=selected>.*?</li><li.*?><a href='([^']+)'")
    else:
        url_pagination = scrapertools.find_single_match(data, '<li class="active">.*?</li><li><a href="([^"]+)">')
    logger.info(url_pagination)

    data = scrapertools.find_multiple_matches(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')
    data = "".join(data)
    
    if clone:
        patron = '(?is)<a href="([^"]+)">.+?<img src="([^"]+)".+?<span class=.+?>(.*?)</span>.+?<h3.*?>(.*?)</h3>.*?<p class="des">(.*?)</p>'
        matches = scrapertools.find_multiple_matches(data, patron)
    else:
        matches = re.compile('<a href="([^"]+)">.+?<img src="([^"]+)".+?<span class=.+?>(.*?)</span>.+?<h3.*?>(.*?)</h3>'
                             '.*?</p><p>(.*?)</p>', re.DOTALL).findall(data)


    for url, thumbnail, _type, title, plot in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        plot=plot)
        
        if _type == "Anime":
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        
        itemlist.append(new_item)
    
    if url_pagination:
        if clone:
            url = urlparse.urljoin(HOST, '/browse{}'.format(url_pagination))
        else:
            url = urlparse.urljoin(HOST, url_pagination)
        title = ">> Pagina Siguiente"
        
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    
    if clone and OGHOST in item.url:
        item.url = item.url.replace(OGHOST, HOST)
    data = get_source(item.url)
    
    if clone:
        data = scrapertools.find_single_match(data, '<ul class="ListCaps".+?>(.+?)</ul')
        patron = '(?is)href="(.+?)".+?\ssrc="(.+?)".+?class="title.+?p>.+?(\d+).*?</.+?'
        episodes = scrapertools.find_multiple_matches(data, patron)
        
        for url, thumb, epnum in episodes:
            season = 1
            season, episodeRenumber = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, season, int(epnum))
            title = '{}x{} Episodio {}'.format(season, str(episodeRenumber).zfill(2), episodeRenumber)
            url = urlparse.urljoin(HOST, url)

            infoLabels = item.infoLabels
            infoLabels['season'] = season
            infoLabels['episode'] = episodeRenumber

            itemlist.append(
                item.clone(
                    action = "findvideos",
                    channel = item.channel,
                    infoLabels = infoLabels,
                    thumbnail = thumb,
                    title = title,
                    url = url
                )
            )
    else:
        info = scrapertools.find_single_match(data, "anime_info = \[(.*?)\];")
        info = eval(info)
        
        episodes = eval(scrapertools.find_single_match(data, "var episodes = (.*?);"))
        
        infoLabels = item.infoLabels

        for episode in episodes:
            url = '{}/ver/{}/{}-{}'.format(HOST, episode[1], info[2], episode[0])
            season = 1
            season, episodeRenumber = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, season, int(episode[0]))

            infoLabels['season'] = season
            infoLabels['episode'] = episodeRenumber
            
            title = '{}x{} Episodio {}'.format(season, str(episodeRenumber).zfill(2), episodeRenumber)
            
            itemlist.append(item.clone(title=title, url=url, action='findvideos', 
                                        contentSerieName=item.contentSerieName, infoLabels=infoLabels))
        
        if not item.extra:
            itemlist = itemlist[::-1]

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    itemlist = sorted(itemlist, key=lambda it: it.title)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.action == 'add_serie_to_library' and not item.extra:
        itemlist.append(Item(channel=item.channel, title=config.get_localized_string(60352), url=item.url,
                             action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def findvideos(item):
    logger.info()
    
    from core import jsontools
    itemlist = []
    
    if clone and OGHOST in item.url:
        item.url = item.url.replace(OGHOST, "")
        item.url = "{}{}".format(HOST, scrapertools.find_single_match(item.url, 'ver/\d+/(.+)'))
    elif not clone and CLONEHOST in item.url:
        item.url = item.url.replace(CLONEHOST, "")
        item.url = "{}ver/{}".format(HOST, item.url)
    data = get_source(item.url)

    if clone:
        data = scrapertools.find_single_match(data, 'class="CapiTnv nav nav-pills anime_muti_link"(.+?)class="CapiTcn-tab-content"')
        videos = scrapertools.find_multiple_matches(data, 'data-video="(.+?)" title="(.+?)"')

        for url, server in videos:
            if not server in ['Our Server', 'Xstreamcdn', 'Animeid', 'Openupload']:
                itemlist.append(
                    Item(
                        action = 'play',
                        channel = item.channel,
                        infoLabels = item.infoLabels,
                        title = '{}'.format(server.title()),
                        url = url
                    )
                )

        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title)
    else:
        videos = scrapertools.find_single_match(data, 'var videos = (.*?);')
    
        videos_json = jsontools.load(videos)
        
        for video_lang in list(videos_json.items()):
            language = IDIOMAS.get(video_lang[0], video_lang[0])
            matches = scrapertools.find_multiple_matches(str(video_lang[1]), "code': '(.*?)'")
            
            lang = " [COLOR=grey](%s)[/COLOR]" % language
            for source in matches:
                
                url = source
                if 'redirector' in source:
                    new_data = httptools.downloadpage(source).data
                    url = scrapertools.find_single_match(new_data, 'window.location.href = "([^"]+)"')
                elif 'animeflv.net/embed' in source or 'gocdn.html' in source:
                    source = source.replace('embed', 'check').replace('gocdn.html#', 'gocdn.php?v=')
                    json_data = httptools.downloadpage(source).json
                    url = json_data.get('file', '')
                
                url = url.replace('embedsito', 'fembed')

                itemlist.append(Item(channel=item.channel, url=url, title='%s'+lang, 
                                    action='play', infoLabels=item.infoLabels, language=language))

        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
