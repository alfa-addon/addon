# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vipporns By Alfa development Group
# --------------------------------------------------------
from core import urlparse as alfa_urlparse
import json
import re
import time

from core import httptools
from core import scrapertools
from core import urlparse
from platformcode import logger

from lib.kt_player import decode

# kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'ignore_response_code': True, 'cf_assistant': False}
# kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 3, 'ignore_response_code': True, 'cf_assistant': False}
kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 6, 'ignore_response_code': True, 
          'timeout': 45, 'cf_assistant': False, 'CF_stat': True, 'CF': True}

# Para la API de OK.RU (via generate_mp4) se manda un User-Agent de navegador explicito
NAVEGADOR = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

# https://trahkino.cc/video/353484/ necesita "False"
# https://www.porn00.org/ necesita "None"
#  generate_mp4  ENCRYPT  https://www.porngrey.net/video/charlie-red-enjoys-anal-in-a-wild-gonzo-scene_v1/  


def _generar_mp4(page_url, data):
    """Las URLs buenas de estas paginas estan en OK.RU, no en el dominio propio.

    Medido el 2026-10-16 en porndupe: su get_stream/<id>-<calidad>.mp4 solo funciona para algunos
    videos (para otros responde 5 bytes con "error", y Kodi falla con
    "CVideoPlayerDemo::OpenDemuxStream - Error creating demuxer"). Las que si van salen de aqui.
    """
    try:
        from lib.kt_player import saca_generate_mp4, descifra_token, url_okru, MAPA_CALIDADES_OKRU
    except ImportError:
        return []

    piezas = saca_generate_mp4(data)
    if not piezas:
        return []

    payload, clave, vids = piezas
    token = descifra_token(payload, clave)
    if not token:
        logger.error("ktp: generate_mp4 presente pero el token no sale (payload de %d)" % len(payload))
        return []

    # OJO: aqui NO se usan los kwargs del conector. Esos llevan el aparato de Cloudflare
    # (CF, retries_cloudflare, set_tls...) que hace falta para las paginas del sitio, pero esta es
    # una API JSON de OK.RU y con ellos la respuesta no llegaba a ser JSON ("Expecting value:
    # line 1 column 1", kodi.log 2026-10-16 00:53). Medido: con peticion limpia responde 200 con
    # las 8 calidades, con cualquier User-Agent.
    respuesta = None
    try:
        respuesta = httptools.downloadpage(url_okru(token, vids),
                                           headers={'User-Agent': NAVEGADOR,
                                                     'Accept': 'application/json, text/plain, */*'},
                                           ignore_response_code=True, timeout=20)
        cuerpo = respuesta.data
        # httptools puede devolver bytes, y si la peticion salio por otra via puede venir
        # comprimido en crudo: json.loads de eso da justo el "line 1 column 1" que se vio en Kodi.
        if isinstance(cuerpo, bytes):
            if cuerpo[:2] == b'\x1f\x8b':
                import gzip
                cuerpo = gzip.decompress(cuerpo)
            cuerpo = cuerpo.decode('utf-8', 'replace')
        # La API de OK.RU contesta JSON o su XML antiguo segun las cabeceras, asi que se
        # aceptan las dos formas. Medido (kodi.log 2026-10-16 00:56): con las cabeceras que
        # mete httptools devuelve
        #   <?xml ...?><video_get_response xmlns:ns2="http://api.forticom.com/1.0/">
        #   <video><url_mobile>https...
        # y una peticion limpia devuelve el mismo contenido en JSON.
        videos = []
        if cuerpo.lstrip().startswith('<'):
            import xml.etree.ElementTree as ET
            raiz = ET.fromstring(cuerpo)
            unico = {}
            for hijo in raiz.iter():
                if hijo.tag.startswith('url_') and hijo.text:
                    unico[hijo.tag] = hijo.text.strip()
            if unico:
                videos = [unico]
        else:
            datos = json.loads(cuerpo)
            videos = datos.get('videos') or []
    except Exception as e:
        logger.error("ktp: fallo pidiendo las URLs a OK.RU: %s | codigo=%s | respuesta=%r" % (
            str(e)[:70], getattr(respuesta, 'code', '?'),
            str(getattr(respuesta, 'data', ''))[:140]))
        return []

    salida = []
    if videos and isinstance(videos[0], dict):
        for clave_v, valor in videos[0].items():
            nombre = clave_v.replace('url_', '')
            if isinstance(valor, str) and valor.startswith('http'):
                salida.append([MAPA_CALIDADES_OKRU.get(nombre, nombre), valor])
    return salida


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    response = httptools.downloadpage(page_url, **kwargs)
    if response.code == 404 \
    or "cwtvembeds" in page_url \
    or "Page not Found" in response.data \
    or "File was deleted" in response.data \
    or "not allowed to watch this video" in response.data \
    or "video is a private" in response.data \
    or "is no longer available" in response.data\
    or "Embed Player Error" in response.data:
        return False, "[ktplayer] El fichero no existe o ha sido borrado"
    
    global data, host, license_code
    data = response.data
    
    host = alfa_urlparse.build_url(alfa_urlparse.urlunsplit(('https', u'{}'.format(scrapertools.get_domain_from_url(page_url)), "", "", "")), '/')
    license_code = scrapertools.find_single_match(response.data, 'license_code:\s*(?:\'|")([^\,]+)(?:\'|")')
    
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    invert = ""
    url = ""
    global data, host, license_code

    # 1) Si la pagina usa generate_mp4 (porndupe, porngrey), las URLs que funcionan salen de OK.RU.
    #    Es ADITIVO: si no hay generate_mp4 o falla, se sigue por el camino de siempre.
    for etiqueta, enlace in _generar_mp4(page_url, data):
        video_urls.append(['[ktplayer] %s' % etiqueta, enlace])

    if video_urls:
        return video_urls

    # data = httptools.downloadpage(page_url, **kwargs).data
    
    if "flashvars.video_url_text" in data: #sunporno
        data = scrapertools.find_single_match(data, '(flashvars.video_url[^\}]+)')
        patron = "(?:flashvars.video_url|flashvars.video_alt_url)\s*=\s*'([^']+)'.*?"
        patron += "(?:flashvars.video_url_text|flashvars.video_alt_url_text)\s*=\s*'([^']+)'"
    elif "video_url_text" in data:
        patron = '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += '(?:video_url_text|video_alt_url_text|video_alt_url[0-9]*_text):\s*(?:\'|")([^\,]+)(?:\'|")'
    else:
        patron = 'video_url:\s*(?:\'|")([^\,]+)(?:\'|").*?'
        patron += 'postfix:\s*(?:\'|")([^\,]+)(?:\'|")'
    matches = re.compile(patron,re.DOTALL).findall(data)
    logger.debug(matches)
    for url, quality in matches:
        if "?login" not in url and "signup" not in url and "_preview" not in url and ".mp4" in url:
            if "function/" in url:
                url = decode(url, license_code)
            elif url.startswith("/get_file/"):
                url = urlparse.urljoin(page_url, url)
            if "SD" in quality and not "Full" in quality:
                quality = "360p"
            if "HD" in quality and not "Full" in quality:
                quality = "720p"
            if "2K" in quality and not "Full" in quality:
                quality = "1080p"
            if "?br=" in url:
                # url += "&rnd=" + str(int(datetime.now().timestamp() * 1000))
                url = alfa_urlparse.append_query(url, [('rnd', str(int(time.time() * 1000)))])
            if not "analdin" in url and not "sunporno" in url and not "theyarehuge" in url:
                url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}'.format(host)})
            if "sunporno" in url or "theyarehuge" in url:
                url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, **kwargs).headers.get("location", "")
                if "theyarehuge" in url:
                    url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, **kwargs).headers.get("location", "")
            video_urls.append(['[ktplayer] %s' % quality, url])
        
        if "lq" in quality.lower() or "high" in quality.lower() or "low" in quality.lower():
            invert= "true"
        elif "mq" in quality.lower() or "hq" in quality.lower() or "full" in quality.lower(): ### 4kporn
            invert= "false"
    
    if "true" in invert:
        video_urls.reverse()
    elif "false" in invert:
        return video_urls
    else:
        video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    
    if not url:
        url = scrapertools.find_single_match(data, '(?:video_url|video_alt_url|video_alt_url[0-9]*):\s*(?:\'|")([^\,]+)(?:\'|").*?')
        if "allclassic.porn" in url:
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, **kwargs).headers.get("location", "")
        if not "allclassic.porn":
            url = alfa_urlparse.add_url_headers(url, {'Referer': u'{}'.format(host)})
        
        video_urls.append(['[ktplayer]', url])
    return video_urls

