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
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import logger
from channels import autoplay
from lib import alfa_assistant

IDIOMAS = {'VOSE': 'VOSE'}
list_language = list(IDIOMAS.values())
list_servers = ['directo']
list_quality = ['default']


HOST = "https://animeflv.ac/"


def mainlist(item):
    logger.info()

    itemlist = list()

    if alfa_assistant.is_alfa_installed():

        autoplay.init(item.channel, list_servers, list_quality)

        itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios",
                             url=HOST+'anime-online.html', thumbnail="https://i.imgur.com/w941jbR.png"))

        itemlist.append(Item(channel=item.channel, action="novedades_anime", title="Últimos animes",
                             url=HOST+'anime-online.html', thumbnail="https://i.imgur.com/hMu5RR7.png"))

        itemlist.append(Item(channel=item.channel, action="listado", title="Animes",
                             url=HOST + "animes/nombre/lista", thumbnail='https://i.imgur.com/50lMcjW.png'))

        itemlist.append(Item(channel=item.channel, action="search_section",
                             title="Géneros", url=HOST + "animes",
                             extra="genre", thumbnail='https://i.imgur.com/Xj49Wa7.png'))

        itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                             thumbnail='https://i.imgur.com/4jH5gpT.png'))


        itemlist = renumbertools.show_option(item.channel, itemlist)

        autoplay.show_option(item.channel, itemlist)
    else:
        from lib import generictools
        browser, res = generictools.call_browser('', lookup=True)
        if not browser:
            action = ''
        else:
            action = 'call_browser'
        from channelselector import get_thumb
        from core import channeltools
        channel_name = channeltools.get_channel_parameters(item.channel)["title"]
        itemlist.append(Item(channel=item.channel, action=action, title="Para utilizar {} se requiere Alfa Assistant. [COLOR=yellow]Haz clic para + info[/COLOR] [COLOR=green](https://alfa-addon.com/threads/manual-de-alfa-assistant-herramienta-de-apoyo.3797/)[/COLOR]".format(channel_name),
                             thumbnail=get_thumb("update.png"), url="https://alfa-addon.com/threads/manual-de-alfa-assistant-herramienta-de-apoyo.3797/"))

    return itemlist


def clean_title(title):
    year_pattern = r'\([\d -]+?\)'
    year_pattern += '|(\d{4})$'
    year_pattern += '|(TV)$'
    return re.sub(year_pattern, '', title).strip()


def search(item, texto):
    logger.info()
    itemlist = []
    item.url = urlparse.urljoin(HOST, "search_suggest")
    texto = texto.replace(" ", "+")
    post = "value=%s" % texto

    try:
        if alfa_assistant.is_alfa_installed():
            dict_data = httptools.downloadpage(item.url, post=post).json
            for e in dict_data:
                title = clean_title(scrapertools.htmlclean(e["name"]))
                url = e["url"]
                plot = e["description"]
                thumbnail = e["thumb"]
                new_item = item.clone(action="episodios", title=title, url=url, plot=plot, thumbnail=thumbnail)
                if "Pelicula" in e["genre"]:
                    new_item.contentType = "movie"
                    new_item.contentTitle = title
                else:
                    new_item.contentSerieName = title
                    new_item.context = renumbertools.context(item)
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
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    patron = 'id="%s_filter"[^>]+><div class="inner">(.*?)</div></div>' % item.extra
    data = scrapertools.find_single_match(data, patron)
    matches = re.compile('<a href="([^"]+)"[^>]+>(.*?)</a>', re.DOTALL).findall(data)
    for url, title in matches:
        url = "%s/nombre/lista" % url
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url,
                             context=renumbertools.context(item)))
    return itemlist


def newest(categoria):
    itemlist = []
    if alfa_assistant.is_alfa_installed():
        if categoria == 'anime':
            itemlist = novedades_episodios(Item(url=HOST))
    return itemlist


def novedades_episodios(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListEpisodios[^>]+>(.*?)</ul>')
    matches = re.compile('href="([^"]+)"[^>]+>.+?<img src="([^"]+)".+?"Capi">(.*?)</span>'
                         '<strong class="Title">(.*?)</strong>', re.DOTALL).findall(data)
    itemlist = []
    for url, thumbnail, str_episode, show in matches:
        try:
            episode = int(str_episode.replace("Ep. ", ""))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)
        show = clean_title(show)
        title = "%s: %sx%s" % (show, season, str(episode).zfill(2))
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url, contentSerieName=show, thumbnail=thumbnail,
                        contentTitle=title)
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def novedades_anime(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')
    
    matches = re.compile('<img src="([^"]+)".+?<a href="([^"]+)">(.*?)</a>', re.DOTALL).findall(data)
    
    for thumbnail, url, title in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        title = clean_title(title)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        contentTitle=title)
        new_item.contentSerieName = title
        new_item.context = renumbertools.context(item)
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def listado(item):
    logger.info()
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    
    url_pagination = scrapertools.find_single_match(data, '<li class="current">.*?</li>[\s]<li><a href="([^"]+)">')
    
    data = scrapertools.find_single_match(data, '</div><div class="full">(.*?)<div class="pagination')
    
    matches = re.compile('<img.+?src="([^"]+)".+?<a href="([^"]+)">(.*?)</a>.+?'
                         '<div class="full item_info genres_info">(.*?)</div>.+?class="full">(.*?)</p>',
                         re.DOTALL).findall(data)
    itemlist = []
    for thumbnail, url, title, genres, plot in matches:
        title = clean_title(title)
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        contentTitle=title, plot=plot, )
        if "Pelicula Anime" in genres:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        else:
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        itemlist.append(new_item)
    if url_pagination:
        url = urlparse.urljoin(HOST, url_pagination)
        title = ">> Pagina Siguiente"
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    
    if alfa_assistant.is_alfa_installed():

        data = httptools.downloadpage(item.url).data
        data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
        
        if item.plot == "":
            item.plot = scrapertools.find_single_match(data, 'Description[^>]+><p>(.*?)</p>')
        
        data = scrapertools.find_single_match(data, '<div class="Sect Episodes full">(.*?)</div>')
        matches = re.compile('<a href="([^"]+)"[^>]+>(.+?)</a', re.DOTALL).findall(data)
        
        for url, title in matches:
            title = title.strip()
            url = urlparse.urljoin(item.url, url)
            thumbnail = item.thumbnail
            try:
                episode = int(scrapertools.find_single_match(title, "Episodio (\d+)"))
            except ValueError:
                season = 1
                episode = 1
            else:
                season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)
            
            infoLabels['season'] = season
            infoLabels['episode'] = episode

            title = "%s: %sx%s" % (item.title, season, str(episode).zfill(2))
            
            itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                                       contentTitle=title, fanart=thumbnail, contentType="episode",
                                       infoLabels=infoLabels, contentSerieName=item.contentSerieName,))
        itemlist.reverse()
        
        tmdb.set_infoLabels(itemlist, seekTmdb=True)
    else:
        return []
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if alfa_assistant.is_alfa_installed():

        data = httptools.downloadpage(item.url).data
        bloque = scrapertools.find_single_match(data, 'Server</span>(.*?)id="choose_quality"')
        matches = scrapertools.find_multiple_matches(bloque, '<option sv="[^"]+" value="([^"]+)"')
        headers = {"Referer" : item.url}

        for url in matches:
            xserver = scrapertools.find_single_match(url, 's=([a-zA-Z0-9]+)')
            source = HOST + "get_video_info_v2?s=%s" % xserver
            link = get_link(source, url)
            if link:
                itemlist.append(Item(channel=item.channel, action="play", url=link, 
                                title=xserver.capitalize(),plot=item.plot, thumbnail=item.thumbnail,
                                contentTitle=item.title, language='VOSE', server="directo"))
        #~itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

        # Requerido para AutoPlay
        autoplay.start(itemlist, item)
    else:
        from lib import generictools
        browser, res = generictools.call_browser('', lookup=True)
        if not browser:
            action = ''
        else:
            action = 'call_browser'
        from channelselector import get_thumb
        from core import channeltools
        channel_name = channeltools.get_channel_parameters(item.channel)["title"]
        itemlist.append(Item(channel=item.channel, action=action, title="Para utilizar {} se requiere Alfa Assistant. [COLOR=yellow]Haz clic para + info[/COLOR] [COLOR=green](https://alfa-addon.com/threads/manual-de-alfa-assistant-herramienta-de-apoyo.3797/)[/COLOR]".format(channel_name),
                             thumbnail=get_thumb("update.png"), url="https://alfa-addon.com/threads/manual-de-alfa-assistant-herramienta-de-apoyo.3797/"))

    return itemlist

def get_link(source, referer):
    logger.info()
    itemlist = []
    
    headers={"Referer" : referer}
    _id = scrapertools.find_single_match(referer, 'ver/([^/]+)/')
    post = "embed_id=%s" % _id

    
    dict_data = httptools.downloadpage(source, post=post,  headers=headers).json
    frame_src = scrapertools.find_single_match(dict_data["value"], 'iframe src="([^"]+)"')
    
    try:
        new_data = httptools.downloadpage(frame_src, headers=headers).data
    except:
        logger.error('Problema con headers???')
        return ''


    if 'hydrax.net' in new_data:
        slug = scrapertools.find_single_match(new_data, '"slug","value":"([^"]+)"')
        post = "slug=%s&dataType=mp4" % slug
        #based on https://github.com/thorio/KGrabber/issues/35#issuecomment-667401636
        data = httptools.downloadpage("https://ping.iamcdn.net/", post=post).json
        url = data.get("url", '')
        if url:
            import base64
            url = "https://www.%s" % base64.b64decode(url[-1:]+url[:-1])
            url += '|Referer=https://playhydrax.com/?v=%s&verifypeer=false' % slug
        
        return url
    
    new_data = new_data.replace("'", '"')
    patron = '"file":'
    
    if 's=fserver' in source:
        patron = r'window.open\('
    
    url = scrapertools.find_single_match(new_data, patron+'"([^"]+)"')

    url = url.replace("\\","")
    url += "|User-Agent=%s" % httptools.get_user_agent()
        
    return url
