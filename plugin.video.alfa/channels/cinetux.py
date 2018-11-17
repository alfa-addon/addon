# -*- coding: utf-8 -*-

import re
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'Latino': 'Latino', 'Subtitulado': 'Subtitulado', 'Español': 'Español', 'SUB': 'SUB' }
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'okru', 'vidoza', 'openload', 'powvideo', 'netutv','gvideo']


CHANNEL_HOST = "http://www.cinetux.to/"

# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'cinetux')
__perfil__ = config.get_setting('perfil', 'cinetux')

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', 'cinetux')]


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    item.viewmode = viewmode
    data = httptools.downloadpage(CHANNEL_HOST + "pelicula").data
    total = scrapertools.find_single_match(data, "Películas</h1><span>(.*?)</span>")
    titulo = "Peliculas (%s)" %total
    itemlist.append(item.clone(title=titulo, text_color=color2, action="", text_bold=True))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "pelicula",
                               thumbnail=get_thumb('newest', auto=True),
                               text_color=color1))
    itemlist.append(item.clone(action="destacadas", title="      Destacadas", url=CHANNEL_HOST + "mas-vistos/",
                               thumbnail=get_thumb('hot', auto=True),
                               text_color=color1))
    itemlist.append(item.clone(action="idioma", title="      Por idioma", text_color=color1,
                               thumbnail=get_thumb('language', auto=True)))
    itemlist.append(item.clone(action="generos", title="      Por géneros", url=CHANNEL_HOST,
                               thumbnail=get_thumb('genres', auto=True),
                               text_color=color1))

    itemlist.append(item.clone(title="Documentales", text_bold=True, text_color=color2, action=""))
    itemlist.append(item.clone(action="peliculas", title="      Novedades", url=CHANNEL_HOST + "genero/documental/", text_color=color1,
                               thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(item.clone(action="peliculas", title="      Por orden alfabético", text_color=color1, url=CHANNEL_HOST + "genero/documental/?orderby=title&order=asc&gdsr_order=asc",
                               thumbnail=get_thumb('alphabet', auto=True)))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(action="search", title="Buscar...", text_color=color3,
                               thumbnail=get_thumb('search', auto=True)))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = CHANNEL_HOST + "?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = CHANNEL_HOST
            item.action = "peliculas"

        elif categoria == 'documentales':
            item.url = CHANNEL_HOST + "genero/documental/"
            item.action = "peliculas"

        elif categoria == 'infantiles':
            item.url = CHANNEL_HOST + "genero/animacion/"
            item.action = "peliculas"

        elif categoria == 'terror':
            item.url = CHANNEL_HOST + "genero/terror/"
            item.action = "peliculas"

        elif categoria == 'castellano':
            item.url = CHANNEL_HOST + "idioma/espanol/"
            item.action = "peliculas"

        elif categoria == 'latino':
            item.url = CHANNEL_HOST + "idioma/latino/"
            item.action = "peliculas"

        itemlist = peliculas(item)
        if itemlist[-1].action == "peliculas":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    patron = '(?s)class="(?:result-item|item movies)">.*?<img src="([^"]+)'
    patron += '.*?alt="([^"]+)"'
    patron += '(.*?)'
    patron += 'href="([^"]+)"'
    patron += '.*?(?:<span>|<span class="year">)(.+?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, quality, scrapedurl, scrapedyear in matches:
        quality = scrapertools.find_single_match(quality, '.*?quality">([^<]+)')
        try:
            fulltitle = scrapedtitle
            year = scrapertools.find_single_match(scrapedyear,'\d{4}')
            if "/" in fulltitle:
                fulltitle = fulltitle.split(" /", 1)[0]
            scrapedtitle = "%s (%s)" % (fulltitle, year)
        except:
            fulltitle = scrapedtitle
        if quality:
            scrapedtitle += "  [%s]" % quality
        new_item = item.clone(action="findvideos", title=scrapedtitle, fulltitle=fulltitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentType="movie", quality=quality)
        if year:
            new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone(action="peliculas", title=">> Página siguiente", url=next_page_link,
                                   text_color=color3))
    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'peliculas_destacadas.*?class="letter_home"')
    patron = '(?s)title="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'
    patron += 'src="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        scrapedurl = CHANNEL_HOST + scrapedurl
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, fulltitle=scrapedtitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentType="movie"
                              ))
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link:
        itemlist.append(
            item.clone(action="destacadas", title=">> Página siguiente", url=next_page_link, text_color=color3))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?s)dos_columnas">(.*?)</ul>')
    patron = '<li><a.*?href="/([^"]+)">(.*?)</li>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        scrapedurl = CHANNEL_HOST + scrapedurl
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        scrapedtitle = unicode(scrapedtitle, "utf8").capitalize().encode("utf8")
        if scrapedtitle == "Erotico" and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(item.clone(action="peliculas", title=scrapedtitle, url=scrapedurl))
    return itemlist


def idioma(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="peliculas", title="Español", url= CHANNEL_HOST + "idioma/espanol/"))
    itemlist.append(item.clone(action="peliculas", title="Latino", url= CHANNEL_HOST + "idioma/latino/"))
    itemlist.append(item.clone(action="peliculas", title="VOSE", url= CHANNEL_HOST + "idioma/subtitulado/"))
    return itemlist


def findvideos(item):
    import urllib
    logger.info()
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    patron = 'class="title">.*?src.*?/>([^>]+)</span>.*?data-type="([^"]+).*?data-post="(\d+)".*?data-nume="(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    #logger.info("Intel66")
    #scrapertools.printMatches(matches)
    for language, tp, pt, nm in matches:
        language = language.strip()
        post = {'action':'doo_player_ajax', 'post':pt, 'nume':nm, 'type':tp}
        post = urllib.urlencode(post)
        new_data = httptools.downloadpage(CHANNEL_HOST+'wp-admin/admin-ajax.php', post=post, headers={'Referer':item.url}).data
        if not config.get_setting('unify'):
            if item.quality == '':
                quality = 'SD'
            else:
                quality = item.quality
            title = ' [%s][%s]' % (quality, IDIOMAS[language])
        else:
            title = ''
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        #logger.info("Intel33 %s" %url)
        url = get_url(url)
        if "mega" not in url and "mediafire" not in url:
            itemlist.append(Item(channel=item.channel, title ='%s'+title, url=url, action='play', quality=item.quality,
                                 language=IDIOMAS[language], infoLabels=item.infoLabels))
    #logger.info("Intel44")
    #scrapertools.printMatches(itemlist)
    patron = "<a class='optn' href='([^']+)'.*?<img src='.*?>([^<]+)<.*?<img src='.*?>([^<]+)<"
    matches = re.compile(patron, re.DOTALL).findall(data)
    #logger.info("Intel66a")
    #scrapertools.printMatches(matches)
    for hidden_url, quality, language in matches:
        if not config.get_setting('unify'):
            title = ' [%s][%s]' % (quality, IDIOMAS[language])
        else:
            title = ''
        new_data = httptools.downloadpage(hidden_url).data
        url = scrapertools.find_single_match(new_data, 'id="link" href="([^"]+)"')
        url = url.replace('\\/', '/')
        url = get_url(url)
        if "mega" not in url and "mediafire" not in url:
            itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', quality=quality,
                                 language=IDIOMAS[language], infoLabels=item.infoLabels))
    #logger.info("Intel55")
    #scrapertools.printMatches(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def get_url(url):
    if "cinetux.me" in url:
        d1 = httptools.downloadpage(url).data
        if "mail" in url:
            id = scrapertools.find_single_match(d1, '<img src="[^#]+#(\w+)')
            #logger.info("Intel77b %s" %id)
            url = "https://my.mail.ru/video/embed/" + id
        else:
            url = scrapertools.find_single_match(d1, 'document.location.replace\("([^"]+)')
        #logger.info("Intel22a %s" %d1)
        #logger.info("Intel77a %s" %url)
    url = url.replace("povwideo","powvideo")
    return url
