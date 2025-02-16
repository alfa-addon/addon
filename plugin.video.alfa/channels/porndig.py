# -*- coding: utf-8 -*-
#------------------------------------------------------------
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import httptools
from core import servertools
from core import urlparse
from bs4 import BeautifulSoup

canonical = {
             'channel': 'porndig', 
             'host': config.get_setting("current_host", 'porndig', default=''), 
             'host_alt': ["https://www.porndig.com/"], 
             'host_black_list': [], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", value="date", id=1, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", value="views", id=1, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", value="rating", id=1, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas comentado" , action="lista", value="comments", id=1, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas metraje" , action="lista", value="duration", id=1, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="pornstar", url=host + "pornstars/load_more_pornstars", id=1,
                               value="popularity", offset=""))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="pornstar", url=host + "studios/load_more_studios", id=1,
                               value="popularity", offset=""))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "video/", id=1))
    # itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))

    itemlist.append(Item(channel=item.channel, title="", action="", folder=False))

    itemlist.append(Item(channel=item.channel, title="Amateur" , action="submenu", url=host + "amateur/videos/", id=4))
    itemlist.append(Item(channel=item.channel, title="Shemale" , action="submenu", url=host + "transexual/videos/", id=3))
    itemlist.append(Item(channel=item.channel, title="Gay" , action="submenu", url=host + "gay/videos/", id=2))
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", value="date", id=item.id, per="",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", value="views", id=item.id, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", value="rating", id=item.id, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas comentado" , action="lista", value="comments", id=item.id, per="month",
                               category = "", offset=""))
    itemlist.append(Item(channel=item.channel, title="Mas metraje" , action="lista", value="duration", id=item.id, per="month",
                               category = "", offset=""))
    if item.id !=4:
        itemlist.append(Item(channel=item.channel, title="PornStar" , action="pornstar", url=host + "pornstars/load_more_pornstars", id=item.id,
                                   value="popularity", offset=""))
        itemlist.append(Item(channel=item.channel, title="Canal" , action="pornstar", url=host + "studios/load_more_studios", id=item.id,
                                   value="popularity", offset=""))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=item.url, id=item.id))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%ssearch?q=%s" % (host,texto)
    item.texto = texto
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
    
    soup = create_soup(item.url)
    matches = soup.find('div', class_='filter_category_select_wrapper').find_all('option')
    for elem in matches:
        category = elem['value']
        title = elem.text
        if category:
            itemlist.append(Item(channel=item.channel, title=title , action="lista", value="date", id=item.id, per="",
                                       category=category, offset=""))
    return itemlist


def create_soup(url, post=None, referer=None,  unescape=False):
    logger.info()
    if post:
        headers = {'Cookie': 'main_category_id=%s' % referer}
        data = httptools.downloadpage(url, post=post, headers=headers, canonical=canonical).data
        data = data.replace("\\n", " ").replace("\\t", "").replace("\\", "")
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def pornstar(item):
    logger.info()
    itemlist = []
    
    if not item.offset:
        offset = 0
    else:
        offset = item.offset
    if "pornstars" in item.url:
        posturl = "%spornstars/load_more_pornstars" %host
        post = "main_category_id=%s&type=pornstar&name=top_pornstars&filters[filter_type]=%s&offset=%s" % (item.id,item.value,offset)
    else:
        posturl = "%sstudios/load_more_studios" %host
        # post = "main_category_id=1&type=studio&name=top_studios&filters[filter_type]=%s&offset=%s" % (item.value,offset)
        post = {'main_category_id': item.id, 'type': 'studio', 'name': 'top_studios', 'filters[filter_type]': item.value, 'quantity': 30, 'offset':offset} 
    soup = create_soup(posturl, post)
    matches = soup.find_all('div', class_='showcase_item_wrapper')
    for elem in matches:
        value = elem['id'].replace("_", "")
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('div', class_='showcase_views').text.strip()
        if cantidad:
            title = "%s (%s)" % (title, cantidad)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url, plot=plot,
                               fanart=thumbnail, thumbnail=thumbnail, id=item.id, value=value, category = "", offset=""))
    next_page = scrapertools.find_single_match(str(soup), '"has_more":(true)')
    if next_page:
        offset += 30 
        itemlist.append(Item(channel=item.channel, action="pornstar", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=item.url, id=item.id, value=item.value, offset=offset ) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    
    if not item.offset:
        offset = 0
    else:
        offset = item.offset
    posturl = "%sposts/load_more_posts" %host
    referer = item.id
    
    if "pornstars" in item.url:
        # main_category_id=1&type=post&name=pornstar_related_videos&filters%5Bfilter_type%5D=date&filters%5Bfilter_period%5D=&filters%5Bfilter_quality%5D%5B%5D=270&filters%5Bfilter_duration%5D%5B%5D=45&filters%5Bfilter_duration%5D%5B%5D=26&filters%5Bfilter_duration%5D%5B%5D=15&filters%5Bfilter_duration%5D%5B%5D=14&adblock_enabled=&content_id=4366&offset=30
        post = "main_category_id=%s&type=post&name=pornstar_related_videos&filters[filter_type]=date&filters[filter_period]=&filters[filter_quality][]=270&content_id=%s&offset=%s" % (item.id,item.value,offset)
    else:
        # post = "?main_category_id=%s&type=post&name=multifilter_videos&filters[filter_type]=%s&filters[filter_period]=%s&category_id[]=%s&offset=%s" % (item.id,item.value,item.per,item.category,offset)
        post = {'main_category_id': item.id, 'type': 'post', 'name': 'multifilter_videos', 'filters[filter_type]': item.value, 'filters[filter_period]': item.per, 'category_id[]': item.category, 'offset':offset} 
    if "studio" in item.url:
        post = {'main_category_id': item.id, 'type': 'post', 'name': 'studio_related_videos', 'filters[filter_type]': 'ctr', 'filters[filter_period]': '','filters[filter_quality][]': '270', 'content_id': item.value, 'offset':offset} 
        post = "main_category_id=%s&type=post&name=studio_related_videos&filters[filter_type]=ctr&filters[filter_period]=&filters[filter_quality][]=270&content_id=%s&offset=%s" % (item.id,item.value,offset)
    if "search" in item.url:
        post = "main_category_id=%s&type=post&name=search_posts&search=%s&offset=%s" % (item.id,item.texto, offset)
    
    soup = create_soup(posturl, post, referer)
    matches = soup.find_all('section', class_='video_item_medium')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['data-src']
        stime = elem.find('div', class_='bubble').text.strip()
        quality = elem.find('i', class_='pull-right')['class'][1].replace("icon-ic_19_qlt_", "")
        if stime:
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,stitle)
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (stime,stitle)
        url = urlparse.urljoin(host,url)
        plot = ""
        action = "play"
        if logger.info() is False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, plot=plot,
                               fanart=thumbnail, thumbnail=thumbnail, contentTitle=title ))
    next_page = scrapertools.find_single_match(str(soup), '"has_more":(true)')
    if next_page:
        if "name=all_videos" in post:
            offset += 50 
        else:
            offset += 36 
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=item.url, id=item.id, value=item.value, category=item.category, offset=offset ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='video_download_wrapper').find_all('a', class_='post_download_link clearfix')
    for elem in matches:
        url = elem['href']
        quality = url[-4:]
        url = httptools.downloadpage(url, headers={"referer": item.url}, follow_redirects=False).headers["location"]
        itemlist.append(Item(channel=item.channel, action="play", title=quality, contentTitle = item.title, url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = create_soup(item.url).find('div', class_='video_wrapper').iframe['src'] #server
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    
    # matches = soup.find('div', class_='video_download_wrapper').find_all('a', class_='post_download_link clearfix')
    # for elem in matches:
        # url = elem['href']
        # quality = url[-5:].replace("_", "")
        # url = httptools.downloadpage(url, headers={"referer": item.url}, follow_redirects=False).headers["location"]
        # itemlist.append([quality, url])
    return itemlist

