# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools


# IDIOMAS = {'vo': 'VO'}
# list_language = list(IDIOMAS.values())
# list_quality = ['default']
# list_servers = []


canonical = {
             'channel': 'stripchat', 
             'host': config.get_setting("current_host", 'stripchat', default=''), 
             'host_alt': ["https://stripchat.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }


host = canonical['host'] or canonical['host_alt'][0]
hosta = "%sapi/front/models?limit=40&offset=0&sortBy=stripRanking&primaryTag=%s&filterGroupTags=[[\"%s\"]]"
    # 'https://stripchat.com/api/external/v4/widget/?limit=100&modelsCountry=&modelsLanguage=&modelsList=&tag=%s'
cat = "%sapi/front/models/liveTags?limit=40&primaryTag=girls&filterGroupTags=[[]]&sortBy=stripRanking" % host
       # https://es.stripchat.com/api/front/models/liveTags?primaryTag=girls&uniq=go3bmp2lfs6zi18a
httptools.downloadpage(host, canonical=canonical).data


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel = item.channel, title="Female" , action="lista", url=hosta %(host,"girls", "")))
    itemlist.append(Item(channel = item.channel, title="Couples" , action="lista", url=hosta % (host,"couples", "")))
    itemlist.append(Item(channel = item.channel, title="Male" , action="lista", url=hosta % (host,"men", "")))
    itemlist.append(Item(channel = item.channel, title="Transexual" , action="lista", url=hosta % (host,"trans", "")))
    itemlist.append(Item(channel = item.channel, title="Categorias" , action="categorias", url=cat))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host,texto)
    try:
        return lista(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for elem in data['liveTagGroups']:
        for list in elem['tags']:
            title = re.sub(r"tagLanguage|autoTag|age|ethnicity|privatePrice|specifics|specific|^do|subculture", "", list) # |bodyType|hairColor
            title = title.capitalize()
            url = hosta %(host,"girls", list)
            thumbnail = ""
            plot = ""
            itemlist.append(Item(channel = item.channel, action="lista", title=title, url=url,
                                  thumbnail=thumbnail , plot=plot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for elem in data['models']:
        ref = elem['hlsPlaylist']
        id = elem['id']
        thumbnail = elem['popularSnapshotTimestamp']
        server = elem['snapshotServer']
        quality = ""
        if elem['presets']:
            presets = elem['presets']
            quality = presets[0]
            presets.pop()
            presets = ','.join(presets[::-1])
        name = elem['username']
        pais = elem['country']
        title = name
        if quality:
            title += " [COLOR red]%s[/COLOR]" %quality
        if pais:
            title += " (%s)" %pais
        thumbnail = "https://img.strpst.com/thumbs/%s/%s_webp" %(thumbnail, id)
        if "_240p" in ref:
            ref = ref.replace("_240p", "")
            # url = "https://edge-hls.doppiocdn.com/hls/%s/master/%s.m3u8" %(id, id)
        url = "https://stripchat.com/api/front/v1/broadcasts/%s" %name
        url += "|%s" %ref
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel = item.channel, action=action, title=title, contentTitle=title, url=url,
                             thumbnail=thumbnail, fanart=thumbnail, plot=plot ))
                               
    count= data['filteredCount']
    current_page = scrapertools.find_single_match(item.url, ".*?&offset=(\d+)")
    current_page = int(current_page)
    if current_page <= int(count) and (int(count) - current_page) > 40:
        current_page += 40
        next_page = re.sub(r"&offset=\d+", "&offset={0}".format(current_page), item.url)
        itemlist.append(Item(channel = item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    itemlist.append(Item(channel = item.channel, action="play", contentTitle = item.contentTitle, url=item.url, server="stripchat" ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    
    itemlist.append(Item(channel = item.channel, action="play", contentTitle = item.contentTitle, url=item.url, server="stripchat" ))
    return itemlist