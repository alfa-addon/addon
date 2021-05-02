# -*- coding: utf-8 -*-
# -*- Channel Cliver -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re, time

from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools
from channelselector import get_thumb
from lib import generictools

direct_play = config.get_setting('direct_play', channel='cliver')
IDIOMAS = {'es': 'CAST', 'lat': 'LAT', 'es_la': 'LAT', 'vose': 'VOSE', 'ingles': 'VOS'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['openload', 'rapidvideo', 'directo']

host = 'https://www.cliver.to/'
xhr_list = host + 'frm/cargar-mas.php'
#xhr_ep = host + 'frm/obtener-lista-capitulos.php'
xhr_film = host + 'frm/obtener-enlaces-pelicula.php'
xhr_srv = 'https://directvideo.stream/getFile.php'

def mainlist(item):
    logger.info()
    itemlist = []
    #No series
    #type_content = config.get_setting('default_content', channel='cliver')
    type_content = 0
    if type_content > 0:
        mod = 'series'
        thumbm = 'tvshows'
        alt_mod = "Peliculas"
    else:
        mod = "peliculas"
        thumbm = 'movies'
        alt_mod = 'Series'

    #if item.tcont:
        #type_content = item.tcont
    par_type = {"mas-vistas": "mas-vistas-series", "genero": "generosSeries", "anio": "anioSeries", "buscador": "buscadorSeries"}
    listpar = list(par_type.items())

    autoplay.init(item.channel, list_servers, list_quality)

    #Titulo principal series/peliculas
    # itemlist.append(Item(channel=item.channel,title="[COLOR springgreen][B]%s[/B][/COLOR]" % mod.upper(),
    #                 action="", plot=item.plot,
    #                 url='', folder=False,
    #                 thumbnail=get_thumb(thumbm, auto=True)
    #                 ))

    if type_content == 0:
        itemlist.append(Item(channel=item.channel, title="Estrenos",
                            action="list_all",
                            thumbnail=get_thumb('premieres', auto=True),
                            url=xhr_list, page=0, tipo='estrenos',
                            tmod=mod, plot=item.plot
                            ))

    itemlist.append(Item(channel=item.channel,title="Más Vistas",
                    action="list_all",
                    thumbnail=get_thumb('more_watched', auto=True),
                    url=xhr_list, page=0, tipo=listpar[1][type_content],
                    tmod=mod, plot=item.plot
                    ))
    if type_content == 0:
        itemlist.append(Item(channel=item.channel,title="Tendencias",
                        action="list_all",
                        thumbnail=get_thumb('more_voted', auto=True),
                        url=xhr_list, page=0, tipo='peliculas-tendencias',
                        tmod=mod, plot=item.plot
                        ))
    if type_content != 0:
        itemlist.append(Item(channel=item.channel,title="Nuevos Capitulos",
                        action="list_all",
                        thumbnail=get_thumb('new episodes', auto=True),
                        url=xhr_list, page=0, tipo='nuevos-capitulos',
                        tmod=mod, plot=item.plot
                        ))

    itemlist.append(Item(channel=item.channel, title="Por Género",
                         action="seccion",
                         thumbnail=get_thumb('genres', auto=True),
                         url=host, page=0, tipo=listpar[2][type_content],
                         tmod=mod, plot=item.plot
                        ))

    itemlist.append(Item(channel=item.channel,title="Por Año",
                    action="seccion",
                    thumbnail=get_thumb('year', auto=True),
                    url=host, page=0, tipo=listpar[0][type_content],
                    tmod=mod, plot=item.plot
                    ))
    if type_content != 0:
        itemlist.append(Item(channel=item.channel,title="Por Canal",
                        action="seccion",
                        thumbnail=get_thumb('tvshows', auto=True),
                        url=host, page=0, tipo='networkSeries',
                        tmod=mod, plot=item.plot
                        ))

    itemlist.append(Item(channel=item.channel,title="Buscar",
                    action="search", page=0, tmod=mod,
                    url=host+'buscar/?txt=', tipo=listpar[3][type_content],
                    thumbnail=get_thumb('search', auto=True), plot=item.plot
                    ))

    autoplay.show_option(item.channel, itemlist)

    #No series
    # itemlist.append(Item(channel=item.channel,title="[COLOR grey]Cambiar a Modo %s[/COLOR]" % alt_mod,
    #                 action="switchmod", plot=item.plot,
    #                 url='', tcont=type_content,
    #                 thumbnail=get_thumb('update.png', "thumb_")
    #                 ))
    return itemlist


def switchmod(item):
    logger.info()
    if item.tcont > 0:
        type_content = 0
        config.set_setting('default_content', type_content, channel='cliver')
    else:
        type_content = 1
        config.set_setting('default_content', type_content, channel='cliver')
    return mainlist(item)

def get_source(url, post=None, ctype=None):
    logger.info()
    headers = {"Cookie": "tipo_contenido=%s" % ctype}

    data = httptools.downloadpage(url, post=post).data

    if 'Javascript is required' in data:
        generictools.js2py_conversion(data, url, domain_name=".cliver.to")
        data = httptools.downloadpage(url, post=post).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()
    itemlist = []
    
    post = "tipo=%s&pagina=%s" % (item.tipo, item.page)
    if item.adicional:
        post+= '&adicional=%s' % item.adicional

    data = get_source(xhr_list, post=post)

    if len(data) < 10:
        data = get_source(item.url, ctype=item.tmod)
        data = scrapertools.find_single_match(data, '<section class="panel-der">(.*?)</section')

    patron = '<img src="([^"]+)" alt="([^"]+)"'# thumb, title
    patron += '(.*?)' #info
    patron += '<a href="([^"]+)".*?<span>(.*?)</sp' #url, year
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedinfo, scrapedurl, scrapedyear in matches:
        title = scrapedtitle
        if item.tipo == 'nuevos-capitulos':
            try:
                scrapedyear = scrapedyear.split(' - ')[1]
                scrapedtitle = re.sub(r'\dx\d+\s', "", scrapedtitle)
            except:
                pass
        #metodo alternativo (sin usar)
        content_id = scrapertools.find_single_match(scrapedthumbnail, '/(\d+)_')
        if not content_id:
            continue
        if not scrapedurl.startswith('http'):
            scrapedurl = host+scrapedurl
        title += ' [COLOR grey](%s)[/COLOR]' % scrapedyear
        list_langs = scrapertools.find_multiple_matches(scrapedinfo, '<div class="([^"]+)">\s*</div>')
        langs = ""
        if list_langs:
            langs += "["
            for i, elem in enumerate(list_langs):
                langs += IDIOMAS.get(elem, elem)+'/'
                list_langs[i] = IDIOMAS.get(elem, elem)
            langs = langs[:-1]+']'
            title += ' [COLOR springgreen]%s[/COLOR]' % langs
        thumbnail = scrapedthumbnail.replace('_min.','.')
        
        if 'serie' in scrapedurl:
            itemlist.append(item.clone(channel=item.channel,
                            title=title,
                            url=scrapedurl,
                            thumbnail=thumbnail,
                            action = 'seasons',
                            contentSerieName = scrapedtitle,
                            content_id = content_id,
                            ))
        else:
            itemlist.append(item.clone(channel=item.channel,
                            title=title,
                            url=scrapedurl,
                            thumbnail=thumbnail,
                            action = 'findvideos',
                            contentTitle = scrapedtitle,
                            content_id = content_id,
                            infoLabels = {'year': scrapedyear},
                            language= list_langs
                            ))

    tmdb.set_infoLabels(itemlist, True)
    if len(matches) == 18:
        page = item.page + 1
        itemlist.append(item.clone(action="list_all", 
                        title="[COLOR springgreen]Página Siguiente >>>[/COLOR]",
                        page=page))
    return itemlist


def seccion(item):
    logger.info()

    itemlist = []
    prefix = '<div class="anios">'
    if "nero" in item.title:
        prefix = '<div class="generos">'
    elif "Canal" in item.title:
        prefix = '<div class="networks">'
    data = get_source(item.url+item.tmod+'/', ctype=item.tmod)
    data = scrapertools.find_single_match(data, '%s(.*?)</div>' % prefix)
    patron = '<li\s*><a href="([^"]+)".*?>(.*?)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapertools.find_single_match(scrapedtitle, '<span class="cat">(.*?)</span>')
        count = scrapertools.find_single_match(scrapedtitle, '<span class="cat-count">(\d+)</span>')
        adicional = scrapertools.find_single_match(url, host+item.tmod+'/.*?/(.*?)/')
        if not title:
            title = scrapedtitle
        if count:
            title += '[COLOR darkgrey] (%s)[/COLOR]' % count
        itemlist.append(item.clone(action='list_all',
                            title=title,
                            url=url,
                            adicional=adicional,
                            ))
    return itemlist


def seasons(item):
    logger.info()
    itemlist = []

    data = get_source(item.url, ctype=item.tmod)
    patron = 'Temporada (\d+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if matches == 1:
        return episodesxseason(item)
    infoLabels = item.infoLabels
    for scrapedseason in matches:
        contentSeasonNumber = scrapedseason
        title = 'Temporada %s' % scrapedseason
        infoLabels['season'] = contentSeasonNumber

        itemlist.append(Item(channel=item.channel,
                             action='episodesxseason',
                             url=item.url,
                             title=title,
                             contentSeasonNumber=contentSeasonNumber,
                             infoLabels=infoLabels,
                             context=filtertools.context(item, list_language)
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             extra1='library'
                             ))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    season = item.contentSeasonNumber
    action = "findvideos"
    server = ''
    
    data = get_source(item.url, ctype=item.tmod)
    data = scrapertools.find_single_match(data, 'Temporada %s(.*?)<div class="clear"></div></div></div>' % season)
    patron = 'data-numcap="(\d+)".*?data-titulo="([^"]+)".*?' #episodio, titulo
    patron += 'data-idiomas="([^"]+)" (.*?)><i.*?'#langs, url-langs
    patron += '<img src="([^"]+)".*?<p>(.*?)</p>'#thumbs, plot
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for scrapedep, title, scrapedlangs, scrapedurls, thumb, plot in matches:
        language = ""
        contentEpisodeNumber = scrapedep
        if not ',' in scrapedlangs:
            language = " (%s)" % IDIOMAS.get(scrapedlangs, scrapedlangs)
            if direct_play:
                if config.get_setting('unify'):
                    title += "[COLOR grey] (Autoplay)[/COLOR]"
                scrapedurls = scrapertools.find_single_match(scrapedurls, 'data-url-%s="([^"]+)"' % scrapedlangs)
                action = 'play'
                server = servertools.get_server_from_url(scrapedurls)
                if item.extra:
                    action = 'findvideos'
        else:
            listl = scrapedlangs.split(",")
            prio = ""
            for lang in listl:
                lang = lang.strip()
                language += " (%s)" % IDIOMAS.get(lang, lang)
                if lang == 'es':
                    prio = lang
                elif lang == 'es_la' and not prio:
                    prio = 'es-la'
                elif lang == 'vose' and not prio:
                    prio = lang
            if direct_play:
                scrapedurls = scrapertools.find_single_match(scrapedurls, 'data-url-%s="([^"]+)"' % prio)
                action = 'play'
                if config.get_setting('unify'):
                    title += "[COLOR grey] (Autoplay)[/COLOR]"
                server = servertools.get_server_from_url(scrapedurls)
                if item.extra:
                    action = 'findvideos'
        infoLabels['episode'] = scrapedep
        infoLabels = item.infoLabels
        title += '[COLOR springgreen]%s[/COLOR]' % language
        itemlist.append(Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=scrapedurls,
                             plot=plot,
                             thumbnail=thumb,
                             contentEpisodeNumber=contentEpisodeNumber,
                             infoLabels=infoLabels,
                             server=server,
                             direct_play=direct_play
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist



def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.adicional = texto
    if texto != '':
        try:
            return list_all(item)
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
        if categoria in ['peliculas']:
            item.url = host +'/peliculas'
        elif categoria == 'infantiles':
            item.url = host + '/animacion/'
        elif categoria == 'terror':
            item.url = host + '/terror/'
        item.first=0
        itemlist = list_all(item)
        if 'Siguiente >>>' in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []

    if not item.contentSerieName:
        headers = {"Cookie": "tipo_contenido=%s" % item.tmod}
        post = {"pelicula": item.content_id}
        data = httptools.downloadpage(xhr_film, post=post, headers=headers).json

        for langs in data:
            language = IDIOMAS.get(langs, langs)
            for elem in data[langs]:
                token = elem['token']
                server = elem['reproductor_nombre'].lower()
                title = '%s[COLOR springgreen] (%s)[/COLOR]' % (server.capitalize(), language)
                
                if 'supervideo' in server:
                    server = 'directo'
                    
                itemlist.append(Item(channel=item.channel,
                        url='',
                        title= title,
                        contentTitle=item.contentTitle,
                        action='play',
                        infoLabels = item.infoLabels,
                        server=server,
                        token=token,
                        language=language
                        ))

    elif item.direct_play == True:
        item.action = 'play'
        return play(item)
    else:

        matches = scrapertools.find_multiple_matches(item.url, 'data-url-(.*?)="(.*?)"')

        for scrapedlang, scrapedurl in matches:
            if not scrapedurl:
                continue
            scrapedlang = scrapedlang.replace('-', '_')
            language = IDIOMAS.get(scrapedlang, scrapedlang)
            server = servertools.get_server_from_url(scrapedurl)
            title = '%s[COLOR springgreen] (%s)[/COLOR]' % (server.capitalize(), language)
            itemlist.append(Item(channel=item.channel,
                        url=scrapedurl,
                        title= title,
                        contentSerieName=item.contentSerieName,
                        action='play',
                        infoLabels = item.infoLabels,
                        server=server,
                        language=language
                        ))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos' and not item.contentSerieName:
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 content_id=item.content_id,
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))


    return itemlist

def play(item):
    if item.token:
        post = {"hash": item.token}
        new_data = httptools.downloadpage(xhr_srv, post=post).json
        item.url = new_data['url'].rstrip()
        item.url = item.url.replace(' ', '%20')
    return [item]

def js2py_conversion(data, domain=".cliver.to"):
    logger.info()
    from lib import js2py
    import base64
        
    patron = ",\s*S='([^']+)'"
    data_new = scrapertools.find_single_match(data, patron)

    if not data_new:
        logger.error('js2py_conversion: NO data_new')
        
    try:
        for x in range(10):                                          # Da hasta 10 pasadas o hasta que de error
            data_end = base64.b64decode(data_new).decode('utf-8')
            data_new = data_end
    except:
        js2py_code = data_new
    else:
        logger.error('js2py_conversion: base64 data_new NO Funciona: ' + str(data_new))
    
    if not js2py_code:
        logger.error('js2py_conversion: NO js2py_code BASE64')
        
    js2py_code = js2py_code.replace('document', 'window').replace(" location.reload();", "")
    js2py.disable_pyimport()
    context = js2py.EvalJs({'atob': atob})
    new_cookie = context.eval(js2py_code)
    
    logger.info('new_cookie: ' + new_cookie)

    dict_cookie = {'domain': domain,
                }

    if ';' in new_cookie:
        new_cookie = new_cookie.split(';')[0].strip()
        namec, valuec = new_cookie.split('=')
        dict_cookie['name'] = namec.strip()
        dict_cookie['value'] = valuec.strip()
    zanga = httptools.set_cookies(dict_cookie)
    
    
def atob(s):
    import base64
    return base64.b64decode(s.to_string().value)