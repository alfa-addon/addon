# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from platformcode import config, logger, platformtools
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools, tmdb
from bs4 import BeautifulSoup
from channels import autoplay
from channels import filtertools
from channelselector import get_thumb
import codecs


list_language = []
list_servers = []
list_quality = []

canonical = {
             'channel': 'salynpm', 
             'host': config.get_setting("current_host", 'salynpm', default=''), 
             'host_alt': ["https://plyrs.blogspot.com/"], 
             'host_black_list': ["https://salynpm-links.blogspot.com/", "https://salyn-pm.blogspot.com/"], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
__channel__ = canonical['channel']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


# /search?updated-max=2022-05-20T19%3A29%3A00-07%3A00&max-results=40#PageNo=2

def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel = item.channel,title="Películas" , action="lista", url=host ))
    itemlist.append(Item(channel = item.channel,title="Géneros" , action="generos", url=host + "p/categorias.html"))
    itemlist.append(Item(channel = item.channel,title="Buscar", action="search"))
    
    itemlist.append(Item(channel = item.channel,title="Configurar canal...", text_color="gold", action="configuracion", thumbnail=get_thumb('setting_0.png')))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "search?q=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def generos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='col')
    matches = soup.find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text
        url = url.replace("www.salynpm", "salyn-pm.blogspot")
        thumbnail = ""
        itemlist.append(Item(channel = item.channel,action="lista", title=title, url=url,
                              thumbnail=thumbnail ) )
    return itemlist


def create_soup(url):
    logger.info()
    data = httptools.downloadpage(url, ignore_response_code=True, canonical=canonical).data
    if "document.write" in data:
        data =  scrapertools.find_single_match(data, r"document\.write\('([^']+)'")
        data = codecs.decode(data.replace("\u000D", "\n"), "unicode_escape")
    if not "Error 404" in data:
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    else:
        soup = ""
    return soup


# <div class='card-content'>
# <a href='https://plyrs.blogspot.com/2022/06/american-pie-tu-primera-vez.html' title='American Pie: Tu primera vez'>
# <img alt='American Pie: Tu primera vez' src='https://4.bp.blogspot.com/-DDf24jYeWWQ/Xriq1FKHSpI/AAAAAAAAIdo/5bQ3oJFMCtQc2GnDw9IVGOMwuv6FrV0PACLcBGAsYHQ/w193/Dolittle.jpg'/></a>
# <h3 class='card-title'>American Pie: Tu primera vez</h3>
# <div class='card-quality m16'>
# <span class='btn btn-color btn-tiny'>1999</span>
# </div>
# </div>
# <div class='c12 c6-xs c3-md card'>
# <div class='card-content'>
# <a href='https://plyrs.blogspot.com/2022/06/the-boys-temporada-1.html' title='The Boys Temporada 1'>
# <img alt='The Boys Temporada 1' src='https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjmVrUlWqhVcyorFRPuifH6q6meFa1Rv6FyYVzMRh_XhGL8_3b-gaoMw6iOq23npU7rhXvS9vgYzOVyCca8NV9-ppIuWZi0B0FJvqKLpCRvcCigRByuWPjw9_3BVBAcwkAf9V5sLxxdDui43QKwvxCzJQPez16Z6gWFUO37dZDSyMPjj2rX8VmzW8jv/w193/The%20Boys.jpg'/></a>
# <h3 class='card-title'>The Boys Temporada 1</h3>
# <div class='card-quality m16'>
# <span class='btn btn-color btn-tiny'>2019</span>
# </div>
# </div>



def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='card-content')
    for elem in matches:
        # year = ""
        season = ""
        contentSerieName = ""
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        year = elem.find('div', class_='card-quality')
        if year:
            year = year.text.strip()
        else:
            year = '-'
        # logger.debug(title +"     "+ url + "       " + year)
        if "Temporada" in title:
            season = scrapertools.find_single_match(title, ".*? Temporada (\d+)")
            title = scrapertools.find_single_match(title, "(.*?) Temporada \d+")
            contentSerieName = title
            if season != "1":
                year = "-"
            # logger.debug(contentSerieName +"     "+ season + "       " + year)
        logger.debug(year)
        new_item = item.clone(url=url, title=title, thumbnail=thumbnail, infoLabels={"year": year})
        if "season":
            infoLabels = item.infoLabels
            new_item.action = "seasons"
            infoLabels["season"] = season
            new_item.contentSerieName = contentSerieName
        else:
            new_item.action = "findvideos"
            new_item.contentTitle = title
        itemlist.append(new_item)

        # itemlist.append(Item(channel = item.channel,action="findvideos", title=title, url=url,
                              # thumbnail=thumbnail, fanart=thumbnail, contentTitle = contentTitle,
                              # quality=quality, infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, True)

    # current_page = scrapertools.find_single_match(item.url, "PageNo=(\d+)")
    # base_next_page = soup.find('i', class_='fas fa-arrow-right')
    # if base_next_page:
        # base_next_page = base_next_page.parent['href']
    # num = len(itemlist)
    # if not current_page and num >= 24 :
        # next_page = base_next_page.replace("&start=24", "").replace("&by-date=false", "#PageNo=2")
        # itemlist.append(Item(channel = item.channel,action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    # if "search?q=" in item.url:
        # next_page = base_next_page
        # if num >= 20:
            # itemlist.append(Item(channel = item.channel,action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    # else:
        # base_next_page = base_next_page.replace("&start=24", "").replace("&by-date=false", "")
        # if current_page:
            # next = str(int(current_page) + 1)
            # next_page = base_next_page.replace("PageNo=%s" % current_page, "PageNo=%s" % next)
            # itemlist.append(Item(channel = item.channel,action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = list()
    # soup = create_soup(item.url).find("div", id="seasons")
    # matches = soup.find_all("div", class_="se-c")
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    # for elem in matches:
        # season = elem.find("span", class_="se-t").text
    title = "Temporada %s" % season
        # infoLabels["season"] = season
    itemlist.append(Item(channel = item.channel,title=title, url=item.url, action="episodesxseasons", infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel = item.channel,title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                        action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    return itemlist


# <ul id="vplaylist">
# <li class="active"><a href="https://archive.org/download/tbs-3x-1/TBS-3x1.mp4"> 1. Revancha</a></li>
# <li><a href="https://archive.org/download/tbs-3x-2/TBS-3x2.mp4" > 2. El único en el cielo</a></li>
# <li><a href="https://archive.org/download/tbs-3x-3/TBS-3x3.mp4"> 3. Costa Bereber</a></li>
# <li><a href="https://archive.org/download/tbs-3x-4/TBS%203x4.mp4"> 4. Un plan glorioso de cinco años</a></li>

# </ul>


def episodesxseasons(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find("ul", id="vplaylist")
    matches = soup.find_all("li")
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    for elem in matches:
        # if elem.find("span", class_="se-t").text != str(season):
            # continue
        # epi_list = elem.find("ul", class_="episodios")
        # for epi in epi_list.find_all("li"):
            # info = epi.find("div", class_="episodiotitle")
            # url = info.a["href"]
        url = elem.a['href']
        epi_name = elem.text.split(". ")[1]
        epi_num = elem.text.split(". ")[0]
        infoLabels["episode"] = epi_num
        title = "%sx%s - %s" % (season, epi_num, epi_name)
        logger.debug(url + "      " + title)
        itemlist.append(Item(channel = item.channel,title=title, url=url, action="play", infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)
    return itemlist

# https://plyrs.blogspot.com/2022/06/american-pie-tu-primera-vez.html
# <video class="js-player" id="video" controls=""preload="auto">
    # <source src="https://dl.dropboxusercontent.com/s/kzokqmp2d5fi1t7/SalynPM-AERAPE1.mp4?dl=1" type="video/mp4">
  # <source src="https://bit.ly/3djsH4X" type="video/mp4">
    # <source src="https://bit.ly/2SGiuYv" type="video/mp4">
    # <source src="https://www.googleapis.com/drive/v3/files/14JZ2X19ezRk-EpOFVbzm4L8dwzDAAhwF?alt=media&key=AIzaSyBQuJN3fqg0Ykk7cbYhAoDJRGL44ZeAONg" type="video/mp4">
    # <source src="https://tamconalepedu-my.sharepoint.com/:v:/g/personal/kgonzalezl14_tam_conalep_edu_mx/ERCxbEkvPZ1NkgtEgbQ2S7UBoTPLg5Am1B3ZjNfviXM-fg?download=1" type="video/mp4">
  # </video>

# https://plyrs.blogspot.com/2022/05/los-croods.html
# <div class="movie-thumbnail">
# <img src="https://3.bp.blogspot.com/-ILX1ZMZ_47U/WzkQluEgZeI/AAAAAAAACfc/0BiZCuWw0kMq-EFF-unQZDCaHu2I5-gTQCLcBGAs/s320/los-croods.jpeg" title="Los Croods">
# <a href="https://dl.dropbox.com/s/p6qzp5dgpemdgza/Los%20Croods.torrent?dl=0" target="_blank" class="movie-imdb"> Descargar Torrent</a>
# </div>


def findvideos(item):
    logger.info()
    itemlist = []
    audios = ["VOSE","LAT"]
    listed = []
    soup = create_soup(item.url)
    descargas = ""
    if soup.find(src=re.compile("salynpm-links.")):
        descargas = soup.find(src=re.compile("salynpm-links."))['src']
    if soup.find(href=re.compile("salynpm-links.")):
        descargas = soup.find(href=re.compile("salynpm-links."))['href']
    if descargas:
        descargas = create_soup(descargas)
        data = descargas.find('div', class_='post-entry')
        matches = data.find_all('a')
        for elem in matches:
            url = elem['href']
            url = codecs.decode(url,"unicode-escape")
            url = url.replace("?download=1", "").replace("dropboxusercontent", "dropbox").replace("/dl.dropbox", "/www.dropbox")
            if url != "" and url not in listed:
                listed.append(url)
    online = soup.find_all(type='video/mp4')
    codigo = soup.find(string=re.compile("document.write"))
    if codigo:
        codigo = scrapertools.find_single_match(codigo, r"document\.write\(unescape\('([^']+)'")
        codigo = codecs.decode(codigo.replace("%", ""), "hex")
        codigo = BeautifulSoup(codigo, "html5lib", from_encoding="utf-8")
        online = codigo.find_all(type='video/mp4')
    if online:
        for elem in online:
            url = elem['src']
            if "bit.ly" in url:
                url = httptools.downloadpage(url, follow_redirects=False).headers["location"]
            url = codecs.decode(url,"unicode-escape")
            url = url.replace("?download=1", "").replace("dropboxusercontent", "dropbox").replace("/dl.dropbox", "/www.dropbox")
            if url != "" and url not in listed:
                listed.append(url)
    for url in listed:
        if not "bit.ly" in url and not "https://archive.org/download/salynpm" in url:
            itemlist.append(Item(channel = item.channel,action="play", title = "%s", language=audios, url = url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(Item(channel = item.channel,action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist

