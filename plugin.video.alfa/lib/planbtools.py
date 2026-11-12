# -*- coding: utf-8 -*-
"""Resolución compartida de RepelisHD y SoloLatino."""
import sys
import traceback

from core import servertools, tmdb
from modules import autoplay, filtertools
from platformcode import config, logger


def host_alt_findb_fun(item, matches=None, host_alt_findb=None, seasons=False):
    matches = [] if matches is None else matches
    try:
        if sys.version_info[0] >= 3:
            from lib import planb_py3 as planb
        else:
            from lib import planb

        names = {1: 'e69org', 2: 'lsrc', 3: 'vhd', 4: 'psy', 5: 'vaplayer',
                 6: 'netmirror', 7: 'cuatrokhdhub', 8: 'streamflix',
                 9: 'vixsrc', 10: 'vidsrc', 11: 'unlimplay', 99: 'lsrc_temporadas'}
        sources = host_alt_findb or []
        if seasons:
            sources = [99] if seasons is True else seasons
        elif sources is True:
            sources = [1, 2]
        elif 'ALL' in sources:
            sources = sorted(key for key in names if key != 99)

        seen = set(match.get('url') for match in matches)
        for source in sources:
            resolver = getattr(planb, names.get(source, ''), None)
            if not callable(resolver):
                continue
            try:
                links = resolver(item.infoLabels)
                if seasons:
                    if isinstance(links, dict) and links:
                        return links
                    continue
                for link in links or []:
                    if not isinstance(link, (tuple, list)) or len(link) != 4:
                        continue
                    label, url, language, server = link
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    matches.append({'title': '%s', 'url': url, 'language': language,
                                    'server': server if isinstance(server, str) else '',
                                    'mediatype': item.contentType, 'quality': ''})
            except Exception:
                logger.error(traceback.format_exc())
    except Exception:
        logger.error(traceback.format_exc())
    return {} if seasons else matches


def build_findvideos(canonical, list_language, item):
    tmdb.set_infoLabels_item(item, True)
    matches = host_alt_findb_fun(item, host_alt_findb=canonical.get('host_alt_findb', []))
    itemlist = []
    for match in matches:
        itemlist.append(item.clone(action='play', url=match['url'], title='%s',
                                   language=match['language'], quality=match['quality'],
                                   server=match['server']))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda it: it.title % it.server.capitalize())
    if list_language:
        itemlist = filtertools.get_links(itemlist, item, list_language)
    itemlist.sort(key=lambda it: it.language)
    autoplay.start(itemlist, item)
    if (config.get_videolibrary_support() and itemlist and item.contentType == 'movie'
            and item.extra != 'findvideos'):
        itemlist.append(item.clone(title=config.get_localized_string(70146),
                                   action='add_pelicula_to_library', extra='findvideos'))
    return itemlist
