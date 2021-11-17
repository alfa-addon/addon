# -*- coding: utf-8 -*-
# -*- Channel CineCalidad -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from builtins import map
from builtins import range

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import re
import base64
from core import tmdb
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay

IDIOMAS = {'latino': 'Latino', 'castellano': 'Castellano', 'portugues': 'Portugues'}
list_language = list(IDIOMAS.values())
list_quality = ['1080p']
list_servers = ['gounlimited',
                'mega',
                'vidcloud',
                'torrent'
                ]

host = 'https://cinecalidad.website/'

thumbmx = 'http://flags.fmcdn.net/data/flags/normal/mx.png'
thumbes = 'http://flags.fmcdn.net/data/flags/normal/es.png'
thumbbr = 'http://flags.fmcdn.net/data/flags/normal/br.png'

current_lang = ''

site_list = ['', '%s' % host, '%s/espana/' % host, 'https://www.cinemaqualidade.im']
site = config.get_setting('filter_site', channel='cinecalidad')
site_lang = '%s' % site_list[site]

def mainlist(item):
    logger.info()

    itemlist = list()
    idioma2 = "destacadas"

    if site > 0:
        item.action = 'submenu'
        item.host = site_lang
        return submenu(item)

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title="CineCalidad Latino",
                         action="submenu",
                         host=host,
                         thumbnail=thumbmx))

    itemlist.append(Item(channel=item.channel,
                         title="CineCalidad Castellano",
                         action="submenu",
                         host=host+'/espana/',
                         thumbnail=thumbes))

    # itemlist.append(Item(channel=item.channel,
    #                      title="CineCalidad Portugues",
    #                      action="submenu",
    #                      host="https://www.cinemaqualidade.im",
    #                      thumbnail=thumbbr))

    itemlist.append(Item(channel=item.channel,
                         title="Configurar Canal...",
                         text_color="turquoise",
                         action="settingCanal",
                         thumbnail=get_thumb('setting_0.png'),
                         url='',
                         fanart=get_thumb('setting_0.png')
                         ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    idioma = 'peliculas'
    idioma2 = "destacada"
    host = item.host
    # if item.host == "https://www.cinemaqualidade.im":
    #     idioma = "filmes"
    #     idioma2 = "destacado"
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title=idioma.capitalize(),
                         action="list_all",
                         url=host,
                         thumbnail=get_thumb('movies', auto=True),
                         ))
    if "/espana/" not in item.host:
        itemlist.append(Item(channel=item.channel,
                             title="Destacadas",
                             action="featured",
                             url=host,
                             thumbnail=get_thumb('hot', auto=True),
                             ))
        itemlist.append(Item(channel=item.channel,
                             title="Generos",
                             action="genres",
                             url=host,
                             thumbnail=get_thumb('genres', auto=True),

                             ))
        itemlist.append(Item(channel=item.channel,
                             title="Por Año",
                             action="by_year",
                             url=host + idioma + "-por-ano",
                             thumbnail=get_thumb('year', auto=True),
                             ))
    itemlist.append(Item(channel=item.channel,
                         title="Buscar...",
                         action="search",
                         thumbnail=get_thumb('search', auto=True),
                         url=host + '/?s=',
                         host=item.host,
                         ))
    if site > 0:
        autoplay.init(item.channel, list_servers, list_quality)

        itemlist.append(Item(channel=item.channel,
                             title="Configurar Canal...",
                             text_color="turquoise",
                             action="settingCanal",
                             thumbnail=get_thumb('setting_0.png'),
                             url='',
                             fanart=get_thumb('setting_0.png')
                             ))

        autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def featured(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find("div", class_="wdgt__movies")
    matches = soup.find_all("a")

    for elem in matches:
        url = elem["href"]
        if scrapertools.find_single_match(url, "\d+x\d+") or "episode" in url:
            continue
        title = elem["title"]
        year = scrapertools.find_single_match(title, " \((\d{4})\)")
        contentTitle = title.replace("(%s)" % year, "").strip()
        
        itemlist.append(Item(channel=item.channel, title=contentTitle, contentTitle=contentTitle, url=url,
                             action="findvideos", infoLabels={"year": year}))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url, unescape=True)
    #matches = soup.find_all("div", class_="home_post_cont")
    matches = soup.find_all("div", class_="postItem")

    for elem in matches:
        #url = scrapertools.find_single_match(elem.img.get("extract", ""), "href='([^']+)'")
        url = elem.a.get("href", "")

        if not url:
            continue
        try:
            title, year = elem.img["title"].split(' (')
            year = re.sub(r"\)","", year)
        except:
            title = elem.img["alt"]
            year = "-"

        thumb = re.sub(r'(-\d+x\d+.jpg)', '.jpg', elem.img["src"])
        if elem.p: 
            plot = elem.p.text
        else:
            plot = ''
        
        if scrapertools.find_single_match(url, "\d+x\d+") or "episode" in url:
            continue
        itemlist.append(Item(channel=item.channel, title=title, url=url, thumbnail=thumb, action="findvideos",
                             plot=plot, contentTitle=title, infoLabels={'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    ## Pagination ##

    try:
        next_page = soup.find("a", class_="nextpostslink")["href"]
        itemlist.append(Item(channel=item.channel,  action="list_all",  title="Página siguiente >>",
                             url=next_page, language=item.language ))
    except:
        pass

    return itemlist


def by_year(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url, unescape=True).find("div", class_="yearlist")
    for elem in soup.find_all('a'):
        url = elem["href"]
        title = elem.text
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all", search=True))

    return itemlist


def genres(item):
    logger.info()

    itemlist = list()

    #soup = create_soup(item.url, unescape=True).find("ul", id="menu-menu")
    soup = create_soup(item.url, unescape=True).find("div", class_="tagList__cnt")
    matches = soup.find_all("a")
    for elem in matches:

        url = elem["href"]
        title = elem.text

        if "series" in title.lower() or "peliculas" in title.lower():
            continue

        if not url.startswith('http'):
            url = item.url +url
        
        itemlist.append(Item(channel=item.channel, title=title, url=url, action="list_all"))

    return itemlist


def settingCanal(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return


def dec(item, dec_value):
    link = list()
    val = item.split(' ')
    link = list(map(int, val))
    for i in range(len(link)):
        link[i] = link[i] - int(dec_value)
        real = ''.join(map(chr, link))
    return (real)


def findvideos(item):

    logger.info()
    itemlist = []
    dl_itemlist = list()
    duplicados = []

    if 'espana' in item.url:
        lang = 'castellano'
    else:
        lang = 'latino'
    
    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = '(?:onclick="Abrir.*?"|class="link(?: onlinelink)?").*?data(?:-url)?="([^"]+)".*?<li>([^<]+)</li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    server_url = {'yourupload': 'https://www.yourupload.com/embed/%s',
                  'trailer': 'https://www.youtube.com/embed/%s',
                  'bittorrent': '',
                  'mega': 'https://mega.nz/file/%s',
                  'fembed': '%s',
                  'gounlimited': 'https://gounlimited.to/embed-%s.html',
                  'clipwatching': 'https://clipwatching.com/embed-%s.html',
                  'vidcloud': 'https://vidcloud.co/embed/%s',
                  'jetload': 'https://jetload.net/e/%s',
                  'evoload': 'https://evoload.io/e/%s',
                  'doodstream': '%s',
                  'cineplay': '%s'}

    dec_value = scrapertools.find_single_match(data, 'String\.fromCharCode\(parseInt\(str\[i\]\)-(\d+)\)')
    protected_links = scrapertools.find_multiple_matches(data, '<a href="(%sprotect/v.php[^"]+)" target="_blank">\s?<li>([^<]+)</li>\s+?</a>' % host)
    subs = scrapertools.find_single_match(data, '<a id=subsforlink href=(.*?) ')
    if protected_links:
        headers = {'Referer': item.url}
        language = IDIOMAS[lang]
        quality = '1080p'
        for protected, server_id in protected_links:
            is_dl = False
            protected_link = scrapertools.decodeHtmlentities(protected)
            if "torrent" not in server_id.lower():
                enc_url = scrapertools.find_single_match(protected_link, "i=([^&]+)")
                url = base64.b64decode(enc_url).decode("utf-8")
                if url.startswith("https://mega.nz/file"):
                    continue
                is_dl = True
            else:
                p_data = httptools.downloadpage(protected_link, headers=headers, ignore_response_code=True).data
                url = scrapertools.find_single_match(p_data, 'value="(magnet.*?)"')
                quality = '1080p'
                if "4K" in server_id:
                    quality = '4K'
                language = IDIOMAS[lang]
            if url and url in duplicados:
                continue
            else:
                duplicados.append(url)
            new_item = Item(channel=item.channel,
                            action='play',
                            title="%s",
                            contentTitle=item.contentTitle,
                            url=url,
                            language=language,
                            quality=quality,
                            subtitle=subs,
                            infoLabels=item.infoLabels
                            )
            if is_dl:
                dl_itemlist.append(new_item)
            else:
                new_item.server = "Torrent"
                itemlist.append(new_item)

    for video_cod, server_id in matches:
        thumbnail = item.thumbnail

        server = server_id.lower()
        if server == "trailer":
            continue

        video_id = dec(video_cod, dec_value)
        if not video_id.startswith("http"):
            url = server_url.get(server, '')
            if not url:
                continue
            url = url % video_id
        else:
            url = video_id

        quality = '1080p'
        language = IDIOMAS[lang]
        if url:
            duplicados.append(url)
            new_item = Item(channel=item.channel,
                            action='play',
                            title="%s",
                            contentTitle=item.contentTitle,
                            url=url,
                            language=language,
                            thumbnail=thumbnail,
                            quality=quality,
                            subtitle=subs,
                            infoLabels=item.infoLabels
                            )
            itemlist.append(new_item)

    if dl_itemlist:
        itemlist += dl_itemlist

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    # itemlist.append(trailer_item)
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))

    return itemlist


def get_urls(item, link):
    logger.info()
    url = '%s/ccstream/ccstream.php' % host
    headers = dict()
    headers["Referer"] = item.url
    post = 'link=%s' % link

    dict_data = httptools.downloadpage(url, post=post, headers=headers).json
    return dict_data['link']


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = '%sinfantil/' % host
        elif categoria == 'terror':
            item.url = '%sterror/' % host
        elif categoria == 'castellano':
            item.url = '%sespana/' % host
        itemlist = list_all(item)
        if itemlist[-1].title == 'Página siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "-")

    if item.host != '':
        host_list = [item.host]
    elif site:
        item.gb_search = True
        host_list = [site_lang]
    else:
        item.gb_search = True
        host_list = ['%s/espana/' % host, host]
    item.search = True
    for host_name in host_list:
        item.url = host_name + '?s=' + texto
        if texto != '':
            itemlist.extend(list_all(item))

    return itemlist