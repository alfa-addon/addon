# -*- coding: utf-8 -*-
# -*- Channel TVAnime -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Development Group -*-

import re
import base64

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from modules import filtertools
from modules import autoplay
from core import tmdb
from modules import renumbertools
from platformcode import platformtools
import bs4

canonical = {
    "channel": "tvanime",
    "host": config.get_setting("current_host", "tvanime", default=""),
    "host_alt": ["https://ww3.monoschinos3.com/"],
    "host_black_list": ["https://monoschinos2.com"],
    "pattern": '<meta\s*property="og:url"\s*content="([^"]+)"',
    "set_tls": True,
    "set_tls_min": True,
    "retries_cloudflare": 1,
    "CF": False,
    "CF_test": False,
    "alfa_s": True,
}

host = canonical['host'] or canonical['host_alt'][0]
host = host.rstrip("/")

IDIOMAS = {"VOSE": "VOSE", "Latino": "LAT", "Castellano": "CAST"}

epsxfolder = config.get_setting("epsxfolder", canonical["channel"])
list_epsxf = {0: None, 1: 25, 2: 50, 3: 100}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ["directo", "fembed", "streamtape", "uqload", "okru", "streamsb"]


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(
            channel=item.channel,
            title="Nuevos Episodios",
            action="new_episodes",
            thumbnail=get_thumb("new_episodes", auto=True),
            url=host,
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Ultimas",
            action="list_all",
            thumbnail=get_thumb("last", auto=True),
            url=host + "/animes?estado[]=2&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Todas",
            action="list_all",
            thumbnail=get_thumb("all", auto=True),
            url=host + "/animes",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Anime",
            action="list_all",
            thumbnail=get_thumb("anime", auto=True),
            url=host + "/animes?tipo[]=1&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Donghua",
            action="list_all",
            thumbnail=get_thumb("anime", auto=True),
            url=host + "/animes?tipo[]=9&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Películas",
            action="list_all",
            thumbnail=get_thumb("movies", auto=True),
            url=host + "/animes?tipo[]=3&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="OVAs",
            action="list_all",
            thumbnail=get_thumb("anime", auto=True),
            url=host + "/animes?tipo[]=2&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="ONAs",
            action="list_all",
            thumbnail=get_thumb("anime", auto=True),
            url=host + "/animes?tipo[]=6&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Especiales",
            action="list_all",
            thumbnail=get_thumb("anime", auto=True),
            url=host + "/animes?tipo[]=4&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Latino",
            action="list_all",
            thumbnail=get_thumb("latino", auto=True),
            url=host + "/animes?q=latino",
        )
    )
    
    itemlist.append(
        Item(
            channel=item.channel,
            title="Castellano",
            action="list_all",
            thumbnail=get_thumb("cast", auto=True),
            url=host + "/animes?genre[]=42&order=created",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Año",
            action="section",
            thumbnail=get_thumb("year", auto=True),
            url=host + "/animes",
            section="yearDropdown",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Generos",
            action="section",
            thumbnail=get_thumb("genres", auto=True),
            url=host + "/animes",
            section="genreDropdown",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Buscar",
            action="search",
            url=host,
            thumbnail=get_thumb("search", auto=True),
            fanart="https://s30.postimg.cc/pei7txpa9/buscar.png",
        )
    )

    itemlist.append(
        Item(
            channel=item.channel,
            title="Configurar Canal...",
            text_color="turquoise",
            action="settingCanal",
            thumbnail=get_thumb("setting_0.png"),
            url="",
            fanart=get_thumb("setting_0.png"),
        )
    )

    autoplay.show_option(item.channel, itemlist)
    itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(
            url, referer=referer, canonical=canonical, soup=True
        ).data
    else:
        data = httptools.downloadpage(url, canonical=canonical, soup=True).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = bs4.BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def new_episodes(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    container = soup.find("h2", string="Últimos capítulos🔥").parent.ul

    for elem in container.find_all("article"):
        url = elem.a["href"]
        lang, c_title = clear_title(elem.h3.text)
        c_title = re.sub("(?i)1080p|720p|movie", "", c_title).strip()
        c_title, season = get_season_from_title(c_title)
        epi = elem.select_one("a > div > span")
        if epi:
            epi = int(epi.getText(strip=True))
        else:
            epi = 1
        
        title = "%sx%s - %s" % (season, epi, c_title)
        thumb = host + elem.find("img")["src"]

        itemlist.append(
            Item(
                channel=item.channel,
                title=title,
                url=url,
                action="findvideos",
                thumbnail=thumb,
                contentSerieName=c_title,
                language=lang,
                contentSeason=season,
                contentEpisodeNumber=epi,
                contentType="episode",
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    container = soup.find("div", class_="container").find("ul")

    for elem in container.find_all("li", recursive=False):
        if elem.find("article"):
            elem = elem.article
        url = elem.a["href"]
        lang, title = clear_title(elem.a.get("title", "") or elem.find("h3").text)
        title = re.sub(
            "(?i)1080p|720p|movie|ovas|ova|onas|ona|especiales|especial|specials|special",
            "",
            title,
        ).strip()
        thumb = host + elem.find("img")["src"]

        
        info = elem.a.span
        c_type = "movie" if info and \
                 ' · ' in info.string and \
                 info.string.split(' · ')[0] == 'Pelicula' else \
                 "tvshow"
        
        if c_type == "movie":
            # https://ww3.monoschinos3.com/anime/4593/black-clover-mahou-tei-no-ken
            # https://ww3.monoschinos3.com/ver/4593/black-clover-mahou-tei-no-ken/episodio-1
            if "/anime/" in url:
                url = url.replace('/anime/', '/ver/') + '/episodio-1'
            itemlist.append(
                Item(
                    channel=item.channel,
                    title=title,
                    url=url,
                    action="findvideos",
                    language=lang,
                    thumbnail=thumb,
                    contentTitle=title,
                    contentType=c_type,
                    infoLabels={"year": "-"},
                )
            )
        else:
            c_title, season = get_season_from_title(title)
            itemlist.append(
                Item(
                    channel=item.channel,
                    title=title,
                    url=url,
                    action="folders",
                    context=renumbertools.context(item),
                    language=lang,
                    thumbnail=thumb,
                    contentSerieName=c_title,
                    contentSeaon=season,
                    contentType=c_type,
                    infoLabels={"season": season},
                )
            )

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        link_next_page = soup.find("a", rel="next")
        if link_next_page and \
           link_next_page.get("href", "") and \
           len(itemlist) > 8:
            itemlist.append(
                Item(
                    channel=item.channel,
                    title="Siguiente >>",
                    url=link_next_page["href"],
                    action="list_all",
                )
            )
    except (AttributeError, KeyError, TypeError):
        pass

    return itemlist


def section(item):
    itemlist = list()

    soup = create_soup(item.url)

    genrediv = soup.find("div", attrs={"aria-labelledby": item.section})
    matches1 = genrediv.find_all("input")
    matches2 = genrediv.find_all("label")
    matches = zip(matches1, matches2)

    for elem in matches:
        url = host + "/animes?%s=%s&order=created" % (elem[0]["name"], elem[0]["value"])
        title = elem[1].text

        itemlist.append(
            Item(channel=item.channel, title=title, url=url, action="list_all")
        )
    

    return itemlist


def episodios(item):
    logger.info()
    itemlist = list()

    templist = folders(item)

    for tempitem in templist:
        if tempitem.infoLabels["episode"]:
            itemlist = templist
            break
        itemlist += episodesxfolder(tempitem)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("button", class_="play-video")

    for elem in matches:
        url = base64.b64decode(elem["data-video"]).decode("utf-8")

        itemlist.append(
            Item(
                channel=item.channel,
                title="%s",
                url=url,
                action="play",
                language=item.language,
                infoLabels=item.infoLabels,
            )
        )

    itemlist = servertools.get_servers_itemlist(
        itemlist, lambda x: x.title % x.server.capitalize()
    )

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def search(item, texto):
    logger.info()

    try:
        if texto != "":
            texto = texto.replace(" ", "+")
            item.url = item.url + "/animes?q=" + texto
            return list_all(item)
        else:
            return []
    except Exception:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    itemlist = []
    item = Item()

    if categoria == "anime":
        item.url = host
        itemlist = new_episodes(item)

    return itemlist


def settingCanal(item):
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return


def clear_title(title):
    if "latino" in title.lower():
        lang = "Latino"
    elif "castellano" in title.lower():
        lang = "Castellano"
    else:
        lang = "VOSE"

    title = re.sub(r"Audio|Latino|Castellano|\((.*?)\)", "", title)
    title = re.sub(r"\s:", ":", title)

    return lang, title


def folders(item):
    logger.info()
    itemlist = list()

    exf = list_epsxf.get(epsxfolder, None)
    if not epsxfolder:
        return episodesxfolder(item)

    soup = create_soup(item.url)
    matches = soup.find_all("a", class_="ko")

    l_matches = len(matches)

    if l_matches <= exf:
        return episodesxfolder(item)
    div = l_matches // exf
    res = l_matches % exf
    tot_div = div

    count = 1
    for folder in list(range(0, tot_div)):
        final = count * exf
        inicial = (final - exf) + 1
        if count == tot_div:
            final = (count * exf) + res

        title = "Eps %s - %s" % (inicial, final)
        init = inicial - 1
        itemlist.append(
            Item(
                channel=item.channel,
                title=title,
                url=item.url,
                action="episodesxfolder",
                init=init,
                fin=final,
                type=item.type,
                thumbnail=item.thumbnail,
                foldereps=True,
            )
        )
        count += 1

    if (
        item.contentSerieName != ""
        and config.get_videolibrary_support()
        and len(itemlist) > 0
        and not item.extra == "episodios"
    ):
        itemlist.append(
            Item(
                channel=item.channel,
                title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                url=item.url,
                action="add_serie_to_library",
                extra="episodios",
                contentSerieName=item.contentSerieName,
                extra1="library",
            )
        )

    return itemlist


def episodesxfolder(item):
    logger.info()

    itemlist = list()

    if not item.init:
        item.init = None
    if not item.fin:
        item.fin = None

    soup = create_soup(item.url)
    matches = soup.find_all("a", class_="ko")

    infoLabels = item.infoLabels

    for cap in matches[item.init : item.fin]:
        scrapedurl = cap["href"]
        thumb = host + cap.div.img["src"]
        episode = cap.h2.getText(strip=True).split('\n')[1].strip()
        try:
            season, episode = renumbertools.numbered_for_trakt(
                item.channel, item.contentSerieName, item.contentSeason, int(episode)
            )
            season = int(season)
            episode = int(episode)
        except ValueError:
            season = 1
            episode = 1
        title = "%sx%s - %s" % (season, str(episode).zfill(2), item.contentSerieName)
        url = scrapedurl
        infoLabels["season"] = season
        infoLabels["episode"] = episode

        itemlist.append(
            Item(
                channel=item.channel,
                title=title,
                contentSerieName=item.contentSerieName,
                thumbnail=thumb,
                url=url,
                action="findvideos",
                language=item.language,
                infoLabels=infoLabels,
                contentType="episode",
            )
        )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if not item.extra:
        if (
            item.contentSerieName != ""
            and config.get_videolibrary_support()
            and len(itemlist) > 0
            and not item.foldereps
        ):
            itemlist.append(
                Item(
                    channel=item.channel,
                    title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]",
                    url=item.url,
                    action="add_serie_to_library",
                    extra="episodios",
                    contentSerieName=item.contentSerieName,
                    extra1="library",
                )
            )

    return itemlist


def get_season_from_title(title):
    """
    Extracts the season number from the title.
    :param title: The title of the anime.
    :return: The title and the season number or 1 if not found.
    """
    
    patern1 = r'(?i)\s*(\d+)\s*(?:st|nd|rd|th)\s+season'
    patern2 = r'(?i)(?:season|temporada|part|parte)\s*(\d+)'
    
    season = scrapertools.find_single_match(title, patern1)
    if not season:
        season = scrapertools.find_single_match(title, patern2)
        if season:
            title = re.sub(patern2, '', title)
    else:
        title = re.sub(patern1, '', title)
    
    return title.strip(), int(season) if season else 1