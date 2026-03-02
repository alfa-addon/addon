# -*- coding: utf-8 -*-
# -*- Channel allpornstream -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-
#------------------------------------------------------------

import re

from core import urlparse
from platformcode import config, logger,unify
from core import scrapertools

from core.item import Item
from core import servertools, channeltools
from core import httptools
from bs4 import BeautifulSoup
from modules import autoplay
from core.jsontools import json

UNIFY_PRESET = config.get_setting("preset_style", default="Inicial")
color = unify.colors_file[UNIFY_PRESET]

list_quality = ['default']
list_servers = ['']

### https://allpornstream.com/   https://dayporner.com/  https://pornstellar.com/   https://freepornfun.com/
### https://diepornos.com/    https://redtubevids.com/  https://pornapes.com/
### https://scenesxxx.com/    https://sex-scenes.com/


##############    FALTA DIVIDIR EN PAG categorias

timeout = 20
forced_proxy_opt = 'ProxySSL'


canonical = {
             'channel': 'allpornstream', 
             'host': config.get_setting("current_host", 'allpornstream', default=''), 
             'host_alt': ["https://allpornstream.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
             # 'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             # 'cf_assistant': False, 'CF_stat': True, 
             # 'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "?page=1&sort=views" ))
    itemlist.append(Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "?page=1&sort=rating" ))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "api/table-list?type=producers", extra="producer" ))
    itemlist.append(Item(channel=item.channel, title="Pornstar" , action="categorias", url=host + "api/table-list?type=actors", extra="actor" ))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "api/table-list?type=categories", extra="category" ))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s?search=%s&page=1" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical, timeout=timeout).data
    else:
        data = httptools.downloadpage(url, canonical=canonical, timeout=timeout).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def categorias(item):
    logger.info()
    itemlist = []
    
    data_json = httptools.downloadpage(item.url).json
    
    for elem in data_json:
        cantidad = ""
        cantidad = elem['count']
        title = elem['%s' %item.extra] 
        slug = title.replace(" ", "-")
        if "producer" in item.extra:
            url = "%s?studio=%s&page=1" %(host,slug)
        else:
            url = "%s?%s=%s&page=1" %(host,item.extra,slug)
        if elem['thumbs_urls']:
            thumbnail = elem['thumbs_urls'][-1]
        else:
            thumbnail = ""
        if cantidad:
            title = "%s (%s)" %(title,cantidad)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             thumbnail=thumbnail , plot=plot) )
    if "category" in item.extra:
        itemlist.sort(key=lambda x: x.title)
        
    # cantidad = int(len(data_json))
    # lastpage = cantidad/30
    # if lastpage - int(lastpage) > 0:
        # lastpage = int(lastpage) + 1
    
    
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url, referer=host)
    matches = soup.find_all('div', attrs={'data-href': re.compile(r"^/post/[a-z0-9]+")})
    for elem in matches:
        if not elem.get('data-href', ''): continue
        url = elem['data-href']
        title = elem['data-title']
        slug = elem['data-slug']
        thumbnail = elem.img['src']
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        # canal = ""
        # canal = elem.find('a', href=re.compile("/producers/[A-z0-9-]+"))
        # if canal:
            # canal = canal.img['alt']
            # if canal in title: title = title.split("]")[-1]
            # canal = "[COLOR %s][%s][/COLOR]" % (color.get('tvshow',''),canal)
        pornstar = ""
        nostar = ""
        pornstars = elem.find_all('a', class_='inline-block', href=re.compile("/actors/[A-z0-9-]+"))
        for x , value in enumerate(pornstars):
            if value.text.strip() in title:
                camb = "[COLOR %s] %s[/COLOR]" % (color.get('rating_3',''),value.text.strip())
                title = title.replace(value.text.strip(), camb)
            else:
                pornstars[x] = value.text.strip()
                nostar = 1
        if nostar == 1:
            pornstar = ' & '.join(pornstars)
            pornstar = "[COLOR %s] %s[/COLOR]" % (color.get('rating_3',''),pornstar)
            title = "%s %s" %(pornstar,title)
        
        url = urlparse.urljoin(item.url,url)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, contentTitle=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    
    if not "page=" in item.url:
        item.url = "%s?page=1" %host
    next_page = soup.find_all('a', tabindex='-1')
    if next_page:
        next_page = next_page[-1]['href']
        next_page = scrapertools.find_single_match(next_page, 'page=(\d+)')
        next_page = re.sub(r"page=\d+", "page={0}".format(next_page), item.url)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    repes = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\\"', '"', data)
    
    url = ""
    url = scrapertools.find_single_match(data, '"contentUrl":"([^"]+)"')
    if url:
        itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    
    patron = '"embed_url":"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        if not url in repes:
            repes.append(url)
            itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    autoplay.start(itemlist, item)
    return itemlist
