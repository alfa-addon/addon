# -*- coding: utf-8 -*-
# -*- Alfa Channel Helper -*-
# -*- Herramientas genericas para canales BS -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse
else:
    import urlparse

import re
import traceback
import time
import base64

from core import httptools
from core import scrapertools
from core.scrapertools import episode_title
from core import tmdb
from core import jsontools
from core.item import Item
from platformcode import config
from platformcode import logger
from channels import filtertools

forced_proxy_def = 'ProxyCF'
DEBUG = False
IDIOMAS = {'mx': 'Latino', 'dk': 'Latino', 'es': 'Castellano', 'en': 'VOSE', 'gb': 'VOSE', 
           'sub': 'VOSE', 'su': 'VOSE', 'eng': 'VOSE', "subtitulado": "VOSE", "usa": "VOSE", 
           'de': 'VOSE', "español": "Castellano", "espana": "Castellano", 'cas': 'Castellano', 
           "mexico": "Latino", "latino": "Latino", 'lat': 'Latino', 'LAT': 'Latino', 'jp': 'VOSE'}


class AlfaChannelHelper:

    def __init__(self, host, channel='', movie_path="/movies", tv_path="/serie", 
                 movie_action="findvideos", tv_action="seasons", forced_proxy_opt='ProxyCF', 
                 list_language=[], list_quality=[], list_quality_movies=[], list_quality_tvshow=[], 
                 list_servers=[], language=[], idiomas={}, IDIOMAS_TMDB={0: 'es', 1: 'en', 2: 'es,en'}, 
                 actualizar_titulos=True, canonical={}, finds={}, debug=False, url_replace=[]):
        global DEBUG, forced_proxy_def
        DEBUG = debug
        forced_proxy_def = forced_proxy_opt
        
        self.url = ''
        self.host = host
        self.doo_url = "%swp-admin/admin-ajax.php" % host
        self.channel = channel
        self.movie_path = movie_path
        self.tv_path = tv_path
        self.movie_action = movie_action
        self.tv_action = tv_action
        self.list_language = list_language
        self.list_quality = self.list_quality_tvshow = list_quality or list_quality_tvshow
        self.list_quality_movies = list_quality_movies
        self.list_servers = list_servers
        self.language = language
        self.idiomas = idiomas or IDIOMAS
        self.IDIOMAS_TMDB = IDIOMAS_TMDB
        self.actualizar_titulos = actualizar_titulos
        self.canonical = canonical
        self.finds = finds
        self.url_replace = url_replace

    def create_soup(self, url, resp=False, **kwargs):
        """
        :param url: url destino
        :param kwargs: parametros que se usan en donwloadpage
        :return: objeto soup o response sino soup
        """
        from lib.generictools import js2py_conversion

        if "soup" not in kwargs: kwargs["soup"] = True
        if 'referer' not in kwargs and 'Referer' not in kwargs.get('headers', {}) \
                                   and "add_referer" not in kwargs: kwargs["add_referer"] = True
        if "ignore_response_code" not in kwargs: kwargs["ignore_response_code"] = True
        if "canonical" not in kwargs: kwargs["canonical"] = self.canonical
        size_js = kwargs.pop('size_js', 10000)
        
        if DEBUG: logger.debug('KWARGS: %s' % kwargs)
        response = httptools.downloadpage(url, **kwargs)

        if response.code in httptools.SUCCESS_CODES + httptools.REDIRECTION_CODES \
                       and ('text/' in response.headers.get('Content-Type', '') \
                       or 'json' in response.headers.get('Content-Type', '') \
                       or 'xml' in response.headers.get('Content-Type', '') \
                       or 'javascript' in req.headers.get('Content-Type', '')):
                response = js2py_conversion(response.data, url, resp=response, size=size_js, **kwargs)
        
        if kwargs.get("soup", {}):
            soup = response.soup or {}
        else:
            soup = response
        
        if response.host:
            self.doo_url = self.doo_url.replace(self.host, response.host)
            self.url = url.replace(self.host, response.host)
            self.host = response.host
        elif response.url and response.url != url:
            if not scrapertools.find_single_match(url, '(page\/\d+\/?)'):
                self.url = '%s%s' % (response.url, scrapertools.find_single_match(url, '(page\/\d+\/?)'))
            else:
                self.url = response.url

        if resp: return response
        return soup

    def list_all(self, item, postprocess=None):
        pass

    def limit_results(self, item, matches, lim_max=20):

        next_page = None
        next_limit = None

        if len(matches) > lim_max and not item.next_limit:
            limit = int(len(matches) / 2)
            next_limit = limit
            next_page = item.url
            matches = matches[:limit]
        elif item.next_limit:
            matches = matches[item.next_limit:]

        return matches, next_limit, next_page

    def section(self, item, menu_id=None, section=None, postprocess=None):
        pass

    def seasons(self, item, action="episodesxseason", postprocess=None):
        pass

    def episodes(self, item, action="findvideos", postprocess=None):
        pass

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def):
        pass

    def define_content_type(self, new_item, is_tvshow=False):

        if new_item.infoLabels.get("year", '') and str(new_item.infoLabels["year"]) in new_item.title and len(new_item.title) > 4:
            new_item.title = re.sub("\(|\)|%s" % str(new_item.infoLabels["year"]), "", new_item.title).strip()

        if new_item.contentType == 'episode': 
            new_item.contentSerieName = re.sub('\s*\d+x\d+\s*', '', new_item.title)
            new_item.action = self.movie_action
            if not new_item.season_search: new_item.season_search = new_item.contentSerieName
        elif not is_tvshow and (self.movie_path in new_item.url or not self.tv_path in new_item.url):
            new_item.action = self.movie_action
            new_item.contentTitle = new_item.title.strip()
            if not new_item.contentType: new_item.contentType = 'movie'
            if not new_item.infoLabels.get("year", ''): new_item.infoLabels["year"] = '-'
            if not new_item.season_search: new_item.season_search = new_item.contentTitle
        else:
            new_item.action = self.tv_action
            new_item.contentSerieName = new_item.title.strip()
            new_item.contentType = 'tvshow'
            if not new_item.season_search: new_item.season_search = new_item.contentSerieName

        return new_item

    def add_video_to_videolibrary(self, item, itemlist, contentType='tvshow'):

        if item.add_videolibrary or item.library_playcounts:
            return itemlist

        actionType = 'pelicula' if contentType == 'movie' else 'season' if contentType == 'season' else 'serie'
        contentTitle = 'pelicula' if contentType == 'movie' else 'temporada' if contentType == 'season' else 'serie'

        if len(itemlist) > 0:
            if item.contentChannel != "videolibrary" and item.action == 'findvideos':
                itemlist.append(item.clone(channel="trailertools", title="**-[COLOR magenta] Buscar Trailer [/COLOR]-**", 
                                           action="buscartrailer", context=""))
        
        if config.get_videolibrary_support() and len(itemlist) > 0 \
                        and ((item.contentType == 'movie' and item.action == 'findvideos') or item.action != 'findvideos'):
            item.url = self.do_url_replace(item.url)
            
            if self.actualizar_titulos:
                from lib.generictools import get_color_from_settings
                itemlist.append(item.clone(title="** [COLOR %s]Actualizar Títulos - vista previa videoteca[/COLOR] **" \
                                                  % get_color_from_settings('library_color', default='yellow'), 
                                           action="actualizar_titulos",
                                           tmdb_stat=False, 
                                           from_action=item.action, 
                                           contentType=contentType,
                                           from_title_tmdb=item.title, 
                                           from_update=True, 
                                           thumbnail=item.infoLabels['temporada_poster'] or item.infoLabels['thumbnail']
                                          )
                               )

            itemlist.append(item.clone(title='[COLOR yellow]Añadir esta %s a la videoteca[/COLOR]' % contentTitle, 
                                       url=item.url,
                                       action="add_%s_to_library" % actionType,
                                       extra="episodios",
                                       contentType=contentType, 
                                       contentSerieName=item.contentSerieName
                                      )
                           )
        return itemlist

    def do_url_replace(self, url, url_replace=[]):

        if url and (url_replace or self.url_replace):

            for url_from, url_to in (url_replace or self.url_replace):
                url = re.sub(url_from, url_to, url)

        return url

    def do_quote(self, url, plus=True):

        if plus:
            return urlparse.quote_plus(url)
        else:
            return urlparse.quote(url)

    def do_unquote(self, url):
        
        return urlparse.unquote(url)

    def obtain_domain(self, url, sub=False, point=False, scheme=False):

        return httptools.obtain_domain(url, sub=sub, point=point, scheme=scheme)

    def get_language_and_set_filter(self, elem, elem_json):

        langs = ""
        finds_out = self.finds.get('get_language', {})
        finds_lang_rgx = self.finds.get('get_language_rgx', '(?:flags\/|-)(\w+)\.(?:png|jpg|jpeg|webp)')

        try:
            lang_list = self.parse_finds_dict(elem, finds_out)
            for lang in lang_list:
                lang_ = scrapertools.find_single_match(str(lang), finds_lang_rgx)
                if self.idiomas.get(lang_, ''):
                    if self.idiomas.get(lang_, '') not in langs:
                        langs += '%s,' % self.idiomas.get(lang_, '')
                elif lang_ and lang_ not in langs:
                    langs += '%s,' % lang_
        except:
            langs = ""
        if DEBUG or not langs: 
            logger.debug('FINDS_get_language: %s; LANGS: %s' % (finds_lang_rgx, langs))
            if not langs: logger.debug('FINDS_get_language: ELEM: %s' % elem)

        elem_json['language'] = langs.rstrip(',')

    def find_quality(self, elem_in, item):

        if isinstance(elem_in, dict):
            elem = elem_in
            c_type = item.c_type or item.contentType
        else:
            elem = {}
            elem['quality'] = elem_in.quality
            elem['title'] = elem_in.title
            elem['url'] = elem_in.url
            elem['language'] = elem_in.language
            c_type = elem_in.contentType

        quality = elem.get('quality', '').replace('*', '').replace('[]', '')

        if c_type in ['series', 'documentales', 'tvshow', 'season', 'episode']:
            if '720' in elem['title'] or '720' in elem['url'] or '720' in elem.get('quality', ''):
                quality = 'HDTV-720p'
            elif '1080' in elem['title'] or '1080' in elem['url'] or '1080' in elem.get('quality', ''):
                quality = '1080p'
            else:
                quality = 'HDTV'
        else:
            if not quality and ('hd' in item.url.lower() or '4k' in item.url.lower() or '3d' in item.url.lower() \
                        or 'hd' in elem['url'].lower() or '4k' in elem['url'].lower() or '3d' in elem['url'].lower()):
                quality = 'HD'
        if (('4k' in item.url.lower() and not item.url.startswith('magnet')) or ('4k' in elem['url'].lower() \
                                      and not elem['url'].startswith('magnet'))) and not '4k' in quality.lower():
            quality += ', 4K'
        if (('3d' in item.url.lower() and not item.url.startswith('magnet')) or ('3d' in elem['url'].lower() \
                                      and not elem['url'].startswith('magnet'))) and not '3d' in quality.lower():
            quality += ', 3D'

        if 'dual' in quality.lower(): quality = re.sub('(?i)\s*dual', '', quality)
        if 'digg' in elem.get('quality', '').lower(): quality += config.BTDIGG_LABEL

        if DEBUG: logger.debug('find_QUALITY: %s' % quality)
        return quality

    def find_language(self, elem_in, item):

        language = []
        
        if isinstance(elem_in, dict):
            elem = elem_in
            c_type = item.c_type or item.contentType
        else:
            elem = {}
            elem['quality'] = elem_in.quality
            elem['title'] = elem_in.title
            elem['url'] = elem_in.url
            elem['language'] = elem_in.language
            c_type = elem_in.contentType
        
        if isinstance(elem.get('language'), str): elem['language'] = [elem['language']]
        for lang in elem.get('language', []):
            if 'sub' in elem.get('quality', '').lower() or 'subs. integrados' in elem.get('title', '').lower() \
                        or 'sub forzados' in elem.get('title', '').lower() or  'english' in elem.get('title', '').lower() \
                        or 'subtitle' in elem.get('url', '').lower() or 'english' in elem.get('url', '').lower() \
                        or 'sub' in lang.lower() or 'ing' in lang.lower() or 'eng' in lang.lower() \
                        or 'vo' in lang.lower():
                if 'VOSE' not in language: language += ['VOSE']
            if 'latin' in elem.get('title', '').lower() or 'latin' in elem.get('url', '').lower() \
                        or 'lat' in elem.get('url', '').lower() or ('la' in lang.lower() \
                                 and not 'lla' in lang.lower() and not 'ula' in lang.lower()):
                if 'LAT' not in language: language += ['LAT']
            if 'castellano' in elem.get('quality', '').lower() or (('español' in elem.get('quality', '').lower() \
                        or 'espanol' in elem.get('quality', '').lower()) and not 'latino' in elem.get('quality', '').lower()) \
                        or 'castellano' in elem.get('title', '').lower() or 'castellano' in elem.get('url', '').lower() \
                        or 'ca' in lang.lower() or ('es' in lang.lower() and not 'latino' in lang.lower()): 
                language += ['CAST']
            if 'dual' in elem.get('title', '').lower() or 'dual' in elem.get('quality', '').lower() \
                        or 'dual' in elem.get('url', '').lower() or 'dual' in lang.lower():
                 if 'DUAL' not in language: language += ['DUAL']
            if not language and self.language:
                language = self.language

        if DEBUG: logger.debug('find_LANGUAGE: %s' % language)
        return language

    def convert_size(self, size):
        
        s = 0
        if not size or size == 0 or size == '0':
            return s

        try:
            size_name = {"M·B": 1, "G·B": 1024, "MB": 1, "GB": 1024}
            if ' ' in size:
                size_list = size.split(' ')
                size = float(size_list[0])
                size_factor = size_name.get(size_list[1], 1)
                s = size * size_factor
        except:
            pass

        return s

    def manage_torrents(self, item, elem, lang, soup={}, finds={}, **kwargs):

        from lib.generictools import convert_url_base64, get_torrent_size
        from core import filetools
        if DEBUG: logger.debug('ELEM_IN: %s' % elem)

        finds_controls = finds.get('controls', {})

        host_torrent = finds_controls.get('host_torrent', '') or self.host
        host_torrent_referer = finds_controls.get('host_torrent_referer', host_torrent)
        FOLDER = config.get_setting("folder_movies") if item.contentType == 'movie' else config.get_setting("folder_tvshows")
        size = ''

        if finds.get('torrent_params', {}):
            torrent_params = finds['torrent_params']
        else:
            torrent_params = {
                              'url': item.url,
                              'torrents_path': None, 
                              'local_torr': item.torrents_path, 
                              'lookup': False, 
                              'force': True, 
                              'data_torrent': True, 
                              'subtitles': True, 
                              'file_list': True, 
                              'find_alt_link_option': False, 
                              'language_alt': [], 
                              'quality_alt': '', 
                              'domain_alt': ''
                              }

        # Restauramos urls de emergencia por si es necesario
        local_torr = '%s_torrent_file' % item.channel.capitalize()
        if item.emergency_urls and not item.videolibray_emergency_urls:
            try:                                                                # Guardamos la url ALTERNATIVA
                elem['torrent_alt'] = item.emergency_urls[0][0]
                if finds.get('controls', {}).get('url_base64', True):
                    if (elem['torrent_alt'].startswith('http') or elem['torrent_alt'].startswith('//')):
                        elem['torrent_alt'] = convert_url_base64(elem['torrent_alt'], host_torrent, referer=host_torrent_referer)
                    else:
                        elem['torrent_alt'] = convert_url_base64(elem['torrent_alt'])
            except:
                item_local.torrent_alt = ''
                item.emergency_urls[0] = []

            if item.armagedon and elem.get('torrent_alt', ''):
                elem['url'] = elem['torrent_alt']                               # Restauramos la url
                if not elem['url'].startswith('http') and not elem['url'].startswith('magnet'):
                    local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, elem['url'])
            if item.armagedon and len(item.emergency_urls[0]) > 1:
                del item.emergency_urls[0][0]

        # Buscamos tamaño en el archivo .torrent
        if not item.videolibray_emergency_urls and not elem['url'].startswith('magnet'):
            torrent_params['url'] = elem['url']
            torrent_params['torrents_path'] = ''
            torrent_params['local_torr'] = local_torr
            if lang not in item.language: torrent_params['language_alt'] = lang
            torrent_params = get_torrent_size(torrent_params['url'], torrent_params=torrent_params, 
                                              referer=self.host, item=item, **kwargs)           # Tamaño en el .torrent
            size = torrent_params['size']
            elem['url'] = torrent_params['url']
            if torrent_params['torrents_path']: elem['torrents_path'] = torrent_params['torrents_path']

            if 'ERROR' in size and item.emergency_urls and not item.videolibray_emergency_urls:
                item.armagedon = True
                elem['url'] = elem['torrent_alt']                               # Restauramos la url

                torrent_params['size'] = ''
                torrent_params['local_torr'] = local_torr
                torrent_params = get_torrent_size(torrent_params['url'], torrent_params=torrent_params, 
                                                  referer=self.host, item=item, **kwargs)       # Tamaño en el .torrent
                size = torrent_params['size']
                elem['url'] = torrent_params['url']
                if torrent_params['torrents_path']: elem['torrents_path'] = torrent_params['torrents_path']
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                       .replace('Mb', 'M·b').replace('.', ',')
            elem['torrent_info'] = '%s, ' % size                                # Agregamos size
        elem['torrent_info'] =  elem.get('torrent_info', '')
        if elem['url'].startswith('magnet:') and 'magnet' not in elem['torrent_info'].lower():
            elem['torrent_info'] += ' Magnet'
        if elem['torrent_info']:
            elem['torrent_info'] = elem['torrent_info'].replace('[', '').replace(']', '').strip().strip(',')
            if not item.unify:
                elem['torrent_info'] = '[%s]' % elem['torrent_info']

        # Si tiene contraseña, la guardamos y la pintamos
        if elem.get('password', '') or item.password:
            elem['password'] = elem.get('password', '') or item.password
            itemlist.append(item.clone(action="", title="[COLOR magenta] Contraseña: [/COLOR]'%s'" \
                                       % elem['password'], folder=False))

        # Guardamos urls de emergencia si se viene desde un Lookup de creación de Videoteca
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(elem['url'])                          # guardamos la url: la actualizará videolibrarytools
            item.emergency_urls[1].append(elem)                                 # guardamos el match
            item.emergency_urls[2].append(elem['url'])                          # guardamos la url o magnet inicial
            item.emergency_urls[3].append('#%s#%s' % (elem.get('quality', '') \
                                   or item.quality, elem['torrent_info']))      # Guardamos el torrent_info del .magnet
            if DEBUG: logger.debug('ELEM_OUT_EMER: %s' % elem)
            return elem

        elem['language'] = elem.get('language', item.language)
        if str(elem['language']).startswith('*'):
            elem['title'] = elem.get('title', item.title)
            elem['language'] = self.find_language(elem, item)
        
        elem['quality'] = elem.get('quality', item.quality)
        if str(elem['quality']).startswith('*'):
            elem['title'] = elem.get('title', item.title)
            elem['quality'] = self.find_quality(elem, item)
        if item.armagedon:
            elem['quality'] = '[COLOR hotpink][E][/COLOR] [COLOR limegreen]%s[/COLOR]' % elem['quality']

        # Ahora pintamos el link del Torrent
        elem['title'] = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][%s][/COLOR] '
        elem['title'] += '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' \
                        % (elem['quality'], str(elem['language']), elem['torrent_info'])
        elem['title'] = elem['title'].replace('*', '')

        # Preparamos título y calidad, quitando etiquetas vacías
        elem['title'] = re.sub(r'\s*\[COLOR\s*\w+\]\s*(?:\[\[*\s*\]*\])?\[\/COLOR\]', '', elem['title'])
        elem['title'] = re.sub(r'--|\[\s*\/*\]|\(\s*\/*\)|\|', '', elem['title']).strip()

        elem['quality'] = re.sub(r'\s*\[COLOR\s*\w+\]\s*(?:\[\[*\s*\]*\])?\[\/COLOR\]', '', elem['quality'])
        elem['quality'] = re.sub(r'--|\[\s*\/*\]|\(\s*\/*\)|\|', '', elem['quality']).strip()

        elem['alive'] = ''
        if not size or 'Magnet' in size:
            elem['alive'] = "??"                                                # Calidad del link sin verificar
        elif 'ERROR' in size and 'Pincha' in size:
            elem['alive'] = "ok"                                                # link en error, CF challenge, Chrome disponible
        elif 'ERROR' in size and 'Introduce' in size:
            elem['alive'] = "??"                                                # link en error, CF challenge, ruta de descarga no disponible
            elem['channel'] = 'setting'
            elem['action'] = 'setting_torrent'
            elem['unify'] = False
            elem['folder'] = False
            elem['item_org'] = item.tourl()
        elif 'ERROR' in size:
            elem['alive'] = "no"                                                # Calidad del link en error, CF challenge?
        else:
            elem['alive'] = "ok"                                                # Calidad del link verificada
        if elem['channel'] != 'setting':
            elem['action'] = "play"                                             # Visualizar vídeo
            elem['server'] = "torrent"                                          # Seridor Torrent

        if DEBUG: logger.debug('ELEM_OUT: %s' % elem)
        return elem

    def parse_finds_dict(self, soup, finds, year=False, next_page=False, c_type=''):

        matches = matches_init = [] if not year and not next_page else '-' if year else ''
        if not finds: 
            return matches
        
        match = soup
        json = {}
        level_ = ''
        block = ''
        f = ''
        tagOR_save = {}

        try:
            for x, (level_, block) in enumerate(finds.items()):
                level = re.sub('\d+', '', level_)
                for y, f in enumerate(block):
                    levels = {'find': [match.find, match.find_all], 
                              'find_all': [match.find, match.find_all], 
                              'find_parent': [match.find_parent, match.find_parents], 
                              'find_parents_all': [match.find_parent, match.find_parents],
                              'find_next_sibling': [match.find_next_sibling, match.find_next_siblings], 
                              'find_next_sibling_all': [match.find_next_sibling, match.find_next_siblings],
                              'find_previous_sibling': [match.find_previous_sibling, match.find_previous_siblings], 
                              'find_previous_siblings_all': [match.find_previous_sibling, match.find_previous_siblings],
                              'find_next': [match.find_next, match.find_all_next], 
                              'find_all_next': [match.find_next, match.find_all_next], 
                              'find_previous': [match.find_previous, match.find_all_previous], 
                              'find_all_previous': [match.find_previous, match.find_all_previous], 
                              'select_one': [match.select_one, match.select], 
                              'select_all': [match.select_one, match.select], 
                              'get_text': [match.get_text, match.get_text]
                              }
                    
                    soup_func = levels[level][0]
                    soup_func_all = levels[level][1]
                    
                    tag = ''
                    tagOR = False
                    attrs = {}
                    string = ''
                    regex = ''
                    argument = ''
                    strip = ''
                    json = {}
                    if isinstance(f, dict):
                        attrs = f.copy()
                        tagOR = match if attrs.get('tagOR', '') else False
                        tag = attrs.pop('tagOR', '') or attrs.pop('tag', '')
                        string = attrs.pop('string', '')
                        regex = attrs.pop('@TEXT', '')
                        regex_sub = attrs.pop('@SUB', '')
                        argument = attrs.pop('@ARG', '')
                        strip = attrs.pop('@STRIP', True)
                        json = attrs.pop('@JSON', {})
                    else:
                        tag = f
                    if (isinstance(tag, str) and tag == '*') or (isinstance(tag, list) and len(tag) == 1 and tag[0] == '*'): 
                        tag = None

                    if DEBUG: logger.debug('find: %s=%s: %s=%s, %s, %s, %s, %s' % (level, [key for key in f if key in ['tagOR', 'tag']], 
                                            tag, attrs, string, regex, argument, str(strip)))
                    if '_all' not in level or ('_all' in level and x < len(finds[level])-1):

                        if level == 'get_text':
                            match = soup_func(tag or '', strip=strip)
                            if regex:
                                if not isinstance(regex, list): regex = [regex]
                                for reg in regex:
                                    match = scrapertools.find_single_match(match, reg)
                            if regex_sub:
                                for reg_org, reg_des in regex_sub:
                                    match = re.sub(reg_org, reg_des, match)
                        elif regex or regex_sub:
                            if argument:
                                match = soup_func(tag, attrs=attrs, string=string).get(argument)
                            else:
                                match = soup_func(tag, attrs=attrs, string=string).text
                            if regex:
                                if not isinstance(regex, list): regex = [regex]
                                for reg in regex:
                                    match = scrapertools.find_single_match(match, reg)
                            if regex_sub:
                                for reg_org, reg_des in regex_sub:
                                    match = re.sub(reg_org, reg_des, match)
                        elif argument:
                            match = soup_func(tag, attrs=attrs, string=string).get(argument)
                        else:
                            match = soup_func(tag, attrs=attrs, string=string)
                    
                    else:
                        match = soup_func_all(tag, attrs=attrs, string=string)
                    if DEBUG and x < len(finds)-1: logger.debug('Matches[500] (%s/%s): %s' % (len(match) if isinstance(match, list) else 1, 
                                                                                              len(str(match)), str(match)[:500]))

                    if not match:
                        if tagOR:
                            match = tagOR
                            continue
                        if tagOR_save:
                            match = tagOR_save
                            tagOR_save = {}
                            break
                        break
                    if match:
                        if tagOR:
                            if y < len(f)-1:
                                tagOR_save = match
                                continue
                            break
                        continue
                if not match: break

            if json:
                try:
                    if DEBUG: logger.debug('Json[500] (%s/%s): %s' % (len(match) if isinstance(match, list) else 1, 
                                                                      len(str(match)), str(match)[:500]))
                    json_all_work = {}
                    json_all = jsontools.load(match)
                    if json_all:
                        match = []
                        json_match = {}
                        for json_field in json:
                            json_all_work = json_all.copy()
                            key_org, key_des = json_field.split('|')
                            key_org = key_org.split(',')
                            for key_org_item in key_org:
                                json_match[key_des] = json_all_work.get(key_org_item, '')
                                json_all_work = json_all_work.get(key_org_item, {})
                        match.append(json_match)
                except:
                    match = []
                    logger.error('Json[500] (%s/%s): %s' % (len(json_all_work.keys()), 
                                                            len(str(json_all_work)), str(json_all_work)[:500]))
                    logger.error(traceback.format_exc())
            
            if DEBUG: logger.debug('Matches[500] (%s/%s): %s' % (len(match) if isinstance(match, list) else 1, 
                                                                 len(str(match)), str(match)[:500]))
            
            matches = matches_init if not match else match
        except:
            logger.error('LEVEL: %s, BLOCK; %s, FUNC: %s, MATCHES-TYPE: %s, MATCHES[500]: %s' \
                         % (level, block, f, str(type(match)), str(match)[:500]))
            matches = matches_init
            logger.error(traceback.format_exc())

        return matches


class CustomChannel(AlfaChannelHelper):
    pass


class DictionaryAllChannel(AlfaChannelHelper):

    def list_all(self, item, data='', matches_post=None, postprocess=None, generictools=False, finds={}, **kwargs):
        logger.info()

        itemlist = list()
        matches = []
        matches_post_json_force = kwargs.pop('matches_post_json_force', False)

        if not finds: finds = self.finds
        if DEBUG: logger.debug('FINDS: %s' % finds)
        finds_out = finds.get('find', {})
        finds_next_page = finds.get('next_page', {})
        finds_next_page_rgx = finds.get('next_page_rgx', [['page\/\d+\/', 'page/%s/']])
        finds_last_page = finds.get('last_page', {})
        finds_year = finds.get('year', {})
        finds_season_episode = finds.get('season_episode', {})

        AHkwargs = {'soup': item.matches or {}, 'finds': finds, 'function': 'list_all'}

        # Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
        finds_controls = finds.get('controls', {})

        title_lista = []                                        # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
        if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
            title_lista.extend(item.title_lista)                                # Se usa la lista de páginas anteriores en Item
            del item.title_lista                                                # ... limpiamos

        curr_page = 1                                                           # Página inicial
        last_page = 99999 if not isinstance(finds_last_page, bool) else 0       # Última página inicial
        last_page_print = 1                                                     # Última página inicial, para píe de página
        page_factor = finds_controls.get('page_factor', 1.0 )                   # Factor de conversión de pag. web a pag. Alfa
        cnt_tot = finds_controls.get('cnt_tot', 30)                             # Poner el num. máximo de items por página
        cnt_tot_ovf = finds_controls.get('page_factor_overflow', 1.3)           # Overflow al num. máximo de items por página
        cnt_title = 0                                                           # Contador de líneas insertadas en Itemlist
        cnt_tot_match = 0.0                                                     # Contador TOTAL de líneas procesadas de matches
        custom_pagination =  finds_controls.get('custom_pagination', False)     # Paginación controlada por el usuario
        if item.cnt_tot_match:
            cnt_tot_match = float(item.cnt_tot_match)                           # restauramos el contador TOTAL de líneas procesadas de matches
            del item.cnt_tot_match
        if item.curr_page:
            curr_page = int(item.curr_page)                                     # Si viene de una pasada anterior, lo usamos
            del item.curr_page                                                  # ... y lo borramos
        if item.last_page:
            last_page = int(item.last_page)                                     # Si viene de una pasada anterior, lo usamos
            del item.last_page                                                  # ... y lo borramos
        if item.page_factor:
            page_factor = float(item.page_factor)                               # Si viene de una pasada anterior, lo usamos
            del item.page_factor                                                # ... y lo borramos
        if item.last_page_print:
            last_page_print = item.last_page_print                              # Si viene de una pasada anterior, lo usamos
            del item.last_page_print                                            # ... y lo borramos

        inicio = time.time()                                                    # Controlaremos que el proceso no exceda de un tiempo razonable
        fin = inicio + finds_controls.get('inicio', 5)                          # Después de este tiempo pintamos (segundos)
        timeout = finds.get('timeout', 15)                                      # Timeout normal
        timeout_search = timeout * 2                                            # Timeout para búsquedas

        post = item.post or finds_controls.pop('post', None)
        headers = item.headers or finds_controls.get('headers', {})
        forced_proxy_opt = finds_controls.get('forced_proxy_opt', None)
        host = finds_controls.get('host', self.host)
        host_referer = finds_controls.get('host_referer', host)
        url_replace = finds_controls.get('url_replace', [])
        url_base64 = finds_controls.get('url_base64', True)
        videolab_status = finds_controls.get('videolab_status', True)

        season_colapse = config.get_setting('season_colapse', item.channel, default=True)
        filter_languages = config.get_setting('filter_languages', item.channel, default=0)
        modo_grafico = config.get_setting('modo_grafico', item.channel, default=True)
        if not filter_languages: filter_languages = 0
        IDIOMAS_TMDB = finds_controls.get('IDIOMAS_TMDB', {}) or self.IDIOMAS_TMDB
        idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', item.channel, default=0)]    # Idioma base para TMDB
        if not idioma_busqueda: idioma_busqueda = 0
        idioma_busqueda_VO = IDIOMAS_TMDB[2]                                    # Idioma para VO: Local,VO

        next_page_url = item.url
        # Máximo num. de líneas permitidas por TMDB. Máx de 5 segundos por Itemlist para no degradar el rendimiento
        while (cnt_title < cnt_tot and (curr_page <= last_page or (last_page == 0 and finds_next_page and next_page_url)) \
                                   and fin > time.time()) or item.matches:
            
            # Descarga la página
            soup = data
            data = ''
            cnt_match = 0                                                       # Contador de líneas procesadas de matches
            if not item.matches:                                                # si no viene de una pasada anterior, descargamos
                soup = soup or self.create_soup(next_page_url, timeout=timeout_search, post=post, headers=headers, 
                                                forced_proxy_opt=forced_proxy_opt, **kwargs)
                if self.url:
                    next_page_url = self.url
                    self.url = ''
                if soup:
                    AHkwargs['soup'] = soup
                    curr_page += 1
                    matches = self.parse_finds_dict(soup, finds_out)
                    if matches_post and matches:
                        matches = matches_post(item, matches, **AHkwargs)
                        if custom_pagination:
                            if len(matches) < cnt_tot:
                                custom_pagination = False
                if not matches:
                    break
            else:
                matches =  AHkwargs['soup'] = item.matches
                del item.matches
                if matches_post_json_force and matches_post and matches: 
                    matches = matches_post(item, matches, **AHkwargs)
                    if custom_pagination:
                        if len(matches) < cnt_tot:
                            custom_pagination = False
            if DEBUG: logger.debug('MATCHES (%s/%s): %s' % (len(matches), len(str(matches)), str(matches)))

            # Buscamos la próxima página
            if soup:
                if finds_next_page:
                    next_page_url = self.parse_finds_dict(soup, finds_next_page, next_page=True, c_type=item.c_type).lstrip('#')
                elif last_page > 0:
                    for rgx_org, rgx_des in finds_next_page_rgx:
                        if scrapertools.find_single_match(item.url, rgx_org): break
                    else:
                        url = item.url.split('?')
                        item.url = url[0].rstrip('/') + finds_next_page_rgx[0][1] % str(curr_page)
                        if '?' in item.url and len(url) > 1: url[1] = url[1].replace('?', '&')
                        if len(url) > 1: item.url = '%s?%s' % (item.url, url[1].lstrip('/'))
                    for rgx_org, rgx_des in finds_next_page_rgx:
                        next_page_url = re.sub(rgx_org, rgx_des % str(curr_page), item.url.rstrip('/')).replace('//?', '/?')

            if DEBUG: logger.debug('curr_page: %s / last_page: %s / page_factor: %s / next_page_url: %s / matches: %s' \
                                    % (str(curr_page), str(last_page), str(page_factor), str(next_page_url), len(matches)))

            # Buscamos la última página
            if last_page == 99999:                                              # Si es el valor inicial, buscamos
                try:
                    last_page = int(self.parse_finds_dict(soup, finds_last_page, next_page=True, c_type=item.c_type).lstrip('#'))
                    page_factor = float(len(matches)) / float(cnt_tot)
                except:                                                         # Si no lo encuentra, lo ponemos a 999
                    last_page = 0
                    last_page_print = int((float(len(matches)) / float(cnt_tot)) + 0.999999)

                if DEBUG: logger.debug('curr_page: %s / last_page: %s / page_factor: %s / next_page_url: %s / matches: %s' \
                                        % (str(curr_page), str(last_page), str(page_factor), str(next_page_url), len(matches)))

            for elem in matches:
                new_item = Item()
                new_item.infoLabels = item.infoLabels
                cnt_match += 1

                new_item.channel = item.channel
                new_item.category = new_item.channel.capitalize()

                new_item.url = elem.get('url', '')
                if not new_item.url: continue
                new_item.url = urlparse.urljoin(self.host, new_item.url)
                
                new_item.title = elem.get('title', '')
                for clean_org, clean_des in finds.get('title_clean', []):
                    new_item.title = re.sub(clean_org, clean_des, new_item.title).strip()
                # Slugify, pero más light
                new_item.title = new_item.title.replace("á", "a").replace("é", "e").replace("í", "i")\
                                               .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                                               .replace("ï¿½", "ñ").replace("Ã±", "ñ")
                new_item.title = scrapertools.decode_utf8_error(new_item.title).strip()
                if not new_item.title: continue
                
                # Salvo que venga la llamada desde Episodios, se filtran las entradas para evitar duplicados de Temporadas
                if isinstance(finds_controls.get('duplicates', False), list) and self.tv_path in new_item.url and item.c_type != 'episodios':
                    url_list = new_item.url
                    for dup_org, dup_des in finds_controls['duplicates']:
                        if self.tv_path in new_item.url:
                            url_list = re.sub(dup_org, dup_des, new_item.url)
                    if url_list in title_lista:                                 # Si ya hemos procesado el título, lo ignoramos
                        if DEBUG: logger.debug('DUPLICADO %s' % url_list)
                        continue
                    else:
                        if DEBUG: logger.debug('AÑADIDO %s' % url_list)
                        title_lista += [url_list]                               # La añadimos a la lista de títulos
                
                if elem.get('thumbnail', ''): new_item.thumbnail = elem['thumbnail'] if elem['thumbnail'].startswith('http') \
                                                                   else urlparse.urljoin(self.host, elem['thumbnail'])
                if elem.get('quality', ''):
                    new_item.quality = elem['quality']
                    for clean_org, clean_des in finds.get('quality_clean', []):
                        new_item.quality = re.sub(clean_org, clean_des, new_item.quality).strip()
                if str(elem.get('quality', '')).startswith('*'):
                    elem['quality'] = new_item.quality
                    new_item.quality = self.find_quality(elem, item)

                if elem.get('language', self.language):
                    new_item.language = elem.get('language', self.language)
                    for clean_org, clean_des in finds.get('language_clean', []):
                        new_item.language = re.sub(clean_org, clean_des, new_item.language).strip()
                if '*' in str(elem.get('language', '')):
                    elem['language'] = new_item.language
                    new_item.language = self.find_language(elem, item)

                if 'VO' in str(new_item.language):
                    idioma_busqueda = idioma_busqueda_VO

                if elem.get('title_subs', []): new_item.title_subs =  elem['title_subs']

                if elem.get('plot', ''): new_item.contentPlot =  elem['plot']

                if elem.get('info', ''): new_item.info =  elem['info']

                if not new_item.infoLabels['year'] and (not elem.get('info', '') or elem.get('info', '') == '-'): 
                    new_item.infoLabels['year'] = elem.get('info', '')
                if elem.get('info', '') and elem.get('info', '') != '-': 
                    new_item.infoLabels['year'] = elem.get('info', '')

                if item.c_type == 'episodios':
                    new_item.contentType = 'episode'
                    new_item.contentSeason = int(elem.get('season', '1') or '1')
                    new_item.contentEpisodeNumber = int(elem.get('episode', '1') or '1')
                    new_item.title = '%sx%s - %s' % (new_item.contentSeason, new_item.contentEpisodeNumber, new_item.title)

                if item.c_type == 'peliculas': new_item.contentType = 'movie'
                new_item = self.define_content_type(new_item)

                if new_item.contentType != 'movie':
                    new_item.season_colapse = season_colapse

                new_item.context = "['buscar_trailer']"
                new_item.context = filtertools.context(new_item, self.list_language, self.list_quality_movies \
                                                       if new_item.contentType == 'movie' else self.list_quality_tvshow)

                new_item.url = self.do_url_replace(new_item.url, url_replace)

                if postprocess:
                    new_item = postprocess(elem, new_item, item, **AHkwargs)

                cnt_title += 1

                #Ahora se filtra por idioma, si procede, y se pinta lo que vale
                if filter_languages > 0 and self.list_language:                 # Si hay idioma seleccionado, se filtra
                    itemlist = filtertools.get_link(itemlist, new_item, self.list_language)
                else:
                    itemlist.append(new_item.clone())                           # Si no, se añade a la lista

                cnt_title = len(itemlist)                                       # Recalculamos los items después del filtrado
                if cnt_title >= cnt_tot and (len(matches) - cnt_match) + cnt_title > cnt_tot * cnt_tot_ovf:     # Contador de líneas añadidas
                    break
                
                #if DEBUG: logger.debug('New_item: %s' % new_item)

            matches = matches[cnt_match:]                                       # Salvamos la entradas no procesadas
            cnt_tot_match += cnt_match                                          # Calcular el num. total de items mostrados

        if DEBUG: logger.debug('curr_page: %s / last_page: %s / page_factor: %s / next_page_url: %s / matches: %s' \
                                % (str(curr_page), str(last_page), str(page_factor), str(next_page_url), len(matches)))

        if itemlist:
            tmdb.set_infoLabels_itemlist(itemlist, modo_grafico, idioma_busqueda=idioma_busqueda)

            for new_item in itemlist:
                if not isinstance(new_item.infoLabels['year'], int):
                    new_item.infoLabels['year'] = str(new_item.infoLabels['year']).replace('-', '')
            
            if generictools:
                # Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                from lib.generictools import post_tmdb_listado
                item, itemlist = post_tmdb_listado(item, itemlist)
            elif videolab_status:
                # Llamamos al método para encontrar el estado del vídeo en la videoteca
                from lib.generictools import AH_find_videolab_status
                itemlist = AH_find_videolab_status(item, itemlist, **AHkwargs)

        # Si es necesario añadir paginacion
        if (((curr_page <= last_page and last_page < 99999) or (last_page == 0 and len(matches) > 0) \
                                    or len(matches) > 0) and next_page_url) or custom_pagination:

            curr_page_print = int(cnt_tot_match / float(cnt_tot))
            if curr_page_print < 1:
                curr_page_print = 1
            if last_page:
                if last_page > 1:
                    last_page_print = int((last_page * page_factor) + 0.999999)
                title = '%s de %s' % (curr_page_print, last_page_print)
            else:
                title = '%s' % curr_page_print
            title = ">> Página siguiente %s" % title
            if item.infoLabels.get('mediatype'): del item.infoLabels['mediatype']

            itemlist.append(item.clone(action="list_all", title=title, 
                                       title_lista=title_lista, post=post, matches=matches, 
                                       url=next_page_url, last_page=str(last_page), curr_page=str(curr_page), 
                                       page_factor=str(page_factor), cnt_tot_match=str(cnt_tot_match), 
                                       last_page_print=last_page_print))

        return itemlist

    def section(self, item, data= '', action="list_all", matches_post=None, postprocess=None, 
                section_list={}, finds={}, **kwargs):
        logger.info()

        if not finds: finds = self.finds
        finds_out = finds.get('categories', {})
        itemlist = list()
        matches = list()
        soup = {}
        AHkwargs = {'soup': soup, 'finds': finds, 'function': 'section'}
        
        finds_controls = finds.get('controls', {})
        if DEBUG: logger.debug('FINDS_categories: %s; FINDS_controls: %s' % (finds_out, finds_controls))

        page = finds_controls.get('page', '')
        year = finds_controls.get('year', False)
        reverse = finds_controls.get('reverse', False)
        timeout = finds.get('timeout', 15)
        post = item.post or finds_controls.pop('post', None)
        headers = item.headers or finds_controls.get('headers', {})
        forced_proxy_opt = finds_controls.get('forced_proxy_opt', None)
        host = finds_controls.get('host', self.host)
        host_referer = finds_controls.get('host_referer', host)
        url_replace = finds_controls.get('url_replace', [])
        url_base64 = finds_controls.get('url_base64', True)

        if section_list:
            for genre, url in list(section_list.items()):
                matches.append({'url': url + page, 'title': genre})
        else:
            soup = data or self.create_soup(item.url, timeout=timeout, post=post, headers=headers, 
                                            forced_proxy_opt=forced_proxy_opt, **kwargs)
            AHkwargs['soup'] = soup
            matches_section = self.parse_finds_dict(soup, finds_out)
            
            if matches_post:
                matches = matches_post(item, matches_section, **AHkwargs)
            else:
                for elem in matches_section:
                    elem_json = {}
                    elem_json['url'] = elem.a["href"] + page
                    elem_json['title'] = elem.a.text
                    matches.append(elem_json.copy())

        if not matches:
            logger.error(finds_out)
            logger.error(soup or section_list)
            return itemlist

        for elem in matches:
            if not elem.get('url'): continue
            elem['url'] = urlparse.urljoin(self.host, elem['url'])

            new_item = item.clone(
                                  category=item.channel.capitalize(),
                                  title=elem.get('title', '').title(),
                                  action=action,
                                  url=elem['url']
                                  )
            if year and scrapertools.find_single_match(new_item.title, '\d{4}'):
                new_item.infoLabels = {'year': int(scrapertools.find_single_match(new_item.title, '\d{4}'))}

            if postprocess:
                new_item = postprocess(elem, new_item, item, **AHkwargs)

            new_item.url = self.do_url_replace(new_item.url, url_replace)

            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def seasons(self, item, data='', action="episodesxseason", matches_post=None, postprocess=None, 
                generictools=False, seasons_list={}, finds={}, **kwargs):
        logger.info()
        from lib.generictools import post_tmdb_findvideos, convert_url_base64, AH_find_videolab_status

        if not finds: finds = self.finds
        finds_out = finds.get('seasons', {})
        finds_season_num = finds.get('season_num', {})
        itemlist = list()
        matches = list()
        soup = {}
        AHkwargs = {'soup': soup, 'finds': finds, 'function': 'seasons'}

        finds_controls = finds.get('controls', {})
        if DEBUG: logger.debug('FINDS_seasons: %s; FINDS_season_num: %s; FINDS_season_num: %s' \
                                % (finds_out, finds_season_num, finds_controls))

        item.title  = item.title.replace('(V)-' , '')
        item.contentTitle  = item.contentTitle.replace('(V)-' , '')
        timeout = finds.get('timeout', 15)
        post = item.post or finds_controls.pop('post', None)
        headers = item.headers or finds_controls.get('headers', {})
        forced_proxy_opt = finds_controls.get('forced_proxy_opt', None)
        host = finds_controls.get('host', self.host)
        host_referer = finds_controls.get('host_referer', host)
        url_replace = finds_controls.get('url_replace', [])
        url_base64 = finds_controls.get('url_base64', True)
        add_video_to_videolibrary = finds_controls.get('add_video_to_videolibrary', True)
        videolab_status = finds_controls.get('videolab_status', True)

        modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel, default=True)
        season_colapse = config.get_setting('season_colapse', item.channel, default=True)
        filter_languages = config.get_setting('filter_languages', item.channel, default=0)
        modo_grafico = config.get_setting('modo_grafico', item.channel, default=True)
        if not filter_languages: filter_languages = 0
        IDIOMAS_TMDB = finds_controls.get('IDIOMAS_TMDB', {}) or self.IDIOMAS_TMDB
        idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', item.channel, default=0)]    # Idioma base para TMDB
        if not idioma_busqueda: idioma_busqueda = 0
        idioma_busqueda_VO = IDIOMAS_TMDB[2]                                    # Idioma para VO: Local,VO

        item.context = filtertools.context(item, self.list_language, self.list_quality_tvshow)

        item.url = self.do_url_replace(item.url, url_replace)

        if seasons_list:
            for elem in seasons_list:
                elem_json = {}

                elem_json['season'] = int(scrapertools.find_single_match(str(elem.get('season', '1')), '\d+') or '1')
                elem_json['url'] = elem.get('url', item.url)
                if not elem.get('url', ''): continue

                matches.append(elem_json)
        else:
            soup = data or self.create_soup(item.url, timeout=timeout, post=post, headers=headers, 
                                            forced_proxy_opt=forced_proxy_opt, **kwargs)
            AHkwargs['soup'] = soup
            matches_seasons = self.parse_finds_dict(soup, finds_out)

            if matches_post:
                matches = matches_post(item, matches_seasons, **AHkwargs)
            else:
                for elem in matches_seasons:
                    elem_json = {}

                    elem_json['season'] = elem_json.get('season', '')

                    if not elem_json.get('season'):
                        if finds_season_num: elem_json['season'] = int(self.parse_finds_dict(elem, finds_season_num))

                        try:
                            elem_json['season'] = int(elem.span.get_text(strip=True).lower().replace('temporada', ''))
                        except:
                            try:
                                elem_json['season'] = int(elem["value"])
                            except:
                                try:
                                    elem_json['season'] = int(re.sub('(?i)temp\w*\s*', '', elem.a.get_text(strip=True)))
                                except:
                                    ielem_json['season'] = 1
                    elem_json['url'] = elem.a.get("href", '') if "href" in str(elem) else item.url
                    if elem_json['url'].startswith('#'):
                        elem_json['url'] = urlparse.urljoin(item.url, elem_json['url'])

                    matches.append(elem_json.copy())

        if not matches:
            logger.error(finds_out)
            logger.error(soup or seasons_list)
            return itemlist

        if DEBUG: logger.debug('MATCHES (%s/%s): %s' % (len(matches), len(str(matches)), str(matches)))
        for elem in matches:
            elem['season'] = int(scrapertools.find_single_match(str(elem.get('season', '1')), '\d+') or '1')
            elem['url'] = elem.get('url', item.url)
            if url_base64: elem['url'] = convert_url_base64(elem['url'], self.host)

            new_item = item.clone(action=action,
                                  category=item.channel.capitalize(), 
                                  url=elem['url'], 
                                  url_tvshow = item.url, 
                                  contentSeason=elem['season'], 
                                  title='Temporada %s' % elem['season'],
                                  contentType='season'
                                 )

            if postprocess:
                new_item = postprocess(elem, new_item, item, **AHkwargs)

            new_item.url = self.do_url_replace(new_item.url, url_replace)

            itemlist.append(new_item)
            #if DEBUG: logger.debug('SEASONS: %s' % new_item)

        for new_item in itemlist:

            if new_item.quality:
                for clean_org, clean_des in finds.get('quality_clean', []):
                    new_item.quality = re.sub(clean_org, clean_des, new_item.quality).strip()
            if str(new_item.quality).startswith('*'):
                new_item.quality = self.find_quality(new_item, item)
            if not new_item.quality and item.quality:
                new_item.quality = item.quality

            if new_item.language:
                for clean_org, clean_des in finds.get('language_clean', []):
                    new_item.language = re.sub(clean_org, clean_des, new_item.language).strip()
            if '*' in str(new_item.language):
                new_item.language = self.find_language(new_item, item)
            if not new_item.language and item.language:
                new_item.language = item.language
            if 'VO' in str(new_item.language):
                idioma_busqueda = idioma_busqueda_VO

        if itemlist:
            itemlist = sorted(itemlist, key=lambda it: int(it.contentSeason))
            if (item.infoLabels.get('last_season_only', False) and item.add_videolibrary) \
                                or (modo_ultima_temp and item.library_playcounts):
                itemlist = [itemlist[-1]]

            tmdb.set_infoLabels_itemlist(itemlist, modo_grafico, idioma_busqueda=idioma_busqueda)

            if add_video_to_videolibrary:
                if generictools:
                    # Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                    item, itemlist = post_tmdb_seasons(item, itemlist)
                else:
                    if videolab_status:
                        # Llamamos al método para encontrar el estado del vídeo en la videoteca
                        itemlist = AH_find_videolab_status(item, itemlist, **AHkwargs)
                    itemlist = self.add_video_to_videolibrary(item, itemlist)
            

        return itemlist

    def episodes(self, item, data='', action="findvideos", matches_post=None, postprocess=None, 
                 generictools=False, episodes_list={}, finds={}, **kwargs):
        logger.info()
        from lib.generictools import post_tmdb_findvideos, convert_url_base64, AH_find_videolab_status
        from channels import filtertools

        if not finds: finds = self.finds
        finds_out = finds.get('episodes', {})
        finds_episode_num = finds.get('episode_num', [])
        do_episode_clean = finds.get('episode_clean', [])
        itemlist = list()
        matches = list()
        soup = {}
        AHkwargs = {'soup': soup, 'finds': finds, 'function': 'episodes'}

        finds_controls = finds.get('controls', {})
        if DEBUG: logger.debug('FINDS_episodes: %s; FINDS_controls: %s' % (finds_out, finds_controls))

        timeout = finds.get('timeout', 15)
        post = item.post or finds_controls.pop('post', None)
        headers = item.headers or finds_controls.get('headers', {})
        forced_proxy_opt = finds_controls.get('forced_proxy_opt', None)
        host = finds_controls.get('host', self.host)
        host_referer = finds_controls.get('host_referer', host)
        url_replace = finds_controls.get('url_replace', [])
        url_base64 = finds_controls.get('url_base64', True)
        min_temp = finds_controls.get('min_temp', False)
        add_video_to_videolibrary = finds_controls.get('add_video_to_videolibrary', True)
        videolab_status = finds_controls.get('videolab_status', True)
        
        modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', item.channel, default=True)
        season_colapse = config.get_setting('season_colapse', item.channel, default=True)
        filter_languages = config.get_setting('filter_languages', item.channel, default=0)
        modo_grafico = config.get_setting('modo_grafico', item.channel, default=True)
        if not filter_languages: filter_languages = 0
        IDIOMAS_TMDB = finds_controls.get('IDIOMAS_TMDB', {}) or self.IDIOMAS_TMDB
        idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', item.channel, default=0)]    # Idioma base para TMDB
        if not idioma_busqueda: idioma_busqueda = 0
        idioma_busqueda_VO = IDIOMAS_TMDB[2]                                    # Idioma para VO: Local,VO

        item.context = filtertools.context(item, self.list_language, self.list_quality_tvshow)
        
        if 'VO' in str(item.language):
            idioma_busqueda = idioma_busqueda_VO
        try:
            tmdb.set_infoLabels(item, modo_grafico, idioma_busqueda=idioma_busqueda)
        except:
            pass

        # Vemos la última temporada de TMDB y del .nfo
        if item.ow_force == "1":                                                # Si hay una migración de canal o url, se actualiza todo 
            modo_ultima_temp = False
        max_temp = int(item.infoLabels['number_of_seasons'] or 0)
        max_nfo = 0
        y = []
        if modo_ultima_temp and item.library_playcounts:                        # Averiguar cuantas temporadas hay en Videoteca
            patron = 'season (\d+)'
            matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
            for x in matches:
                y += [int(x)]
            max_nfo = max(y)
        if max_nfo > 0 and max_nfo != max_temp:
            max_temp = max_nfo
        if max_temp == 0 or max_nfo:
            modo_ultima_temp = min_temp = False

        item.url = self.do_url_replace(item.url, url_replace)

        if episodes_list:
            for elem in episodes_list:
                elem_json = {}

                elem_json['season'] = elem.get('season', item.contentSeason)
                elem_json['episode'] = int(scrapertools.find_single_match(str(elem.get('episode', '1')), '\d+') or '1')
                elem_json['url'] = elem.get('url', '')
                if not elem.get('url', ''): continue
                elem_json['title'] = elem.get('title', '')
                elem_json['quality'] = elem.get('quality', '')
                elem_json['language'] = elem.get('language', '')
                elem_json['server'] = elem.get('server', '')
                elem_json['size'] = elem.get('size', '')
                elem_json['plot'] = elem.get('plot', item.contentPlot)

                matches.append(elem_json)
        else:
            soup = data or self.create_soup(item.url, timeout=timeout, post=post, headers=headers, 
                                            forced_proxy_opt=forced_proxy_opt, **kwargs)
            AHkwargs['soup'] = soup
            matches_episodes = self.parse_finds_dict(soup, finds_out)

            if matches_post:
                matches = matches_post(item, matches_episodes, **AHkwargs)

        if not matches:
            logger.error(finds_out)
            logger.error(soup or episodes_list)
            return itemlist

        infolabels = item.infoLabels

        if DEBUG: logger.debug('MATCHES (%s/%s): %s' % (len(matches), len(str(matches)), str(matches)))
        for elem in matches:

            if not elem.get('url', ''): continue
            if url_base64: elem['url'] = convert_url_base64(elem['url'], self.host)

            infolabels["season"] = elem.get('season', item.contentSeason)

            infolabels["episode"] = elem.get('episode', 1)
            if isinstance(finds_episode_num, list):
                for episode_num in finds_episode_num:
                    if scrapertools.find_single_match(elem.get('title', ''), episode_num):
                        infolabels["episode"] = int(scrapertools.find_single_match(elem.get('title', ''), episode_num))
                        break
                else:
                    infolabels["episode"] = int(scrapertools.find_single_match(str(elem.get('episode', '1')), '\d+') or '1')

            if isinstance(do_episode_clean, list):
                for episode_clean in do_episode_clean:
                    if scrapertools.find_single_match(elem.get('title', ''), episode_clean):
                        elem['title'] = scrapertools.find_single_match(elem['title'], episode_clean).strip()
                        break
            elem['title'] = elem.get('title', '').strip()
            if elem['title']:
                elem['title'] = scrapertools.slugify(elem.get('title', '').strip(), strict=False)
                infolabels = episode_title(elem['title'].capitalize(), infolabels)
            elem['title'] = "%sx%s - %s" % (item.contentSeason, infolabels["episode"], elem['title'] or item.contentSerieName)

            new_item = Item(channel=item.channel,
                            category=item.channel.capitalize(), 
                            url=elem['url'], 
                            url_tvshow = item.url_tvshow, 
                            title=elem['title'],
                            action=action,
                            infoLabels=infolabels,
                            contentType='episode',
                            headers=headers,
                            quality=elem.get('quality', ''),
                            language=elem.get('language', ''),
                            contentPlot=elem.get('plot', item.contentPlot), 
                            thumbnail=elem.get('thumbnail', item.thumbnail), 
                            context=item.context, 
                            matches=[]
                           )

            if item.video_path: new_item.video_path = item.video_path

            if postprocess:
                new_item = postprocess(elem, new_item, item, **AHkwargs)

            new_item.url = self.do_url_replace(new_item.url, url_replace)
            
            itemlist.append(new_item)
            #if DEBUG: logger.debug('EPISODES: %s' % new_item)
            if new_item.url.startswith('magnet') or new_item.url.endswith('.torrent'):
                new_item.matches.append(elem)

        if itemlist:
            itemlist_copy = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))
            itemlist = []

            for new_item in itemlist_copy:

                if new_item.quality:
                    for clean_org, clean_des in finds.get('quality_clean', []):
                        new_item.quality = re.sub(clean_org, clean_des, new_item.quality).strip()
                if str(new_item.quality).startswith('*'):
                    new_item.quality = self.find_quality(new_item, item)
                if not new_item.quality and item.quality:
                    new_item.quality = item.quality

                if new_item.language:
                    for clean_org, clean_des in finds.get('language_clean', []):
                        new_item.language = re.sub(clean_org, clean_des, new_item.language).strip()
                if '*' in str(new_item.language):
                    new_item.language = self.find_language(new_item, item)
                if not new_item.language and item.language:
                    new_item.language = item.language
                if 'VO' in str(new_item.language):
                    idioma_busqueda = idioma_busqueda_VO

                # Comprobamos si hay más de un enlace por episodio, entonces los agrupamos
                if DEBUG and len(itemlist) > 0: 
                    logger.debug('EPISODE-DUP: SEASON: %s; EPISODE: %s; QUALITY: %s; LANGUAGE: %s; ' \
                                 'SEASON[-1]: %s; EPISODE[-1]: %s; QUALITY[-1]: %s; LANGUAGE[-1]: %s' \
                                 % (new_item.contentSeason, new_item.contentEpisodeNumber, 
                                    new_item.quality, new_item.language, 
                                    itemlist[-1].contentSeason, itemlist[-1].contentEpisodeNumber, 
                                    itemlist[-1].quality, itemlist[-1].language, ))
                if len(itemlist) > 0 and new_item.contentSeason == itemlist[-1].contentSeason \
                            and new_item.contentEpisodeNumber == itemlist[-1].contentEpisodeNumber \
                            and itemlist[-1].contentEpisodeNumber != 0:         # solo guardamos un episodio ...
                    if itemlist[-1].quality:
                        if new_item.quality not in itemlist[-1].quality:
                            itemlist[-1].quality += ", " + new_item.quality     # ... pero acumulamos las calidades
                    else:
                        itemlist[-1].quality = new_item.quality
                    if itemlist[-1].language:
                        if new_item.language and new_item.language[0] not in itemlist[-1].language:
                            itemlist[-1].language.extend(new_item.language)     # ... pero acumulamos los idiomas
                    elif new_item.language:
                        itemlist[-1].language = new_item.language
                    if new_item.matches: itemlist[-1].matches.append(new_item.matches[0])   # Salvado Matches en el episodio anterior
                    continue                                                    # ignoramos el episodio duplicado
                
                if modo_ultima_temp and item.library_playcounts:                # Si solo se actualiza la última temporada de Videoteca
                    if min_temp and new_item.contentSeason < max_temp:
                        if DEBUG: logger.debug('%s: &s: %s' % (str(min_temp), new_item.contentSerieName, new_item.title))
                        if 'continue' in str(min_temp): continue                # Ignora episodio
                        if 'break' in str(min_temp): break                      # Sale del bucle
                    if item_local.contentSeason < max_temp:
                        if DEBUG: logger.debug('%s: &s: %s' % (str(min_temp), new_item.contentSerieName, new_item.title))
                        continue                                                # Ignora episodio

                itemlist.append(new_item)

            tmdb.set_infoLabels_itemlist(itemlist, modo_grafico, idioma_busqueda=idioma_busqueda)

            # Requerido para FilterTools
            itemlist = filtertools.get_links(itemlist, item, self.list_language, self.list_quality_tvshow)
            #if DEBUG: logger.debug('EPISODE-LAST: %s' % itemlist[-1])

            if add_video_to_videolibrary:
                if generictools:
                    # Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                    item, itemlist = post_tmdb_episodios(item, itemlist)
                else:
                    if videolab_status:
                        # Llamamos al método para encontrar el estado del vídeo en la videoteca
                        itemlist = AH_find_videolab_status(item, itemlist, **AHkwargs)
                    itemlist = self.add_video_to_videolibrary(item, itemlist)

        return itemlist

    def get_video_options(self, item, url, data='', langs=[], matches_post=None, postprocess=None, 
                          verify_links=False, generictools=False, findvideos_proc=False, finds={}, **kwargs):
        logger.info()
        if DEBUG: logger.debug('FINDS: %s' % finds)
        from lib.generictools import post_tmdb_findvideos, convert_url_base64, AH_find_videolab_status

        if not finds: finds = self.finds
        finds_out = finds.get('findvideos', {})
        finds_langs = finds.get('langs', {})
        options = list()
        results = list()
        itemlist = []
        itemlist_total = []
        soup = {}
        AHkwargs = {'soup': soup, 'finds': finds, 'function': 'get_video_options', 'videolibrary': False}

        finds_controls = finds.get('controls', {})
        if DEBUG: logger.debug('FINDS_findvideos: %s; FINDS_langs: %s; FINDS_controls: %s' % (finds_out, finds_langs, finds_controls))

        item.title  = item.title.replace('(V)-' , '')
        item.contentTitle  = item.contentTitle.replace('(V)-' , '')
        timeout = finds.get('timeout', 15)
        post = item.post or finds_controls.pop('post', None)
        headers = item.headers or finds_controls.get('headers', {})
        forced_proxy_opt = finds_controls.get('forced_proxy_opt', forced_proxy_def)
        host = finds_controls.get('host_torrent', self.host)
        host_referer = finds_controls.get('host_torrent_referer', host)
        url_replace = finds_controls.get('url_replace', [])
        url_base64 = finds_controls.get('url_base64', True)
        add_video_to_videolibrary = finds_controls.get('add_video_to_videolibrary', True)
        videolab_status = finds_controls.get('videolab_status', True)

        filter_languages = config.get_setting('filter_languages', item.channel, default=0)
        modo_grafico = config.get_setting('modo_grafico', item.channel, default=True)
        if not filter_languages: filter_languages = 0
        IDIOMAS_TMDB = finds_controls.get('IDIOMAS_TMDB', {}) or self.IDIOMAS_TMDB
        idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', item.channel, default=0)]    # Idioma base para TMDB
        if not idioma_busqueda: idioma_busqueda = 0
        idioma_busqueda_VO = IDIOMAS_TMDB[2]                                    # Idioma para VO: Local,VO
        
        url = self.do_url_replace(url, url_replace)

        tmdb.set_infoLabels_item(item, modo_grafico, idioma_busqueda=idioma_busqueda)

        if data or item.matches:
            soup = data
            response = {
                        'data': data, 
                        'soup': soup, 
                        'sucess': False, 
                        'code': 0
                       }
            response = type('HTTPResponse', (), response)
        else:
            response = self.create_soup(url, resp=True, timeout=timeout, post=post, headers=headers, 
                                        forced_proxy_opt=forced_proxy_opt, **kwargs)
            soup = response.soup or {}
            AHkwargs['soup'] = soup
        
        langs = langs or self.parse_finds_dict(soup, finds_langs) or self.language

        if not item.matches:
            matches = self.parse_finds_dict(soup, finds_out)
            if matches_post and matches:
                matches, langs = matches_post(item, matches, langs, response, **AHkwargs)
        else:
            matches = item.matches
            if matches_post and matches and not isinstance(matches[0], dict):
                # Generar el json desde matches videoteca antiguos
                AHkwargs['videolibrary'] = True
                matches, langs = matches_post(item, matches, langs, response, **AHkwargs)
        if DEBUG: logger.debug('MATCHES (%s/%s): %s' % (len(matches), len(str(matches)), str(matches)))

        if not matches:
            if item.emergency_urls and not item.videolibray_emergency_urls:     # Hay urls de emergencia?
                item.armagedon = True                                           # Marcamos la situación como catastrófica 
                if len(item.emergency_urls) > 1:
                    matches = item.emergency_urls[1]                            # Restauramos matches de vídeos
                else:
                    matches = item.emergency_urls[0]                            # Restauramos torrents/magnetes
                if matches_post and matches and not isinstance(matches[0], dict):
                    # Generar el json desde matches videoteca antiguos
                    AHkwargs['videolibrary'] = True
                    matches, langs = matches_post(item, matches, langs, response, **AHkwargs)
            if not matches:
                if item.videolibray_emergency_urls:                             # Si es llamado desde creación de Videoteca...
                    return item                                                 # Devolvemos el Item de la llamada
                else:
                    return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

        # Si es un lookup para cargar las urls de emergencia en la Videoteca...
        if item.videolibray_emergency_urls:
            item.emergency_urls = []                                            # Iniciamos emergency_urls
            item.emergency_urls.append([])                                      # Reservamos el espacio para los .torrents locales
            item.emergency_urls.append([])                                      # Reservada para matches de los vídeos
            item.emergency_urls.append([])                                      # Reservada para urls de los vídeos
            item.emergency_urls.append([])                                      # Reservamos el espacio para los tamaños de los .torrents/magnets

        #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
        if generictools and not item.videolibray_emergency_urls:
            item, itemlist_total = post_tmdb_findvideos(item, itemlist_total)

        for _lang in langs or ['CAST']:
            lang = _lang

            if 'descargar' in lang: continue
            if 'latino' in lang: lang = ['LAT']
            if 'español' in lang: lang += ['CAST']
            if 'subtitulado' in lang: lang += ['VOS']

            for elem in matches:
                if not elem.get('url', ''): continue
                    
                elem['channel'] = item.channel
                elem['action'] = 'play'
                elem['language'] = elem.get('language', lang)

                if elem['url'].startswith('//'):
                    elem['url'] = 'https:%s' % elem['url']
                if url_base64: elem['url'] = convert_url_base64(elem['url'], host, referer=host_referer)

                # Tratamos las particulirades de los .torrents/magnets
                if elem.get('server', '').lower() == 'torrent':
                    elem = self.manage_torrents(item, elem, lang, soup, finds, **kwargs)

                options.append((lang, elem))
        
        # Si es un lookup para cargar las urls de emergencia en la Videoteca...
        if item.videolibray_emergency_urls:
            return item

        results.append([soup, options])

        if not findvideos_proc: return results[0]

        from channels import autoplay
        from channels import filtertools
        from core import servertools

        for lang, elem in results[0][1]:
            new_item = item.clone()
            
            if verify_links and elem.get('server', '') and elem.get('server', '').lower() != 'torrent':
                if config.get_setting("hidepremium") and not servertools.is_server_enabled(elem['server']):
                    continue
                item_url = elem['url']
                if not isinstance(verify_links, bool): item_url = verify_links(Item(url=item_url, server=elem['server']))[0].url
                elem['alive'] = servertools.check_video_link(item_url, elem['server'])  # Link Activo ?
                if 'NO' in elem['alive']:
                    continue
            
            new_item.channel = elem.get('channel', item.channel)
            new_item.category = new_item.channel.capitalize()
            new_item.action = elem.get('action', 'play')
            new_item.url = elem.get('url', '')
            new_item.server = elem.get('server', '')
            new_item.title = elem.get('title', '%s')
            new_item.headers = headers or {'Referer': item.url}
            new_item.setMimeType = 'application/vnd.apple.mpegurl'

            if elem.get('quality', ''):
                new_item.quality = elem['quality']
                for clean_org, clean_des in finds.get('quality_clean', []):
                    new_item.quality = re.sub(clean_org, clean_des, new_item.quality).strip()
            if str(elem.get('quality', '')).startswith('*'):
                elem['quality'] = new_item.quality
                new_item.quality = self.find_quality(elem, item)

            if elem.get('language', lang):
                new_item.language = elem['language']
                for clean_org, clean_des in finds.get('language_clean', []):
                    new_item.language = re.sub(clean_org, clean_des, new_item.language).strip()
            if '*' in str(elem.get('language', '')):
                elem['language'] = new_item.language
                new_item.language = self.find_language(elem, item)
            if not new_item.language: new_item.language = [lang]

            if elem.get('plot', ''): new_item.contentPlot = elem['plot']
            if elem.get('torrent_info', ''): new_item.torrent_info = elem['torrent_info']
            if elem.get('torrents_path', ''): new_item.torrents_path = elem['torrents_path']
            if elem.get('torrent_alt', ''): new_item.torrent_alt = elem['torrent_alt']
            if elem.get('alive', ''): new_item.alive = elem['alive']
            if elem.get('unify', ''): new_item.unify = elem['unify']
            if elem.get('folder', ''): new_item.folder = elem['folder']
            if elem.get('item_org', ''): new_item.item_org = elem['item_org']
            new_item.size = self.convert_size(elem.get('size', 0))

            if new_item.server.lower() != 'torrent':
                new_item.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][%s][/COLOR] '
                new_item.title += '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' \
                                    % (new_item.quality, str(new_item.language), new_item.torrent_info)

            if postprocess:
                new_item = postprocess(elem, new_item, item, **AHkwargs)

            new_item.url = self.do_url_replace(new_item.url, url_replace)

            itemlist.append(new_item)

        # Requerido para FilterTools
        itemlist = filtertools.get_links(itemlist, item, self.list_language, self.list_quality_movies \
                                                       if new_item.contentType == 'movie' else self.list_quality_tvshow)

        if itemlist:
            try:
                itemlist = servertools.get_servers_itemlist(itemlist, lambda it: it.title % it.server.capitalize())
            except:
                pass
            else:
                itemlist = sorted(itemlist, key=lambda it: (-it.size, it.language[0], it.server))
                if not generictools:
                    if videolab_status:
                        # Llamamos al método para encontrar el estado del vídeo en la videoteca
                        itemlist = AH_find_videolab_status(item, itemlist, **AHkwargs)
                    if add_video_to_videolibrary:
                        itemlist = self.add_video_to_videolibrary(item, itemlist, contentType=item.contentType)
                

            itemlist_total.extend(itemlist)

        # Requerido para AutoPlay
        autoplay.start(itemlist_total, item)

        return itemlist_total


class DooPlay(AlfaChannelHelper):

    def __init__(self, host, canonical={}, channel='', finds={}, debug=False,
                 list_language=[], list_quality=[], list_quality_tvshow=[], list_quality_movies=[], 
                 list_servers=[], language=[], idiomas={}, url_replace=[]):
        global DEBUG
        DEBUG = debug

        self.host = host
        self.canonical = canonical
        self.channel = channel
        self.finds = finds or {'find': {'find': [{'tagOR': ['div'], 'id': ['archive-content']}, 
                                                 {'tag': ['div'], 'class': ['content', 'result-item']}], 
                                        'find_all': [{'tag': ['article'], 'class': ['item movies', 'item tvshows']}]},
                               'categories': {'find': [{'tag': ['li'], 'id': ['menu-item-%s']}, {'tag': ['ul'], 'class': ['sub-menu']}], 
                                              'find_all': [{'tag': ['li']}]}, 
                               'search': {'find_all': [{'tag': ['div'], 'class': ['result-item']}]}, 
                               'get_language': {'find_all': [{'tag': ['span'], 'class': ['flag']}]}, 
                               'get_language_rgx': '(?:flags\/|-)(\w+)\.(?:png|jpg|jpeg|webp)', 
                               'get_quality': {'find': [{'tag': ['span'], 'class': ['quality']}], 'get_text': [{'strip': True}]}, 
                               'get_quality_rgx': '', 
                               'next_page': {}, 
                               'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
                               'last_page': {'find': [{'tag': ['div'], 'class': ['pagination']}, {'tag': ['span']}], 
                                             'get_text': [{'@TEXT': '(?i)\d+\s*de\s*(\d+)'}]}, 
                               'year': {'find': [{'tag': ['div'], 'class': ['metadata']}, {'tag': ['span']}], 
                                        'find_next': [{'tag': ['span']}], 'get_text': [{'strip': True, '@TEXT': '(\d{4})'}]}, 
                               'season_episode': {'find': [{'tag': ['img'], '@ARG': 'alt', '@TEXT': '(?i)(\d+x\d+)'}]}, 
                               'seasons': {'find': [{'tag': ['div'], 'id': ['seasons']}], 
                                           'find_all': [{'tag': ['div'], 'class': ['se-q']}]}, 
                               'season_num': {'find': [{'tag': ['span'], 'class': ['se-t'], '@TEXT': '(\d+)'}]}, 
                               'episode_url': '', 
                               'episodes': {'find': [{'tag': ['div'], 'id': ['seasons']}], 
                                            'find_all': [{'tag': ['li']}]}, 
                               'episode_num': {'find': [{'tag': ['div'], 'class': ['numerando']}], 'get_text': [{'strip': True}]}, 
                               'episode_clean': [], 
                               'plot': {'find': [{'tag': ['div'], 'class': ['texto', 'contenido']}], 'get_text': [{'strip': True}]}, 
                               'findvideos': {'find': [{'tagOR': ['div'], 'id': ['playeroptions']}, 
                                                       {'tag': ['ul'], 'class': ['options']}], 
                                              'find_all': [{'tag': 'li'}]}, 
                               'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', ''],
                                              ['[\(|\[]\s*[\)|\]]', '']],
                               'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real', ''], 
                                                 ['extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
                               'language_clean': [], 
                               'url_replace': [], 
                               'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False, 
                                            'add_video_to_videolibrary': True, 'get_lang': False, 
                                            'custom_pagination': False}, 
                               'timeout': 5}
        self.url = self.movie_path = self.tv_path = self.movie_action = self.tv_action = ''
        self.doo_url = "%swp-admin/admin-ajax.php" % host
        self.list_language = list_language
        self.list_quality = self.list_quality_tvshow = list_quality or list_quality_tvshow
        self.list_quality_movies = list_quality_movies
        self.list_servers = list_servers
        self.language = language
        self.idiomas = idiomas or IDIOMAS
        self.url_replace = url_replace


    def list_all_matches(self, item, matches_int, **AHkwargs):
        logger.info()

        matches = []
        finds = self.finds
        
        if item.json:
            json = jsontools.load(matches_int)
    
            for key, elem in list(json.items()):
                elem_json = {}

                elem_json['url'] = elem.get('url', '')
                elem_json['title'] = elem.get('title', '')
                elem_json['thumbnail'] = elem.get('thumb', '') or elem.get('thumbnail', '') or elem.get('img', '')
                if ('tmdb' in elem_json['thumbnail'] or 'imdb' in elem_json['thumbnail']) and '=http' in elem_json['thumbnail']:
                    elem_json['thumbnail'] = scrapertools.find_single_match(self.do_unquote(elem_json['thumbnail']), '=(.*?)[&|$]')
                elem_json['year'] = elem.get('year', '-') or '-'
                if elem.get('info', ''):
                    elem_json['plot'] = elem['info']
                
                if not elem_json['url']: continue

                matches.append(elem_json.copy())

        else:
            for elem in matches_int:
                elem_json = {}
                if DEBUG: logger.debug('MATCHES_int %s' % (str(elem)))

                if item.c_type == 'episodios':
                    sxe = self.parse_finds_dict(elem, finds.get('season_episode', {}), c_type=item.c_type)
                    elem_json['season'], elem_json['episode'] = sxe.split('x')
                    elem_json['season'] = int(elem_json['season'] or 1)
                    elem_json['episode'] = int(elem_json['episode'] or 1)
                    elem_json['year'] = '-'

                elem_json['url'] = elem.a.get('href', '')
                elem_json['title'] = elem.img.get('alt', '') if item.c_type != 'episodios' \
                                                             else elem.img.get('alt', '').replace(sxe, '').strip()
                elem_json['quality'] = '*%s' % self.parse_finds_dict(elem, finds.get('get_quality', {}), c_type=item.c_type)
                elem_json['thumbnail'] = elem.img.get('src', '')
                if ('tmdb' in elem_json['thumbnail'] or 'imdb' in elem_json['thumbnail']) and '=http' in elem_json['thumbnail']:
                    elem_json['thumbnail'] = scrapertools.find_single_match(self.do_unquote(elem_json['thumbnail']), '=(.*?)[&|$]')
                elem_json['year'] = self.parse_finds_dict(elem, finds.get('year', {}), year=True, c_type=item.c_type)
                if self.parse_finds_dict(elem, finds.get('plot', {}), c_type=item.c_type):
                    elem_json['plot'] = self.parse_finds_dict(elem, finds.get('plot', {}), c_type=item.c_type)

                if not elem_json['url']: continue
                    
                if finds['controls']['get_lang']: 
                        self.get_language_and_set_filter(elem, elem_json)
                        elem_json['language'] = '*%s' % elem_json['language']

                matches.append(elem_json.copy())

        return matches

    def episodesxseason_matches(self, item, matches_int, **AHkwargs):
        logger.info()

        matches = []
        finds = self.finds
        if DEBUG: logger.debug('MATCHES_int %s' % (str(matches_int)))

        for x, elem in enumerate(matches_int):
            elem_json = {}

            try:
                seasonxepi = self.parse_finds_dict(elem, finds.get('episode_num', {}), c_type='episodios')
                if seasonxepi: season, elem_json["episode"] = seasonxepi.split(" - ")
                season = int(season)
                elem_json["episode"] = int(elem_json["episode"])
            except:
                logger.error('ERROR en seasonxepi: %s' % elem)
                logger.error(traceback.format_exc())
                continue

            if item.contentSeason != season: continue

            elem_json['url'] = elem.a.get("href", '')
            try:
                elem_json['title'] = elem.find("div", class_="episodiotitle").get_text('|', strip=True).split('|')[0]
            except:
                logger.error(traceback.format_exc())

            elem_json['season'] = item.contentSeason
            elem_json['thumbnail'] = elem.img.get('src', '')

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())

        return matches

    def findvideos_matches(self, item, matches_int, langs, response, **AHkwargs):
        logger.info()

        matches = []
        finds = self.finds

        for elem in matches_int:
            elem_json = {}

            post = {"action": "doo_player_ajax",
                    "post": elem.get("data-post", ""),
                    "nume": elem.get("data-nume", ""),
                    "type": elem.get("data-type", "")
                   }

            if DEBUG: logger.debug('MATCHES_int %s; POST: %s' % (str(elem), str(post)))
            response = self.create_soup(self.doo_url, resp=True, timeout=self.finds.get('timeout', 5), post=post)

            if response.json:
                if DEBUG: logger.debug('MATCHES_JSON %s' % (str(response.json)))
                elem_json['url'] = response.json.get("embed_url", "")
                if 'base64,' in elem_json['url']: 
                    #elem_json['url'] = base64.b64decode(scrapertools.find_single_match(elem_json['url'], 'base64,([^"]+)"')).decode('utf-8')
                    continue
                elem_json['quality'] = '*'
                elem_json['title'] = '%s'

                if not elem_json['url'] or "youtube" in elem_json['url'] or "waaw" in elem_json['url'] \
                                        or "jetload" in elem_json['url']:
                    continue

                if finds['controls']['get_lang']: 
                    self.get_language_and_set_filter(elem, elem_json)
                    elem_json['language'] = '*%s' % elem_json['language']

                matches.append(elem_json.copy())

        return matches, langs


class ToroFilm(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="post-lst").find_all("article", class_="post")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find("div", class_="nav-links").find_all("a")[-1]["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.h2.text
            except:
                logger.error(elem)
                continue
            try:
                thumb = elem.find("img")["data-src"]
            except:
                thumb = elem.find("img")["src"]

            try:
                year = int(elem.find("span", class_="year").text)
            except:
                year = '-'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item = self.define_content_type(new_item)
            
            new_item.url = self.do_url_replace(new_item.url)

            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 next_limit=next_limit
                                 )
                               )
        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()

        reverse = True if section == "year" else False
        
        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "alpha":
                    matches = soup.find("ul", class_="az-lst")
                elif section == "year":
                    matches = soup.find("section", id=re.compile(r"torofilm_movies_annee-\d+"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)
        
        if reverse:
            return itemlist[::-1]
        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("li", class_="sel-temp")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem.a["data-season"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'
            post_id = elem.a["data-post"]

            new_item = Item(channel=item.channel,
                            title=title,
                            action='episodesxseason',
                            post_id=post_id,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_video_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        infolabels = item.infoLabels
        season = infolabels["season"]

        post = {"action": "action_select_season",
                "season": season,
                "post": item.post_id
                }
        
        try:
            soup = self.create_soup(self.doo_url, post=post)

            matches = soup.find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches:
            try:
                url = elem.a["href"]
                title = elem.find("span", class_="num-epi").text
            except:
                continue
            try:
                infolabels["episode"] = int(title.split("x")[1])
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            infolabels = episode_title(title, infolabels)
            title = "%sx%s - %s" % (season, infolabels["episode"], title)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):

        options = list()
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)

            matches = soup.find_all("ul", class_="aa-tbs aa-tbs-video")
        except:
            matches = []
            logger.error(traceback.format_exc())

        for opt in matches:
            options.extend(opt.find_all("li"))

        results.append([soup, options])

        return results[0]


class ToroPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost C"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.a.h3.text
                thumb = elem.find("img")
                thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            except:
                logger.error(elem)
                continue
            try:
                year = scrapertools.find_single_match(title, r'\((\d{4})\)')
                if not year:
                    year = elem.find("span", class_="Year").text
                year = int(year)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "genres":
                    matches = soup.find(id=re.compile(r"categories-\d+"))
                elif section == "alpha":
                    matches = soup.find("ul", class_="AZList")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("tbody").find_all("tr")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist
        
        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            try:
                year = int(elem.find("td", text=re.compile(r"\d{4}")).string)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_alpha',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("div", class_="Wdgt AABox")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        for elem in matches:
            try:
                infolabels["season"] = int(elem.find("div", class_="AA-Season")["data-tab"])
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_video_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("div", class_="Wdgt AABox")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:
            if elem.find("div", class_="AA-Season")["data-tab"] == str(season):
                epi_list = elem.find_all("tr")
                for epi in epi_list:
                    try:
                        url = epi.a["href"]
                        epi_name = epi.find("td", class_="MvTbTtl").a.text
                    except:
                        continue
                    try:
                        infolabels["episode"] = int(epi.find("span", class_="Num").text)
                    except:
                        infolabels["episode"] = 1
                    infolabels["mediatype"] = 'episode'
                    infolabels = episode_title(epi_name, infolabels)
                    title = "%sx%s - %s" % (season, infolabels["episode"], epi_name)

                    new_item = Item(channel=item.channel,
                                    title=title,
                                    url=url,
                                    action=action,
                                    infoLabels=infolabels
                                    )

                    if postprocess:
                        new_item = postprocess(soup, elem, new_item, item)

                    new_item.url = self.do_url_replace(new_item.url)
                    
                    itemlist.append(new_item)
                break

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)

            matches = soup.find("ul", class_="TPlayerNv").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]


class ToroFlix(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()
        
        try:
            soup = self.create_soup(item.url)
            matches = soup.find("ul", class_="MovieList").find_all("article", class_=re.compile("TPost B"))
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                url = urlparse.urljoin(self.host, elem.a["href"])
                title = elem.find(class_="Title").text
                thumb = elem.find("img")
                thumb = thumb["data-src"] if thumb.has_attr("data-src") else thumb["src"]
            except:
                logger.error(elem)
                continue
            try:
                year = int(elem.find("span", class_="Date").text)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all'
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
            elif section:
                if section == "genres":
                    matches = soup.find(id=(r"toroflix_genres_widget-2"))
                elif section == "alpha":
                    matches = soup.find("ul", class_="AZList")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def list_alpha(self, item, action="season", postprocess=None):

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("tbody").find_all("tr")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches)

        if not next_page:
            try:
                next_page = soup.find(class_="wp-pagenavi").find(class_="current").find_next_sibling()["href"]
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            info = elem.find("td", class_="MvTbTtl")
            thumb = elem.find("td", class_="MvTbImg").a.img["src"]
            url = info.a["href"]
            title = info.a.text.strip()
            try:
                year = int(elem.find("td", text=re.compile(r"\d{4}")).string)
            except:
                year = "-"
            
            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            thumbnail=thumb,
                            infoLabels={"year": year}
                            )

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_alpha',
                                 next_limit=next_limit
                                 )
                            )

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("section", class_="SeasonBx AACrdn")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(elem.a.span.text)
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'
            url = elem.a["href"]

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_video_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find_all("tr", class_="Viewed")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels
        season = infolabels["season"]

        for elem in matches:
            try:
                url = elem.find("td", class_="MvTbTtl").a["href"]
                epi_name = elem.find("td", class_="MvTbTtl").a.text
            except:
                continue
            try:
                infolabels["episode"] = int(elem.find("span", class_="Num").text)
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            infolabels = episode_title(epi_name, infolabels)
            title = "%sx%s - %s" % (season, infolabels["episode"], epi_name)

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                           )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
            
            if soup.find("div", class_="optns-bx"):
                matches = soup.find_all("button")
            else:
                matches = soup.find("ul", class_="ListOptions").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]


class PsyPlay(AlfaChannelHelper):

    def list_all(self, item, postprocess=None, lim_max=20):
        logger.info()

        itemlist = list()

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("div", class_="movies-list").find_all("div", class_="ml-item")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        matches, next_limit, next_page = self.limit_results(item, matches, lim_max=lim_max)
        if not next_page:
            try:
                item.url = re.sub(r"page/\d+/", "", item.url)
                next_page = soup.find("ul", class_="pagination").find("li", class_="active").next_sibling.a.text
                next_page = urlparse.urljoin(self.host, "page/%s/" % next_page)
                next_page = urlparse.urljoin(self.host, next_page)
            except:
                pass

        for elem in matches:
            try:
                thumb = urlparse.urljoin(self.host, elem.a.img.get("src", '') or elem.a.img.get("data-original", ''))
                title = elem.a.find("span", class_="mli-info").h2.text
                url = urlparse.urljoin(self.host, elem.a["href"])
            except:
                logger.error(elem)
                continue

            try:
                year = int(elem.find("div", class_="jt-info", text=re.compile("\d{4}")).text)
            except:
                year = "-"

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            thumbnail=thumb,
                            infoLabels={"year": year})

            new_item = self.define_content_type(new_item)

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        if next_page:
            itemlist.append(Item(channel=item.channel,
                                 title="Siguiente >>",
                                 url=next_page,
                                 action='list_all'
                                 )
                            )

        return itemlist

    def section(self, item, menu_id=None, section=None, action="list_all", postprocess=None):
        logger.info()

        itemlist = list()
        matches = list()
        reverse = True if section == "year" else False

        try:
            soup = self.create_soup(item.url)

            if menu_id:
                matches = soup.find("li", id="menu-item-%s" % menu_id).find("ul", class_="sub-menu")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches.find_all("li"):
            url = elem.a["href"]
            title = elem.a.text

            url = urlparse.urljoin(self.host, url)

            new_item = Item(channel=item.channel,
                            title=title.capitalize(),
                            action=action,
                            url=url,
                            c_type=item.c_type
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        if reverse:
            return itemlist[::-1]

        return itemlist

    def seasons(self, item, action="episodesxseason", postprocess=None):
        
        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)
            matches = soup.find("div", id="seasons").find_all("div", recursive=False)
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        infolabels = item.infoLabels

        for elem in matches:
            try:
                infolabels["season"] = int(scrapertools.find_single_match(elem.text, r"(\d+)"))
            except:
                infolabels["season"] = 1
            title = "Temporada %s" % infolabels["season"]
            infolabels["mediatype"] = 'season'

            new_item = Item(channel=item.channel,
                            title=title,
                            url=item.url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        itemlist = self.add_video_to_videolibrary(item, itemlist)

        return itemlist

    def episodes(self, item, action="findvideos", postprocess=None):
        logger.info()

        itemlist = list()
        item.url = self.do_url_replace(item.url)

        try:
            soup = self.create_soup(item.url)

            infolabels = item.infoLabels
            season = infolabels["season"]

            matches = soup.find("div", id="seasons").find_all("div", recursive=False)[int(season) - 1].find_all("a")
        except:
            matches = []
            logger.error(traceback.format_exc())

        if not matches:
            return itemlist

        for elem in matches:
            try:
                url = elem["href"]
            except:
                continue
            try:
                infolabels["episode"] = int(scrapertools.find_single_match(elem.text, r"(\d+)"))
            except:
                infolabels["episode"] = 1
            infolabels["mediatype"] = 'episode'
            title = "%sx%s - " % (season, infolabels["episode"])

            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action=action,
                            infoLabels=infolabels
                            )

            if postprocess:
                new_item = postprocess(soup, elem, new_item, item)

            new_item.url = self.do_url_replace(new_item.url)
            
            itemlist.append(new_item)

        tmdb.set_infoLabels_itemlist(itemlist, True)

        return itemlist

    def get_video_options(self, url, forced_proxy_opt=forced_proxy_def, referer=None):
        
        results = list()
        url = self.do_url_replace(url)

        try:
            soup = self.create_soup(url, forced_proxy_opt=forced_proxy_opt, referer=referer)
        
            matches = soup.find("ul", class_="idTabs").find_all("li")
        except:
            matches = []
            logger.error(traceback.format_exc())

        results.append([soup, matches])

        return results[0]
