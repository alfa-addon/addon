# -*- coding: utf-8 -*-
# -*- Channel VerAnime Assistant -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib
else:
    import urllib

import re
import base64

from modules import autoplay, renumbertools
from platformcode import config, logger, unify, platformtools
from core import tmdb, httptools, servertools, scrapertools
from core.item import Item
from core.jsontools import json
from bs4 import BeautifulSoup
from channelselector import get_thumb
from channels import filtertools
from lib import alfa_assistant


IDIOMAS = {"audio castellano": "CAST", "audio latino": "LAT", "subtitulado": "VOSE"}
list_language = list(IDIOMAS.values())
list_quality_movies = ['HD']
list_quality_tvshow = list_quality_movies
list_quality = list_quality_movies
list_servers = ['uqload', 'streamwish', 'voe', 'tiwikiwi', 'mixdrop', 'mp4upload', 'gameovideo', 'streamtape', 'doodstream', 'streamlare']
forced_proxy_opt = 'ProxyCF'


canonical = {
             'channel': 'veranimeassistant', 
             'host': config.get_setting("current_host", 'veranimeassistant', default=''), 
             'host_alt': ["https://ww3.animeonline.ninja/"], 
             'host_black_list': ["https://ww2.animeonline.ninja/", "https://www1.animeonline.ninja/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 
             'cf_assistant_if_proxy': True, 'cf_assistant_get_source': False, 'CF_stat': True, 'session_verify': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }

host = canonical['host'] or canonical['host_alt'][0]
patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
domain = scrapertools.find_single_match(host, patron_domain)


def mainlist(item):
    logger.info()

    itemlist = list()
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title='Últimos Capitulos', url=host + 'episodio/', action='latest',
                         thumbnail=get_thumb('new episodes', auto=True), c_type='episodios'))
    
    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'online/', action='list_all',
                         thumbnail=get_thumb('anime', auto=True), c_type='series'))
    
    itemlist.append(Item(channel=item.channel, title='Peliculas', url=host + 'pelicula/', action='list_all',
                         thumbnail=get_thumb('movies', auto=True), c_type='peliculas'))

    itemlist.append(Item(channel=item.channel, title='Categorías',  action='sub_menu', url=host, 
                         thumbnail=get_thumb('categories', auto=True), c_type='series'))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host,
                         thumbnail=get_thumb("search", auto=True)))

    itemlist = renumbertools.show_option(item.channel, itemlist)

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality_tvshow, list_quality_movies)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Latino', url=host + "genero/audio-latino/", action='list_all',
                         thumbnail=get_thumb('lat', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Castellano', url=host + "genero/anime-castellano/", action='list_all',
                         thumbnail=get_thumb('cast', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Más Vistas', url=host + "tendencias/", action='list_all',
                         thumbnail=get_thumb('more watched', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Mejor Valoradas', url=host + "ratings/", action='list_all',
                         thumbnail=get_thumb('more voted', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Live Action', url=host + 'genero/live-action/', action='list_all',
                         thumbnail=get_thumb('anime', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Blu-Ray/DVD', url=host + "genero/blu-ray-dvd/", action='list_all',
                         thumbnail=get_thumb('quality', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Sin Censura', url=host + "genero/sin-censura/", action='list_all',
                         thumbnail=get_thumb('adults', auto=True)))

    return itemlist


def get_source(url, soup=False, unescape=False, ignore_response_code= True, **opt):
    logger.info()
    data = False
    opt['canonical'] = canonical
    opt['ignore_response_code'] = ignore_response_code
    if alfa_assistant.open_alfa_assistant():
        # Se desactiva el cache pues las respuestas fallidas
        # son bastante frecuentes y con el cache permanecen durante 24 horas.
        # Además nuevas entradas (capítulos/series/películas) podrían 
        # ser añadidas en ese periodo.
        response = alfa_assistant.get_source_by_page_finished(url, 1, closeAfter=True, disableCache=True)
        if response and isinstance(response, dict):
            data = get_source_by_url(response['htmlSources'], url)
            if not data or 'challenges.cloudflare.com' in data:
                response = alfa_assistant.get_source_by_page_finished(url, 5, closeAfter=True, disableCache=True)
                if response and isinstance(response, dict):
                    data = get_source_by_url(response['htmlSources'], url)

        if not data:
            platformtools.dialog_ok("Alfa Assistant: Error", "Assistant no pudo acceder a la web, vuelva a intentarlo mas tarde.")
            return False
    else:
        return False

    if 'Javascript is required' in data:
        from lib import generictools
        data = generictools.js2py_conversion(data, url, domain_name='.%s' % domain, 
                                             channel=canonical['channel'], headers=opt.get('headers', {}))
    # logger.info(data, True)
    data = scrapertools.unescape(data) if unescape else data
    data = BeautifulSoup(data, "html5lib", from_encoding="utf-8") if soup else data

    return data


def get_source_by_url(sources, url):
    data = False
    if not sources:
        return data
    try:
        if PY3:
            data = next(filter(lambda source: source['url'] == url, sources))['source']
        else:
            data = filter(lambda source: source['url'] == url, sources)[0]['source']
        data = base64.b64decode(data).decode("utf-8")
    except:
        logger.error("The url could not be found in the response sources.")
    
    return data


def list_all(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True)
    if not soup:
        return itemlist
    
    if "genero" in item.url or "tendencias" in item.url or "ratings" in item.url:
        matches = soup.find("div", class_="items")
    else:
        matches = soup.find("div", id="archive-content")
    
    for elem in matches.find_all("article", id=re.compile(r"^post-\d+")):

        info_1 = elem.find("div", class_="poster")
        info_2 = elem.find("div", class_="data")

        thumb = info_1.img.get("src")
        title = info_1.img["alt"]
        title = re.sub("VOSE", "", title)
        url = info_1.a["href"]
        filtro_tmdb = list({"original_language": "ja"}.items())
        try:
            year = info_2.find("span", text=re.compile(r"\d{4}")).text.split(",")[-1]
        except:
            year = '-'
        new_item = Item(
                    channel = item.channel,
                    infoLabels = {"year": year.strip(), 'filtro': filtro_tmdb},
                    thumbnail = thumb,
                    title = title,
                    url = url,
                )

        if "online" in url and not "pelicula" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
            new_item.contentType = 'tvshow'
            if new_item.infoLabels['year'] == '-': new_item.infoLabels['year'] = ''
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
            new_item.contentType = 'movie'

        new_item.context = filtertools.context(new_item, list_language, list_quality)
        new_item.context = renumbertools.context(new_item)
        new_item.context.extend(autoplay.context)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    try:
        next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
        itemlist.append(
            Item(
                action ="list_all",
                channel = item.channel,
                title = "Siguiente >>",
                url = next_page,
            )
        )
    except:
        pass

    return itemlist


def latest(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True)
    if not soup:
        return itemlist
    matches = soup.find("div", class_="animation-2 items")
    
    if not matches:
        return itemlist

    for elem in matches.find_all("article", id=re.compile(r"^post-\d+")):

        info = elem.find("div", class_="poster")

        thumb = info.img.get("src")
        title = re.sub('(?i)(?:season\s*)?(?:\d{1,2})?\s*Cap\s*\d{1,3}', '', info.img["alt"]).strip()
        url = info.a["href"]

        stitle = info.find("div", class_="epiposter").text
        stitle = stitle.replace('Episodio ', '1x')
        
        try:
            season, episode = scrapertools.find_single_match(info.img["alt"], '(?i)(?:(\d{1,2}))?\s*Cap\s*(\d{1,3})')
            season = int(season)
            episode = int(episode)
        except:
            season = 1
            episode = int(scrapertools.find_single_match(info.img["alt"], '(?i)(?:\d{1,2})?\s*Cap\s*(\d{1,3})') or 1)
        
        try:
            tag = info.find("span", class_="quality").text
        except:
            tag = ""

        ftitle = title +': '+ stitle
        ftitle = "%s [COLOR silver] (%s)[/COLOR]" % (ftitle, tag) if tag else ftitle        
        
        filtro_tmdb = list({"original_language": "ja"}.items())

        itemlist.append(
            Item(
                action = "findvideos",
                channel = item.channel,
                contentSerieName = title,
                contentType = 'episode', 
                contentSeason = season, 
                contentEpisodeNumber = episode, 
                thumbnail = thumb, 
                title = ftitle,
                url = url
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    try:
        next_page = soup.find_all("a", class_="arrow_pag")[-1]["href"]
        itemlist.append(
            Item(
                action="latest",
                channel = item.channel,
                title = "Siguiente >>",
                url = next_page
            )
        )
    except:
        pass

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()
    page = get_source(item.url, soup=True)
    if not page:
        return itemlist
    tags = get_tags(page, item.contentSerieName)
    soup = page.find("div", id="seasons")

    matches = soup.find_all("div", class_="se-c")

    infoLabels = item.infoLabels

    for elem in matches:
        try:
            season = int(elem.find("span", class_="se-t").text)
        except Exception:
            season = 1
        title = "Temporada %s" % (season)
        infoLabels["season"] = season
        infoLabels["mediatype"] = 'season'

        itemlist.append(
            Item(
                action = 'episodesxseasons',
                channel = item.channel,
                context = filtertools.context(item, list_language, list_quality),
                infoLabels = infoLabels,
                title = title,
                url = item.url
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.videolibrary:
        itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName=item.contentSerieName,
                extra = "episodios",
                text_color = 'yellow',
                title = 'Añadir esta serie a la videoteca',
                url = item.url
            )
        )

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    item.videolibrary = True if item.extra else False
    templist = seasons(item)

    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True)
    if not soup:
        return itemlist

    soup = soup.find("div", id="seasons")
    matches = soup.find_all("div", class_="se-c")
    infoLabels = item.infoLabels
    season = infoLabels["season"]

    for elem in matches:
        try:
            elemseason = int(elem.find("span", class_="se-t").text)
        except Exception:
            elemseason = 1
        
        if elemseason != season: continue

        epi_list = elem.find("ul", class_="episodios")

        if 'no hay episodios para' in str(epi_list):
            return itemlist

        for epi in epi_list.find_all("li"):
            info = epi.find("div", class_="episodiotitle")
            url = info.a["href"]
            epi_name = info.a.text
            #fix: temporada x episodio estilo "3x8.5", por la necesidad de convertirlo a int y no sobreescribir capitulo 3x8
            #3x8.5 será 3x85
            epi_num = int(str(epi.find("div", class_="numerando").text.split(" - ")[1]).replace('.','')) or 1
            infoLabels["episode"] = epi_num
            infoLabels["mediatype"] = 'episode'
            title = "%sx%s - %s" % (season, epi_num, epi_name)
            infoLabels['season'], infoLabels['episode'] = renumbertools.numbered_for_trakt(item.channel, 
                                                          item.contentSerieName, infoLabels['season'], infoLabels['episode'])

            itemlist.append(
                Item(
                    action = 'findvideos',
                    channel = item.channel,
                    infoLabels = infoLabels,
                    title = title,
                    url = url
                )
            )

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()
    
    itemlist = list()
    itemlist2 = list()
    servers = {'fcom': 'fembed', 'dood': 'doodstream', 
                'hqq': '', 'youtube': '', 'saruch': '',
                'supervideo': '', 'aparat': 'aparatcam'}
    headers = {"Referer": host}

    soup = get_source(item.url, soup=True)
    if not soup:
        return itemlist

    matches = soup.find("ul", id="playeroptionsul")
    if not matches:
        return itemlist

    for elem in matches.find_all("li"):
        server = elem.find("span", class_="server").text
        server = re.sub(r"\.\w{2,4}", "", server.lower())
        server = servers.get(server, server)

        if not server:
            continue

        eplang = elem.find('span', class_='title').text
        eplang = re.sub(r'SERVER \d+ ', '', eplang)
        language = IDIOMAS.get(eplang.lower(), "VOSE")
        title = '%s [%s]' % (server.capitalize(), language)
        server = elem.find('span', class_='server')
        server = server.text if server else ''

        # Sistema movidy
        # NOTE: De vez en cuando cambian entre un sistema de la API REST
        # de WordPress, y uno de iframes, mantener el código comentado aquí
        if server == 'saidochesto.top':
            # players = soup.find("li", id=re.compile(r"player-option-\d+"))
            # doo_url = players.find("iframe")["src"]
            doo_url = "{}wp-json/dooplayer/v1/post/{}?type={}&source={}".format(
                host, elem["data-post"], elem["data-type"], elem["data-nume"])
            
            data = get_source(doo_url, soup=True, headers=headers)
            if not data:
                continue
            data = json.loads(data.find("pre").text)
            
            url = data.get("embed_url", "")
            # url = players.find("iframe")["src"]
            
            new_soup = get_source(url, soup=True)
            if not new_soup:
                continue
            
            new_soup = new_soup.find("div", class_="OptionsLangDisp")
            
            resultset = new_soup.find_all("li") if new_soup else []

            for elem in resultset:
                url = elem["onclick"]
                url = scrapertools.find_single_match(url, r"\('([^']+)")

                if "cloudemb.com" in url: continue

                server = elem.find("span").text
                lang = elem.find("p").text

                server = re.sub(r"\.\w{2,4}", "", server.lower())
                server = servers.get(server, server)
                if not server:
                    continue

                lang = re.sub(' -.*', '', lang)
                language = IDIOMAS.get(lang.lower(), "VOSE")

                stitle = unify.add_languages("", language)

                if not "multiserver" in eplang.lower():
                    stitle = ": %s %s" % (eplang.title(), stitle)

                if url:
                    itemlist2.append(
                        Item(
                            action = "play",
                            channel = item.channel,
                            infoLabels = item.infoLabels,
                            language = language,
                            title = '%s' + stitle,
                            url = url,
                        )
                    )
            break
        else:    
            itemlist.append(
                Item(
                    action = "play",
                    channel = item.channel,
                    headers = headers,
                    infoLabels = item.infoLabels,
                    language = language,
                    server = server,
                    title = title,
                    url = doo_url
                )
            )

    if itemlist2:
        itemlist = servertools.get_servers_itemlist(itemlist2, lambda x: x.title % x.server.capitalize())
    else:
        itemlist.sort(key=lambda i: (i.language, i.server))

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != "findvideos":
            itemlist.append(
                Item(
                    action = "add_pelicula_to_library",
                    channel = item.channel,
                    contentTitle = item.contentTitle,
                    extra = "findvideos",
                    text_color = "yellow",
                    title = "Añadir esta pelicula a la videoteca",
                    url = item.url
                )
            )

    # Para ver dónde están los "directos" y
    # descartarlos o arreglarlos apropiadamente
    # logger.debug([f"url: {x.url}\nserver: {x.server}\n\n" for x in itemlist])

    return itemlist


def search_results(item):
    logger.info()

    itemlist = list()

    soup = get_source(item.url, soup=True)
    if not soup:
        return itemlist

    for elem in soup.find_all("div", class_="result-item"):

        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.img["alt"]
        year = elem.find("span", class_="year").text

        new_item = Item(
                    channel = item.channel,
                    infoLabels = {"year": year.strip()},
                    title = title,
                    thumbnail = thumb,
                    url = url
                )

        if "online" in url and not "pelicula" in url:
            new_item.action = "seasons"
            new_item.contentSerieName = title
            new_item.contentType = 'tvshow'
            new_item.context = renumbertools.context(new_item)
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
            new_item.contentType = 'movie'

        new_item.context = filtertools.context(new_item, list_language, list_quality)
        new_item.context.extend(autoplay.context)

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist


def search(item, texto):
    logger.info()
    
    try:
        if texto != "":
            item.first = 0
            item.url = "{}?s={}".format(item.url, urllib.quote_plus(texto))
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def play(item):
    logger.info()
    
    itemlist = []
    item.setMimeType = 'application/vnd.apple.mpegurl'
    
    if not 'embed.php' in item.url:
        return [item]

    data = get_source(item.url)
    if not data:
        return itemlist

    item.url = scrapertools.find_single_match(data, 'vp.setup\(\{.+?"file":"([^"]+).+?\);').replace("\\/", "/")
    item.server = ''

    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def get_tags(page, sname):
    logger.info()
    tags = ""
    title = page.find("title").text
    # logger.error('%s(.*?)Veranime' % sname)
    match = scrapertools.find_single_match(title, r'%s\s*(.*?)\|' % sname)
    if match:
        tags = '[COLOR gold]%s[/COLOR]' % match
    return tags