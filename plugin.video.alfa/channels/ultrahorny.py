# -*- coding: utf-8 -*-
# -*- Channel UltraHorny -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from core import urlparse as alfa_urlparse
import re

from core import urlparse
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from bs4 import BeautifulSoup

forced_proxy_opt= ""

''' CANAL ANTIGUA OUT pages
    gameofporn  veporns  https://www.veporno.net  https://www.fxporn.net      http://www.veporns.com    '''

#  https://veporn.com/  https://ultrahorny.com/   https://eporner.xxx/
# https://pornoflix.com/  

canonical = {
             'channel': 'ultrahorny', 
             'host': config.get_setting("current_host", 'ultrahorny', default=''), 
             'host_alt': ["https://ultrahorny.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []





# https://ultrahorny.com/api/videos?category=big-tits&sort=newest&cursor=&cursor=  nextCursor
# https://ultrahorny.com/api/videos?category=&sort=newest&cursor=  most_viewed  top_rated  longest

# https://ultrahorny.com/api/videos?pornstar=cory-chase&sort=newest&cursor=
# https://ultrahorny.com/api/videos?category=big-tits&sort=newest&cursor=

# https://ultrahorny.com/api/videos?q=big+tits&sort=newest&cursor=

api = "%sapi/videos?sort=%s&cursor="

def mainlist(item):
    logger.info()

    itemlist = []
    
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="list_all", url=api %(host,"newest")))
    itemlist.append(Item(channel=item.channel, title="Mas visto" , action="list_all", url=api %(host,"most_viewed")))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="list_all", url=api %(host,"top_rated")))
    itemlist.append(Item(channel=item.channel, title="Mas largo" , action="list_all", url=api %(host,"longest")))
    itemlist.append(Item(channel=item.channel, title="Pornstars", action="catalogo", url=alfa_urlparse.build_url(host, 'pornstars', query='page=1'), extra="Pornstar"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="categorias", url=alfa_urlparse.build_url(host, 'search'), extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))

    return itemlist


def search(item, texto):
    logger.info()
    _url_query_texto = texto
    texto = texto.replace(" ", "+")
    item.url = alfa_urlparse.build_url(host, 'api/search', query=[('q', u'{}'.format(_url_query_texto)), ('sort', 'newest'), ('cursor', '')])
    try:
        return list_all(item)
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    
    matches = soup.find_all('a', href=re.compile("/category/[A-z0-9-]+"))
    for elem in matches:
        id = elem['href'].replace('/category/', '')
        title = elem.img['alt']
        thumbnail = elem.img['src']
        cantidad = elem.find('p')
        if cantidad:
            cantidad = cantidad.text.replace('videos', '')
            title = "%s (%s)" % (title,cantidad.strip())
        url = alfa_urlparse.build_url(host, 'api/videos', query=[('category', u'{}'.format(id)), ('sort', 'newest'), ('cursor', '')])
        # url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="list_all", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('a', href=re.compile("/pornstar/[A-z0-9-]+"))
    for elem in matches:
        id = elem['href'].replace('/pornstar/', '')
        title = elem.img['alt']
        thumbnail = elem.img['src']
        cantidad = elem.find('span')
        if cantidad:
            cantidad = cantidad.text.replace('videos', '')
            title = "%s (%s)" % (title,cantidad.strip())
        url = alfa_urlparse.build_url(host, 'api/videos', query=[('pornstar', u'{}'.format(id)), ('sort', 'newest'), ('cursor', '')])
        # url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="list_all", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    
    next_page = soup.find("a", string=re.compile(r"^Next"))
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist

def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def list_all(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, canonical=canonical).json
    for elem in data['data']:
        url = alfa_urlparse.urljoin(host, u'{}'.format(elem['slug']))
        title = elem['title']
        thumbnail = alfa_urlparse.urljoin(host, u'{}'.format(elem['thumbnailUrl']))
        quality = elem['quality']
        video = elem['cdnUrl']
        
        
        segundos = elem['duration']
        horas=int(segundos/3600)
        segundos-=horas*3600
        minutos=int(segundos/60)
        segundos-=minutos*60
        if segundos < 10:
            segundos = "0%s" %segundos
        if minutos < 10:
            minutos = "0%s" %minutos
        if horas == 00:
            time = "%s:%s" % (minutos,segundos)
        else:
            time = "%s:%s:%s" % (horas,minutos,segundos)
        
        if  elem['quality']:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time, quality,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
                
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle=title, url=url, video=video,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = data['nextCursor']
    if next_page:
        next_page = re.sub(r"&cursor=[^&]*", "&cursor={0}".format(next_page), item.url)
        itemlist.append(item.clone(action="list_all", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info()
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         verify_links=False, findvideos_proc=True, **kwargs)


def play(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url, **kwargs)
    
    pornstars = soup.find_all('a', href=re.compile("/pornstar/[A-z0-9-]+"))
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s" % pornstar
    lista = item.contentTitle.split('[/COLOR]')
    pornstar = ' %s' %pornstar
    if "[COLOR red]" in item.contentTitle:
        lista.insert (2, pornstar)
    else:
        lista.insert (1, pornstar)
    item.contentTitle = '[/COLOR]'.join(lista)
    
    url = "%s|Referer=%s" %(item.video, item.video)
    itemlist.append(Item(channel=item.channel, action="play", contentTitle = item.contentTitle, url=url))
    return itemlist
