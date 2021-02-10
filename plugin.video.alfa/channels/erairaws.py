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

host = "https://www.erai-raws.info"

IDIOMAS = {'French': 'VOS', 'German': 'VOS', 'Italian': 'VOS', 'English': 'VOS', 'Portuguese(Brazil)': 'VOS', 'Spanish': 'VOSE'}
language_list = ('French', 'German', 'Italian', 'English', 'Portuguese(Brazil)', 'Spanish')
list_servers = ['torrent']
quality_list = ['1080p', '720p', '540p', '480p']
hide_unselected_subs = config.get_setting('filter_by', channel='erairaws')
show_vo = config.get_setting('filter_vo', channel='erairaws')
selected_sub = language_list[config.get_setting('filter_subs_lang', channel='erairaws')]
if config.get_setting('play_direct', channel='erairaws'):
    play_direct_action = 'findvideos'
else:
    play_direct_action = 'episodios'

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
            url = host + '/posts/'
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
            url = host + '/batch/'
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
            url = host + '/movies/'
        )
    )
    itemlist.append(
        Item(
            action = "alpha",
            channel = item.channel,
            plot = 'Listado por orden alfabético',
            title = "A-Z",
            thumbnail = 'https://i.imgur.com/vIRCKQq.png',
            url = host + '/anime-list/'
        )
    )
    itemlist.append(
        Item(
            action = "search",
            channel = item.channel,
            title = "Buscar...",
            plot = 'Buscar películas, animes, OVAs, especiales etc. en la página',
            url = host + '/anime-list/',
            thumbnail = 'https://i.imgur.com/ZVMl3NP.png'
        )
    )
    itemlist.append(
        Item(
            action = "setting_channel",
            channel = item.channel,
            plot = 'Cambiar idioma de subtítulos, incluir en buscador global...',
            text_color = 'aquamarine',
            title = "Configurar canal...", 
            thumbnail = get_thumb("setting_0.png"),
            url = ""
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

    data = httptools.downloadpage(url, post=kwargs.get('post', None), headers=kwargs.get('headers', None)).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    if kwargs.get('wp_pager') and kwargs.get('search_key'):
        search_key = kwargs.get('search_key')
        post = {'action': 'load_more_0', 'query': '{"anime-list":"' + search_key + '","error":"","m":"","p":0,"post_parent":"","subpost":"","subpost_id":"","attachment":"","attachment_id":0,"name":"","pagename":"","page_id":0,"second":"","minute":"","hour":"","day":0,"monthnum":0,"year":0,"w":0,"category_name":"","tag":"","cat":"","tag_id":"","author":"","author_name":"","feed":"","tb":"","paged":0,"meta_key":"","meta_value":"","preview":"","s":"","sentence":"","title":"","fields":"","menu_order":"","embed":"","category__in":[],"category__not_in":[],"category__and":[],"post__in":[],"post__not_in":[],"post_name__in":[],"tag__in":[],"tag__not_in":[],"tag__and":[],"tag_slug__in":[],"tag_slug__and":[],"post_parent__in":[],"post_parent__not_in":[],"author__in":[],"author__not_in":[],"ignore_sticky_posts":false,"suppress_filters":false,"cache_results":true,"update_post_term_cache":true,"lazy_load_term_meta":true,"update_post_meta_cache":true,"post_type":"","posts_per_page":99,"nopaging":false,"comments_per_page":"0","no_found_rows":false,"taxonomy":"anime-list","term":"' + search_key + '","order":"DESC"}', 'page': '0'}
        data = httptools.downloadpage('{}/wp-admin/admin-ajax.php'.format(host), post=post, headers={'Referer': url}).data
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup

def set_infoLabels_async(itemlist, seekTmdb = False):
    logger.info()
    import threading

    threads_num = config.get_setting("tmdb_threads", default=20)
    semaforo = threading.Semaphore(threads_num)
    lock = threading.Lock()
    r_list = list()
    i = 0
    l_hilo = list()

    def sub_thread(_item, _i, _seekTmdb):
        semaforo.acquire()
        ret = labeler(_item, _seekTmdb, lock)
        semaforo.release()
        r_list.append((_i, _item, ret))

    for item in itemlist:
        t = threading.Thread(target = sub_thread, args = (item, i, seekTmdb))
        t.start()
        i += 1
        l_hilo.append(t)

    # esperar q todos los hilos terminen
    for x in l_hilo:
        x.join()

    # Ordenar lista de resultados por orden de llamada para mantener el mismo orden q itemlist
    r_list.sort(key=lambda i: i[0])

    # Reconstruir y devolver la lista solo con los resultados de las llamadas individuales
    return [ii[2] for ii in r_list]

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
    """
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
    season_indicators = {2: '(?i)( II$|Second Season|2nd Season)', 3: '(?i)( III$|Third Season|3rd Season)', 4:  '(?i)(Fourth Season|4th Season)',
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
        # Los años son 4 número exactamente, para no confundirlo con temporada u otra cosa
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

def newest(item):
    item.url = host + '/posts/'
    return list_all(item)

def list_selected(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    data = str(soup.find('div', class_='shows-wrapper'))

    if item.letra:
        if item.letra == 'Z':
            pat = '(?is)id="Z".*?</h4>(.*?)</div>\s+</div>'
        else:
            pat = '(?is)id="%s".*?</h4>(.*?</h4>)' % item.letra
        data = scrapertools.find_single_match(data, pat)

    matches = BeautifulSoup(data, "html5lib", from_encoding="utf-8").find_all('div', class_='button5')

    for anime in matches:
        scrapedtitle = str(anime.find('span').string)
        title, infoLabels = process_title(scrapedtitle, get_infoLabels = True)

        if not item.busq.lower() in scrapedtitle.lower():
            continue

        itemlist.append(
            Item(
                action = 'episodios',
                channel = item.channel,
                contentSerieName = title,
                contentTitle = title,
                infoLabels = infoLabels,
                title = scrapedtitle,
                url = item.url + anime.find('a')['href'],
            )
        )
    set_infoLabels_async(itemlist, seekTmdb = True)
    return itemlist

def list_all(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    articles = soup.find('div', id='main').find_all('article')

    if item.list_what == 'episodes':
        itemlist.extend(item_extractor(item, articles, action = play_direct_action, newest_ep_context = True))
    elif item.list_what == 'batch':
        itemlist.extend(item_extractor(item, articles, action = 'episodios', batch = True))
    elif item.list_what == 'movies':
        itemlist.extend(item_extractor(item, articles, action = 'findvideos', treat_as = 'special', contentType = 'movie'))
    else:
        itemlist.extend(item_extractor(item, articles))
    set_infoLabels_async(itemlist, seekTmdb = True)
    nextpage = soup.find('nav', class_='pagination')
    if nextpage:
        itemlist.append(
            item.clone(
                text_color = 'yellow',
                title = 'Siguiente página >',
                url = nextpage.find('a', class_='next')['href']
            )
        )

    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    itemlist.extend(episodios(item, get_episodes = True))
    return itemlist

def episodios(item, get_episodes = False, get_movie = False):
    logger.info()
    itemlist = []
    sections = []
    soup = create_soup(item.url)
    if soup.find('div', class_='h-episodes') and not get_movie:
        section = soup.find('div', class_='h-episodes')
        if section.find('div', class_='load_more'):
            animename = scrapertools.find_single_match(item.url, (host + '/.*?/(.*?)$')).replace('/', '')
            section = create_soup(item.url, wp_pager=True, search_key=animename)
        sections.append([section, 'episodes'])
    if soup.find('div', class_='h-movies') and not get_episodes:
        sections.append([soup.find('div', class_='h-movies'), 'movies'])
    if soup.find('div', class_='h-batch') and not get_episodes and not get_movie:
        sections.append([soup.find('div', class_='h-batch'), 'batch'])
    if len(sections) == 0:
        return itemlist

    # En caso de que la lista contenga algo más que solo episodios o películas (especiales o batches)
    posts_itemlist = []
    batch_itemlist = []
    movies_itemlist = []
    for section, sectiontype in sections:
        if 'episodes' in sectiontype:
            collected_items = item_extractor(item, section.find_all('article'), treat_as = 'episodes', action = 'findvideos')
            collected_items.reverse()
            if len(sections) == 1 and len(collected_items) == 1 and not get_episodes:
                return findvideos(collected_items[0])
            elif len(collected_items) > 0:
                if not get_episodes:
                    posts_itemlist.append(
                        Item(
                            channel = item.channel,
                            folder = False,
                            text_color = 'aquamarine',
                            title = 'Episodios:'
                        )
                    )
                posts_itemlist.extend(collected_items)
        elif 'batch' in sectiontype:
            collected_items = item_extractor(item, section.find_all('article'), treat_as = 'batch', action = 'findvideos')
            if len(sections) == 1 and len(collected_items) == 1:
                return findvideos(collected_items[0])
            elif len(collected_items) > 0:
                batch_itemlist.append(
                    Item(
                        channel = item.channel,
                        folder = False,
                        text_color = 'aquamarine',
                        title = 'Batch:'
                    )
                )
                batch_itemlist.extend(collected_items)
        elif 'movies' in sectiontype:
            collected_items = item_extractor(item, section.find_all('article'), treat_as = 'special', action = 'findvideos')
            if len(sections) == 1 and len(collected_items) == 1:
                return findvideos(collected_items[0])
            elif len(collected_items) > 0:
                if not get_movie:
                    movies_itemlist.append(
                        Item(
                            channel = item.channel,
                            folder = False,
                            text_color = 'aquamarine',
                            title = 'Películas y especiales:'
                        )
                    )
                movies_itemlist.extend(collected_items)

    if len(posts_itemlist) > 0 and config.get_videolibrary_support() and not get_episodes:
        posts_itemlist.append(
            Item(
                action = "add_serie_to_library",
                channel = item.channel,
                contentSerieName = item.contentSerieName,
                extra = 'episodesxseason',
                text_color = 'yellow',
                title = config.get_localized_string(70092),
                url = item.url
            )
        )

    if get_episodes:
        tmdb.set_infoLabels(posts_itemlist, seekTmdb=True)
        return posts_itemlist
    else:
        itemlist.extend(posts_itemlist)
        itemlist.extend(batch_itemlist)
        itemlist.extend(movies_itemlist)
        tmdb.set_infoLabels(itemlist, seekTmdb=True)
        return itemlist

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
        action = kwargs.get('action', 'episodios')
        infoLabels = {}
        if item.infoLabels['tmdb_id']:
            infoLabels['tmdb_id'] = item.infoLabels['tmdb_id']
        contentType = contentType
        contentTitle = ''
        contentSerieName = ''
        context = ''
        language = []
        quality_list = []
        magnet_urls = []
        section = div.find_all('div', class_='quali_po_dark')
        sectiontype = section[0].find('a', class_='tooltip2')['href']
        torrent_urls = []
        url = ''

        # ==== Sección 0 tiene datos del elemento (enlaces a episodios, títulos, estado) ==== #

        if section[0].find('font', class_='aa_ss_blue'):
            epdata = section[0].find('font', class_='aa_ss_blue').find_all('a')
            epname = str(epdata[1].font.string)
            title = str(epdata[0].font.string).strip()
            contentTitle, infoLabels = process_title(title, infoLabels, get_year_only=True)
            contentSerieName = contentTitle
            url = epdata[0]['href']

            if epname:
                if contentType is 'movie' or 'movie' in epname.lower() or ('movies' in sectiontype and not 'special' in epname.lower()):
                    contentType = 'movie'
                if contentType is 'tvshow' or 'special' in epname.lower() or ('posts' or 'finale' or 'batch') in sectiontype:
                    contentType = 'tvshow'
                    if kwargs.get('treat_as', '') == 'episodes':
                        season = process_title(title, get_season_only = True)
                        if season:
                            infoLabels['season'] = int(season)
                        else:
                            infoLabels['season'] = 1
                        if scrapertools.find_single_match(epname, '(?is)\d+'):
                            infoLabels['episode'] = int(scrapertools.find_single_match(epname, '(?is)\d+'))
                        if infoLabels.get('episode') and infoLabels.get('season'):
                            ep_ss = scrapertools.get_season_and_episode(str(infoLabels['season']) + 'x' + str(infoLabels['episode']))
                            title = '{}: {}'.format(ep_ss, title)
                        else:
                            title = '{}: {}'.format(epname.strip(), title)
                    elif kwargs.get('treat_as', '') == 'special':
                        if 'special' in epname.strip().lower():
                            specialname = re.sub('(?i)Special', 'Especial', epname.strip()).strip()
                            title = '{}: {}'.format(title, specialname)
                        else:
                            title = '{}: {}'.format(title, epname.strip())
                    elif kwargs.get('treat_as', '') == 'batch':
                        logger.info(item.infoLabels)
                        title = 'E{}'.format(epname.strip())
                    else:
                        title = '{}: {}'.format(title, epname.strip())
                else:
                    title = '{}: {}'.format(title, epname.strip())
        else:
            continue
        if section[0].find('a', href='/posts/') and 'posts' in sectiontype:
            infoLabels['status'] = str(section[0].find('a', href='/posts/')['data-title'])

        # ============ Sección 1 contienes enlace e idiomas de los subtítulos ============ #
        # Aquí filtramos los items que no contengan subtítulos en el idioma seleccionado

        subtitles = section[1].find('span', class_='tooltip3')
        if not subtitles and not hide_unselected_subs:
            language.append('VO')
        elif (not subtitles and hide_unselected_subs) or (subtitles and show_vo):
            continue
        elif subtitles:
            available_subs = section[1].find_all('span', class_='tooltip3')
            for subtitle in available_subs:
                subtitle_name = subtitle['data-title'].strip()
                if not hide_unselected_subs:
                    for sub_name, alfa_equivalent in IDIOMAS.items():
                        match = scrapertools.find_single_match(subtitle_name, '(?i){}'.format(sub_name))
                        if match and not alfa_equivalent in language:
                            language.append(alfa_equivalent)
                elif hide_unselected_subs:
                    match = scrapertools.find_single_match(subtitle_name, '(?i){}'.format(selected_sub))
                    if match:
                        language.append(IDIOMAS[selected_sub])
                        break
            if len(language) == 0 and not hide_unselected_subs:
                language.append('VOS')
            elif len(language) == 0 and hide_unselected_subs:
                continue

        # ================== Sección 2 contiene los enlaces y las calidades ================= #

        if section[2]:
            q_divs = section[2].find_all('div', class_='quali_po')
            for q_div in q_divs:
                quality = scrapertools.find_single_match(str(q_div.find('i').string), '(?is)\d+p')
                a_links_list = q_div.find_all('a')
                if quality:
                    quality_list.append(quality)
                    title = title + ' [COLOR gray][' + quality + '][/COLOR]'

                for a_link in a_links_list:
                    if 'Torrent' in str(a_link.string):       # Enviamos a la lista de magnets o torrents correspondiente
                        torrent_urls.append([quality, a_link['href']])
                    else:
                        magnet_urls.append([quality, a_link['href']])
                        

        # TODO: Implementar menús contextuales personalizables
        # # Agregamos un menú para acceder a los capítulos/al episodio directamente
        if kwargs.get('newest_ep_context'):
            if play_direct_action == 'findvideos':
                context_action = 'episodios'
                context_title = 'Ver todos los capítulos'
            else:
                context_action = 'findvideos'
                context_title = 'Ver capítulo'
            context = [
                {
                    "action": context_action,
                    "channel": item.channel,
                    "contentSerieName": contentSerieName,
                    "contentTitle": contentTitle,
                    "contentType": contentType,
                    "infoLabels": infoLabels,
                    "language": language,
                    "magnet_urls": magnet_urls,
                    "quality": quality_list,
                    "title": context_title,
                    "torrent_urls": torrent_urls,
                    "url": url
                }
            ]

        itemlist.append(
            Item(
                action = action,
                channel = item.channel,
                contentSerieName = contentSerieName,
                contentTitle = contentTitle,
                contentType = contentType,
                context = context,
                infoLabels = infoLabels,
                language = language,
                magnet_urls = magnet_urls,
                quality = quality_list,
                title = title,
                torrent_urls = torrent_urls,
                url = url
            )
        )
    return itemlist

def findvideos(item, add_to_videolibrary = False):
    logger.info()
    itemlist = []
    if not (item.magnet_urls or item.torrent_urls):
        if item.contentType is 'movie':
            temp_itemlist = episodios(item)
            for i in temp_itemlist:
                if i.magnet_urls:
                    item.magnet_urls = i.magnet_urls
                if i.torrent_urls:
                    item.torrent_urls = i.torrent_urls
            if not (item.magnet_urls or item.torrent_urls):
                return itemlist
        else:
            temp_itemlist = episodios(item, get_episodes = True)
            for i in temp_itemlist:
                if i.infoLabels['episode'] == item.infoLabels['episode']:
                    item.magnet_urls = i.magnet_urls
                    item.torrent_urls = i.torrent_urls
            if not (item.magnet_urls or item.torrent_urls):
                return itemlist

    if item.magnet_urls:
        for quality, url in item.magnet_urls:
            itemlist.append(
                Item(
                    action = 'play',
                    channel = item.channel,
                    infoLabels = item.infoLabels,
                    quality = quality,
                    server = 'torrent',
                    title = 'Torrent [' + quality + '] [Magnet]',
                    url = url
                )
            )
    if item.torrent_urls:
        for quality, url in item.torrent_urls:
            itemlist.append(
                Item(
                    action = 'play',
                    channel = item.channel,
                    infoLabels = item.infoLabels,
                    quality = quality,
                    server = 'torrent',
                    title = 'Torrent [' + quality + ']',
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