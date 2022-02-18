# -*- coding: utf-8 -*-
# -*- Channel Erai-raws -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido
    import urllib

import re

from bs4 import BeautifulSoup
from channels import autoplay
from channelselector import get_thumb
from core import httptools, scrapertools, tmdb
from core.item import Item
from platformcode import logger, config

IDIOMAS = {'French': 'FRA', 'German': 'DEU', 'Italian': 'ITA', 'English': 'ENG', 'Portuguese(Brazil)': 'PTBR', 'Spanish': 'VOSE', 'Spanish(Latin_America)': 'VOSE'}
language_list = ('French', 'German', 'Italian', 'English', 'Portuguese(Brazil)', 'Spanish')
list_servers = ['torrent']
quality_list = ['1080p', '720p', '540p', '480p']

canonical = {
             'channel': 'erairaws', 
             'host': config.get_setting("current_host", 'erairaws', default=''), 
             'host_alt': ["https://www.erai-raws.info/", "https://beta.erai-raws.info/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

hide_unselected_subs = config.get_setting('filter_by', channel=canonical['channel'])
show_vo = config.get_setting('filter_vo', channel=canonical['channel'])
selected_sub = language_list[config.get_setting('filter_subs_lang', channel=canonical['channel'])]
if config.get_setting('play_direct', channel=canonical['channel']):
    play_direct_action = 'findvideos'
else:
    play_direct_action = 'episodesxseason'

if hide_unselected_subs:
    p_main = ' según el idioma de subtítulos seleccionado'
else:
    p_main = ''


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, quality_list)

    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            list_what = 'episodes',
            plot = 'Nuevos episodios' + p_main,
            title = 'Nuevos episodios',
            thumbnail = 'https://i.imgur.com/IexJg5R.png',
            url = host + 'episodes/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all", not_post=True,
            channel = item.channel,
            list_what = 'batch',
            plot = 'Ultimas temporadas o paquetes de episodios' + p_main,
            title = "Batch",
            thumbnail = 'https://i.imgur.com/CzAGve1.png',
            url = host + 'batches/'
        )
    )
    itemlist.append(
        Item(
            action = "list_all",
            channel = item.channel,
            list_what = 'movies',
            plot = 'Ultimas películas, especiales, OVAs, etc.' + p_main,
            title = "Películas",
            thumbnail = 'https://i.imgur.com/aYBo36W.png',
            url = host + 'specials/'
        )
    )
    # itemlist.append(
        # Item(
            # action = "raws",
            # channel = item.channel,
            # plot = 'Raws (anime sin modificaciones a la versión original, lit. crudo)',
            # title = "Raws",
            # thumbnail = 'https://i.imgur.com/vIRCKQq.png',
            # url = host + 'raws/'
        # )
    # )
    itemlist.append(
        Item(
            action = "alpha",
            channel = item.channel,
            plot = 'Listado por orden alfabético',
            title = "A-Z",
            thumbnail = 'https://i.imgur.com/vIRCKQq.png',
            url = host + 'anime-list/'
        )
    )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            title = "Buscar...",
            plot = 'Buscar películas, animes, OVAs, especiales etc. en la página',
            url = host + 'anime-list/',
            thumbnail = 'https://i.imgur.com/ZVMl3NP.png'
        )
    )
    itemlist.append(
        Item(
            action = "setting_channel",
            channel = item.channel,
            folder = False,
            plot = 'Cambiar idioma de subtítulos, incluir en buscador global...',
            text_color = 'aquamarine',
            title = "Configurar canal...", 
            thumbnail = get_thumb("setting_0.png")
        )
    )
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def setting_channel(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret

def create_soup(url, **kwargs):
    logger.info()

    data = httptools.downloadpage(url, post=kwargs.get('post', None), headers=kwargs.get('headers', None), canonical=canonical).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    if kwargs.get('wp_pager') and kwargs.get('search_key'):
        search_key = kwargs.get('search_key')
        post = {'action': 'load_more_0', 'query': '{"anime-list":"' + search_key + '","error":"","m":"","p":0,"post_parent":"","subpost":"","subpost_id":"","attachment":"","attachment_id":0,"name":"","pagename":"","page_id":0,"second":"","minute":"","hour":"","day":0,"monthnum":0,"year":0,"w":0,"category_name":"","tag":"","cat":"","tag_id":"","author":"","author_name":"","feed":"","tb":"","paged":0,"meta_key":"","meta_value":"","preview":"","s":"","sentence":"","title":"","fields":"","menu_order":"","embed":"","category__in":[],"category__not_in":[],"category__and":[],"post__in":[],"post__not_in":[],"post_name__in":[],"tag__in":[],"tag__not_in":[],"tag__and":[],"tag_slug__in":[],"tag_slug__and":[],"post_parent__in":[],"post_parent__not_in":[],"author__in":[],"author__not_in":[],"ignore_sticky_posts":false,"suppress_filters":false,"cache_results":true,"update_post_term_cache":true,"lazy_load_term_meta":true,"update_post_meta_cache":true,"post_type":"","posts_per_page":99,"nopaging":false,"comments_per_page":"0","no_found_rows":false,"taxonomy":"anime-list","term":"' + search_key + '","order":"DESC"}', 'page': '0'}
        data = httptools.downloadpage('{}wp-admin/admin-ajax.php'.format(host), post=post, headers={'Referer': url}, canonical=canonical).data
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup

def item_extractor(item, soup, contentType = 'tvshow', **kwargs):
    """
    @param item: Item que hizo la solicitud
    @type item: item
    @param soup: Una lista con tags bs4 a convertir en items
    @type soup: list
    @param contentType: Tipo de contenido 'movie' o 'tvshow' (por defecto 'tvshow')
    @type contentType: str
    @param episodes: Tratar los items como episodios
    @type episodes: bool
    @param batch: Tratar los items como batch de episodios
    @type batch: bool
    @param special: Tratar los items como películas/especiales
    @type special: bool

    @return: Itemlist con items preparados
    @rtype: list
    """
    # Como toda la página utiliza contenedores de elementos idénticos, reutilizamos el código para convertir esos
    # "contenedores" en items, y hacemos lo apropiado con los items que obtengamos (ej. peliculas, especiales, etc)
    logger.info()
    itemlist = []

    for div in soup:
        action = kwargs.get('action', 'episodesxseason')
        infoLabels = {}
        if item.infoLabels['tmdb_id']:
            infoLabels['tmdb_id'] = item.infoLabels['tmdb_id']
        contentType = contentType
        link = div.find('a', class_='aa_ss_ops_new')
        title, infoLabels = process_title(link.text, infoLabels, get_year_only=True)
        languages = [IDIOMAS.get(x['data-title'], 'VOS') for x in div.find_all(class_='tooltip3') if IDIOMAS.get(x['data-title']) in ['VOS', 'VOSE']]
        quality_list = [x.text for x in div.find_all(class_='load_more_links_buttons')]

        newit = Item(
                    action = action,
                    channel = item.channel,
                    contentType = contentType,
                    infoLabels = infoLabels,
                    language = languages,
                    quality = quality_list,
                    title = title,
                    url = link['href']
                )
        if contentType == 'movie':
            newit.contentTitle = newit.title
        else:
            newit.contentSerieName = newit.title

        itemlist.append(newit)
    return itemlist

def labeler(item, seekTmdb = True, lock = None):
    logger.info()
    tmdb_langs = ['es', 'es-MX', 'en', 'it', 'pt', 'fr', 'de']
    langs = config.get_setting('tmdb_lang', default=0)
    tmdb_lang = tmdb_langs[langs]

    # Excepción(es) por algunas cosas que TMDB suele retornar erróneamente.
    # Estas en particular, las retorna mal en muchos de los canales que se busca cuando no hay año correcto
    year_exceptions = {'(?i)Yuru Camp': '2018', '(?i)One Piece': '1999', '(?i)Arte': '2020'}
    title_exceptions = {'(?i)Bem': 'Bem: Become Human', '(?i)Given': 'Eiga Given'}

    title = item.infoLabels['title']
    for title_exc, title_replace in title_exceptions.items():
        if scrapertools.find_single_match(title, title_exc):
            if item.contentTitle:
                item.contentTitle = title_replace
            if item.contentSerieName:
                item.contentSerieName = title_replace
    for title_exc, year_replace in year_exceptions.items():
        if scrapertools.find_single_match(title, title_exc):
            item.infoLabels['year'] = year_replace

    temp_item = item
    if temp_item.contentType == 'movie':
        result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock, force_no_year = True)
    else:
        if temp_item.contentSeason or temp_item.infoLabels['episode']:
            if temp_item.infoLabels['episode'] and not temp_item.contentSeason:
                temp_item.infoLabels['season'] = 1
            if temp_item.contentSeason or (temp_item.contentSeason and temp_item.infoLabels['episode']):
                season = temp_item.contentSeason
                temp_item.infoLabels['season'] = ''
                temp_item.contentSeason = ''
                if temp_item.infoLabels['episode']:
                    episode = temp_item.infoLabels['episode']
                    temp_item.infoLabels['episode'] = ''
                result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock)
                temp_item.infoLabels['season'] = season
                if item.infoLabels['episode']:
                    temp_item.infoLabels['episode'] = episode
                result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock)
        else:
            result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock)
    if result == 0:
        return temp_item
    if not temp_item.infoLabels.get('tmdb_id'):
        if temp_item.contentType == 'movie':
            oldcontentType = temp_item.contentType
            temp_item.contentType = 'tvshow'
            result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock, force_no_year = True)
        else:
            temp_item.contentType = 'movie'
            temp_item.contentSerieName = ''
            temp_item.infoLabels['tvshowtitle'] = ''
            result = tmdb.set_infoLabels_item(temp_item, True, tmdb_lang, lock, force_no_year = True)
    return temp_item

def process_title(title, infoLabels = None, **kwargs):
    """Procesa la informaicón de un título y la retorna en infoLabels
    
    @param title: String a la cual hay que extraer y/o limpiar información
    @type title: str
    @param infoLabels: Un dict con infoLabels para anexar datos y devolverlas
    @type infoLabels: dict
    @param get_infoLabels: Si se obtienen las infoLabels o solo el título
    @type get_infoLabels: bool
    @param get_year_only: Obtener solo el año como str en title
    @type get_year_only: bool
    @param get_season_only: Obtener solo la temporada como str en title
    @type get_season_only: bool

    @return: Título limpio, infoLabels asignadas / Solo título / Solo infoLabels
    @rtype: str, dict / str / dict
    
    # Notas:
    - TMDB es bastante "especial" si se le agrega un nº de temporada a una serie,
      hay que agregar temporada SOLO en sección temporada, tal cual (usar parámetro
      get_year_only)
    """

    logger.info()
    return_year_only = False
    return_infoLabels = False
    return_season_only = False
    if infoLabels is not None or kwargs.get('get_infoLabels') or kwargs.get('get_year_only'):
        if not infoLabels:
            infoLabels = {}
        else:
            infoLabels = infoLabels
        return_infoLabels = True
        if kwargs.get('get_year_only'):
            return_year_only = True
    else:
        infoLabels = {}
    if kwargs.get('get_season_only'):
        season = ''
        return_season_only = True

    # Las temporadas suelen estar al final, checamos solo ahí (significado del "$") (buscar en cualquier otra parte trae problemas)
    season_indicators = {2: '(?i)( II$|Part 2|Second Season|2nd Season)', 3: '(?i)( III$|Third Season|3rd Season)', 4:  '(?i)(Fourth Season|4th Season)',
                         5: '(?i)(Fifth Season|5th Season)',       6: '(?i)(Sixth Season|6th Season)',       7:  '(?i)(Seventh Season|7th Season)',
                         8: '(?i)(Eight Season|8th Season)',       9: '(?i)(Ninth Season|9th Season)',       10: '(?i)(Tenth Season|10th Season)'}

    # Hay casos especiales donde la temporada solo es un número al final (ej. Hataraku Saibou 2),
    # buscamos esto SOLO cuando haya pasado los que dicen con letra, ya que puede dejar el texto "Season"
    numeric_season_indicators = '(?i)(Season \d+| S\d+$| (?:\d{1}|\d{2})$)'

    if not kwargs.get('movie'):
        replaced = False
        temp_title = title

        # Hacemos loop de temporadas de regex y reemplazamos con la clave (que es la temporada correspondiente)
        for key, pattern in season_indicators.items():
            temp_title = re.sub(pattern, '', title).strip()
            if temp_title != title:
                replaced = True
                title = temp_title
                if infoLabels.get('tmdb_id'):
                    infoLabels['season'] = int(key)
                elif return_season_only:
                    season = int(key)
                # Salimos al encontrar el primer match, seguir puede causar problemas con el título
                break

        # Si es una temporada de un solo número, lo extraemos, lo validamos y lo colocamos
        temp_title = re.sub(numeric_season_indicators, '', title).strip()
        if title not in temp_title and not replaced:
            replaced = True
            match = scrapertools.find_single_match(title, numeric_season_indicators)
            nummatch = scrapertools.find_single_match(match, '\d+')
            if nummatch:
                if str(nummatch).isdigit():
                    title = re.sub(numeric_season_indicators, '', title)
                    if infoLabels.get('tmdb_id'):
                        infoLabels['season'] = int(nummatch)
                    elif return_season_only:
                        season = int(nummatch)
        if replaced and ':' in title:
            title = title.replace(':', '').strip()

    if not return_season_only:
        # Los años son 4 números exactamente, para no confundirlo con temporada u otra cosa
        # Buscamos al final, para no confundir con el nombre del elemento
        year = scrapertools.find_single_match(title, '[\(]?\d{4}[\)]?$')

        if year:
            title = re.sub('[\(]?\d{4}[\)]?', '', title)
            infoLabels['year'] = year

    if return_infoLabels:
        return title, infoLabels
    elif return_season_only:
        return season
    else:
        return title

def alpha(item):
    logger.info()
    itemlist = []
    alphabet = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for letter in alphabet:
        itemlist.append(
            item.clone(
                action = 'list_selected',
                letra = letter,
                title = letter
            )
        )

    return itemlist

def search(item, texto):
    logger.info()
    item.busq = texto

    try:
        if texto != '':
            return list_selected(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(category):
    if category == 'anime':
        item = Item(
            action = 'list_all',
            channel = canonical['channel'],
            list_what = 'episodes',
            url = '{}posts/'.format(host)
        )
        return list_all(item)
    else:
        return []

def list_selected(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    data = soup.find(id='main').find(class_='tab-content')

    if item.letra:
        if item.letra == '#': item.letra = '1'
        data = soup.find(id='menu_{}'.format(item.letra))
        if not data:
            return [Item(folder=False, title="Cambio de estructura. Reportar en el foro")]

    matches = data.find_all('a')

    for anime in matches:
        scrapedtitle = str(anime.string)
        title, infoLabels = process_title(scrapedtitle, get_infoLabels = True)

        if not item.letra and not item.busq.lower() in scrapedtitle.lower():
            continue

        itemlist.append(
            Item(
                action = 'episodesxseason',
                channel = item.channel,
                contentSerieName = title,
                contentTitle = title,
                infoLabels = infoLabels,
                title = scrapedtitle,
                url = item.url + anime['href'],
            )
        )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True, no_year = True)
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    articles = soup.find(id='main').find_all('table')

    episodes = item.list_what == 'episodes'
    batch = item.list_what == 'batch'
    movies = item.list_what == 'movies'

    for div in articles:
        # Scrapping: Obtenemos los datos
        infoLabels = {}
        link = div.find('a', class_='aa_ss_ops_new')
        title, infoLabels = process_title(link.text, infoLabels, get_year_only=True)
        language_list = [IDIOMAS.get(x['data-title'], 'VO') for x in div.find_all(class_='tooltip3') if IDIOMAS.get(x['data-title'], '') in list(['VOS', 'VOSE'])]
        quality_list = [x.text for x in div.find_all(class_='load_more_links_buttons')]

        # Creamos el item
        newit = Item(
            channel = item.channel,
            infoLabels = infoLabels,
            language = language_list,
            quality = quality_list,
            title = title,
            url = link['href']
        )

        # Asignamos propiedades específicas del contentType al item
        if episodes:
            title, labels = newit.title.split(' - ')
            labels = scrapertools.find_multiple_matches(labels, '(?is)(\d+)(?:.+?[\(](\w+)[\)])?')[0]
            newit.action = play_direct_action
            newit.contentType = 'tvshow'
            newit.contentEpisode = int(labels[0])
            newit.title = 'E{}: {}'.format(newit.contentEpisode, title)
            if labels[-1]:
                newit.title += ' [{}]'.format(labels[-1])
            newit.contentSerieName = title
        elif batch:
            title, labels = newit.title.split(' - ')
            labels = scrapertools.find_multiple_matches(labels, '(?is)(\d+).+?(\d+)(?:.+?[\(](\w+)[\)])?')[0]
            newit.action = 'episodesxseason'
            newit.contentType = 'tvshow'
            newit.title = '{} [{} - {}]'.format(title, labels[0], labels[1])
            logger.info(labels)
            if labels[2]:
                newit.title += ' [{}]'.format(labels[2])
            newit.contentSerieName = title
        elif movies:
            newit.action = 'findvideos'
            newit.contentType = 'movie'
            newit.contentTitle = newit.title

        # Agregamos el item
        itemlist.append(newit)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True, no_year = True)
    logger.info(play_direct_action)
    nextpage = soup.find('a', class_='next')
    if nextpage:
        itemlist.append(
            item.clone(
                text_color = 'yellow',
                title = 'Siguiente página >',
                url = nextpage['href']
            )
        )
    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    itemlist.extend(episodesxseason(item, get_episodes = True))
    return itemlist

def episodesxseason(item, get_episodes = False, get_movie = False):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if soup.find(id=re.compile('menu\d+')):
        # Initial variables to set content type
        airing = False
        batch = False
        finale = False
        moviespecial = False

        menu = soup.find(id=re.compile('menu\d+'))

        if "No episodes have been added yet" in menu.text:
            return []

        type = soup.find(class_='alphabet-title').text

        # Detect what kind of content we're dealing with
        if 'airing' in type.lower():
            pass
            airing = True
        elif 'batch' in type.lower():
            pass
            batch = True
        elif 'movie' in type.lower():
            pass
            moviespecial = True
        elif 'finale' in type.lower():
            pass
            finale = True
        else:
            type = ''

        episodes = menu.find_all('table')
        details = soup.find(id=re.compile('post-\d+'))
        image = details.find(class_='entry-content-poster').find('img')['data-src']
        contentTitle = details.find(class_='entry-title').text

        for episode in episodes:
            infoLabels = item.infoLabels
            urls = {}
            ep = episode.find('a', class_='aa_ss_ops_new')
            if ep:
                airing = True
            
            if airing:
                infoLabels['episode'] = int(scrapertools.find_single_match(ep.text, '.+? - (\d+)'))
                title = "1x{}. {}".format(infoLabels['episode'], (config.get_localized_string(60036) % infoLabels['episode']))
            elif batch:
                infoLabels['episode'] = (scrapertools.find_multiple_matches(ep.text, '.+? - (\d+).+?(\d+)'))
                infoLabels['episode'] = (scrapertools.find_multiple_matches(ep.text, '.+? - (\d+).+?(\d+)'))
                title = "1x{}. {}".format(infoLabels['episode'], (config.get_localized_string(60036) % infoLabels['episode']))
            elif finale:
                pass
            elif moviespecial:
                pass
            else:
                title = scrapertools.find_single_match(episode.find(class_='aa_ss_ops_new').text, '')

            for link in episode.find_all(class_='release-links'):
                qa = link.find('span').text.split('|')[0].strip()

                for linktype in link.find_all(class_='link_uppercase'):
                    name = '{} [{}]'.format(linktype.text.title(), qa)
                    urls[name] = linktype['href']

            title = "{}{}".format(type, title)
            new_item = item.clone(
                action = 'findvideos',
                contentTitle = contentTitle,
                fanart = image,
                infoLabels = infoLabels,
                plot = details.find(class_='entry-content-story').text,
                thumbnail = image,
                title = title,
                urls = urls
            )

            itemlist.append(new_item)
        itemlist.reverse()
        return itemlist
    else:
        return [Item(folder=False, title='Cambio de estructura. Reportar en el foro')]

def findvideos(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    if not item.urls:
        return [Item(folder=False, title='Cambio de estructura. Reportar en el foro')]

    if item.urls:
        for title, url in list(item.urls.items()):
            itemlist.append(
                item.clone(
                    action = 'play',
                    server = 'torrent',
                    title = title,
                    url = url
                )
            )

    sorted(itemlist, key=lambda x:x.server)

    if len(itemlist) > 0 and config.get_videolibrary_support() \
        and item.contentTitle and item.contentType == 'movie' and not item.videolibrary:
            itemlist.append(
                item.clone(
                    action = "add_pelicula_to_library",
                    extra = 'episodesxseason',
                    text_color = 'yellow',
                    title = config.get_localized_string(70092),
                    url = item.url,
                    videolibrary = True
                )
            )

    return itemlist
