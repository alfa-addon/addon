# -*- coding: utf-8 -*-

from core import urlparse as alfa_urlparse
import sys
import re

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger
from bs4 import BeautifulSoup

kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

host = "https://stripchat.com"

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    global url,vid,data
    
    # El CDN del widget (lo resuelve findvideos) ya entrega HLS estandar y sirve
    # los segmentos: no hay token ni nada que comprobar.
    if 'growcdn' in page_url:
        return True, ""
    
    vd = page_url.split("|")
    url = vd[0]
    vid = vd[1]
    
    data = httptools.downloadpage(url, **kwargs).json
    
    if not 'public' in data["item"]['status']:
        return False, "[COLOR red][stripchat] Estoy en privado[/COLOR]"
    
    response = httptools.downloadpage(vid, **kwargs)
    if response.code == 404 or response.code == 401:
        return False, "[stripchat] El fichero no existe o ha sido borrado"
    
    
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    global url,vid,data
    
    if 'growcdn' in page_url:
        base = page_url.split("|")[0]
        cabeceras = "|Referer=%s/&Origin=%s" % (host, host)
        try:
            datos = httptools.downloadpage(base, **kwargs).data
            if isinstance(datos, bytes):
                datos = datos.decode('utf-8', 'replace')
        except Exception:
            datos = ''

        variantes = re.findall(r'#EXT-X-STREAM-INF[^\r\n]*RESOLUTION=\d+x(\d+)[^\r\n]*\r?\n([^\r\n#]+)', datos or '')
        lista = []
        for alto, enlace in variantes:
            enlace = enlace.strip()
            if not enlace.startswith('http'):
                enlace = urlparse.urljoin(base, enlace)
            lista.append((int(alto), enlace))

        lista.sort()
        for alto, enlace in lista:
            respuesta = httptools.downloadpage(enlace, **kwargs)
            comprobacion = getattr(respuesta, 'data', '') or ''
            if isinstance(comprobacion, bytes):
                comprobacion = comprobacion.decode('utf-8', 'replace')
            if getattr(respuesta, 'code', 0) != 200 or '#EXTM3U' not in comprobacion:
                logger.info("stripchat: variante %sp descartada (%s)" % (alto, getattr(respuesta, 'code', '?')))
                continue
            video_urls.append(["[stripchat] %sp" % alto, enlace + cabeceras])

        if not video_urls:
            logger.info("stripchat: ninguna variante responde, se entrega el master")
            video_urls.append(["[stripchat]", base + cabeceras])
        return video_urls
    
    data = data["item"]
    
    if data['settings'].get('presets', ''):
        datos = httptools.downloadpage(vid, **kwargs).data
        logger.debug(datos)
        if sys.version_info[0] >= 3 and isinstance(datos, bytes):
            datos = "".join(chr(x) for x in bytes(datos))
        
        if datos:
            #EXT-X-MOUFLON:PSCH:v1:Zokee2OhPh9kugh4
            psch = scrapertools.find_single_match(datos, ":PSCH:([A-z0-9:]+)")
            psch = psch.split(":")
            matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            ## matches_m3u8 = re.compile('#EXT-X-STREAM-INF\:[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
            for quality, url in matches_m3u8:
                ## url =urlparse.urljoin(m3u8_source,url)
                url += "?psch=%s&pkey=%s&playlistType=lowLatency" %(psch[0],psch[1])
                url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}/'.format(u'{}'.format(host)), 'Origin': u'{}'.format(host)})
                # url += "|Referer=%s/" % host
                video_urls.append(["[stripchat] %sp" % quality, url])
    
    else:
        # url += "|Referer=%s/&Origin=%s" % (host, host)
        video_urls.append(["[stripchat]", vid])
    return video_urls
