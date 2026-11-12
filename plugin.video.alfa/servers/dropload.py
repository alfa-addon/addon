# Conector dropload / dr0pstream By Alfa development Group
# --------------------------------------------------------
# MEDIDO el 2026-10-16, con el log de Kodi 21 delante.
#
# La web esta detras de un **Cloudflare Turnstile**. Una peticion normal NO recibe el
# reproductor: recibe una pagina de 1.370 bytes con el widget del reto
#   <form action="" method="POST" id="F1"> op=embed  file_code=...
#   <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?compat=recaptcha">
#   data-sitekey="0x4AAAAAAEpU5huYpkxMDMFk"
# Esa pagina no trae `p,a,c,k,e,d` ni m3u8, y por eso get_video_url fallaba con
# "Could not make sense of p.a.c.k.e.r data". NO era el patron ni el desempaquetador.
#
# Quien pasa el reto es **Alfa Assistant** (es su trabajo). Dos cosas medidas:
#
#   1) `cf_cookie` tiene que ir como "URL|cookie", no con el nombre pelado. Con
#      `cf_cookie='cf_clearance'` el asistente responde
#      "Error syntax in param 'returnWhenCookieNameFound': url1|cookieName1|..." y
#      NO arranca (es el error exacto que salia en kodi.log). Ver cf_assistant.py:357.
#
#   2) `cf_assistant_get_source` NO sirve para esta web: el HTML que devuelve el asistente
#      viene indexado como "javascript:jscode" y cf_assistant.py:1056 lo descarta, porque
#      esa clave no coincide con la URL de la pagina. Con `formatJSdata=True` la funcion del
#      asistente devuelve ese HTML tal cual (alfa_assistant.py:1089), y es la via que se usa.
#
# Encadenado y comprobado el 2026-10-16 (asistente real 1.3.90 / WebView 138):
#   - el asistente tarda ~50 s: pasa el Turnstile, hace el POST del formulario y carga
#     jwplayer.js + provider.hlsjs.js
#   - el HTML resultante (111.781 chars) SI trae el bloque `p,a,c,k,e,d`
#   - al desempaquetarlo aparece
#     file:"https://ds4.dropcdn.io/hls2/01/00034/<id>_n/master.m3u8?t=..."
#   - o sea: la parte de get_video_url que ya existia era correcta; solo faltaba el HTML.
#
# Las cookies que devuelve el asistente (file_id, aff, vcap...) NO bastan para pedir la
# pagina desde fuera del WebView (medido: vuelve la pagina del reto). Por eso el HTML se
# pide al asistente y no se reintenta por HTTP.
# --------------------------------------------------------

import sys
import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger
from core import urlparse

forced_proxy_opt = ''  #'ProxySSL'

# Sin cf_assistant: el reto se resuelve aparte, en _pasa_el_reto (si no, httptools volveria a
# lanzar el asistente y se pagarian dos veces los ~50 s para nada).
kwargs = {'set_tls': None, 'set_tls_min': False, 'retries_cloudflare': 3,
          'ignore_response_code': True, 'cf_assistant': False, 'CF_stat': True, 'CF': True,
          'timeout': 15}


# https://dr0pstream.com/e/w4ptck2ikmh0   https://dr0pstream.com/embed-ecddux6obaee.html
# https://dr0pstream.com/e/ke4xwuxof0mb  https://dr0pstream.com/e/ecddux6obaee

# MEDIDO el 2026-10-16, con el DevTools del dueno delante: el CDN (ds4.dropcdn.io) responde
# **200 OK** al Chrome de escritorio de ESTE MISMO PC y **403** a `requests`, a
# `inputstream.adaptive` (Kodi) y al WebView del asistente. Mismo PC, misma IP, mismo token,
# las mismas cabeceras y SIN cookies -> el CDN discrimina por la HUELLA del cliente (TLS/HTTP2),
# no por el token ni por la IP (por eso WARP no arregla nada aqui).
# Desde el addon no se puede imitar esa huella; lo unico que queda es darle a Kodi las
# cabeceras EXACTAS del navegador del dueno, por si su libcurl pasa donde `requests` no pasa.
UA_NAVEGADOR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36")


def _sufijo_cabeceras(host):
    """Sufijo |clave=valor que Alfa convierte en cabeceras para el reproductor.

    Son las del DevTools del dueno (la peticion que dio 200 OK). Los valores van EN CRUDO, sin
    citar: Alfa ya los codifica al montar el sufijo (en el log se ve `Referer=https%3A%2F%2F...`),
    asi que citarlos aqui los codificaria dos veces y el User-Agent llegaria con %2F.
    """
    pares = [
        ('User-Agent', UA_NAVEGADOR),
        ('Accept', '*/*'),
        ('Accept-Language', 'es-ES,es;q=0.9,en;q=0.8'),
        ('Origin', host),
        ('Referer', host + '/'),
        ('Sec-Fetch-Dest', 'empty'),
        ('Sec-Fetch-Mode', 'cors'),
        ('Sec-Fetch-Site', 'cross-site'),
    ]
    return '|' + '&'.join('%s=%s' % (k, v) for k, v in pares)


def _pasa_el_reto(page_url, host):
    """Pide al asistente el HTML YA pasado el Turnstile.

    El asistente navega, resuelve el reto EL SOLO (el Turnstile va en modo `auto`) y hace el POST
    del formulario. No hace falta guion de pulsaciones: medido el 2026-10-16, con
    `return document.documentElement.outerHTML;` a secas sale el mismo HTML con el reproductor
    (111.781 chars, `p,a,c,k,e,d` incluido) que encadenando el guion de `get_jscode`.

    Lo que SI hace falta es pedir el DOM: sin `jsCode` el asistente devuelve `htmlSources` VACIO.
    Y `formatJSdata=True` hace que la funcion devuelva ese texto directamente
    (alfa_assistant.py:1089), en vez del JSON entero.
    """
    try:
        from lib import alfa_assistant

        html = alfa_assistant.get_urls_by_page_finished(
            page_url,
            timeout=25,
            jsCode="return document.documentElement.outerHTML;",
            # OJO: aqui NO se sustituye $HOST (eso lo hace cf_assistant), asi que va literal
            returnWhenCookieNameFound='%s|cf_clearance' % host,
            getCookies=True,
            disableCache=True,
            extraPostDelay=20,
            removeAllCookies=True,
            useAdvancedWebView=True,
            headers={'Referer': '%s/' % host, 'Origin': host},
            formatJSdata=True,
        )
    except Exception as e:
        logger.error('[dropload] el asistente fallo: %s' % e)
        return ''

    if not isinstance(html, str) or not html:
        logger.error('[dropload] el asistente no devolvio HTML (%r)' % (html,))
        return ''

    # El asistente devuelve el DOM como cadena JSON: sobra la comilla de fuera y los escapes.
    # Se limpia lo justo para que el desempaquetador encuentre el bloque.
    html = html.strip()
    if html.startswith('"') and html.endswith('"') and len(html) > 1:
        html = html[1:-1]
    html = (html.replace('\\n', '\n').replace('\\r', '\r')
                .replace('\\"', '"').replace('\\/', '/').replace('\\\\', '\\'))
    return html


def _trae_la_pagina(page_url, host):
    """Devuelve el HTML con el reproductor: primero por el asistente, si no por HTTP."""
    html = _pasa_el_reto(page_url, host)
    if html and 'p,a,c,k,e,d' in html:
        logger.info('[dropload] HTML con el reproductor, via asistente (%d chars)' % len(html))
        return html

    if html:
        logger.error('[dropload] el asistente devolvio %d chars SIN el reproductor '
                     '(¿sigue el reto pendiente?)' % len(html))
    return httptools.downloadpage(page_url, **kwargs).data


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, host, server

    domain = scrapertools.get_domain_from_url(page_url)
    host = "https://%s" % domain
    server = domain.split(".")[-2]

    data = _trae_la_pagina(page_url, host)

    if not data:
        return False, "[%s] No se pudo descargar la pagina" % server
    if "not found" in data or "no longer available" in data:
        return False, "[%s] El fichero no existe o ha sido borrado" % server
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    try:
        packed = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
        unpacked = jsunpack.unpack(packed)
        m3u8_source = scrapertools.find_single_match(unpacked, '(?:file|"hls2"|src):"([^"]+)"')

        if "bigbuttshub" in host:
            video_urls.append(['[%s] m3u' % server, m3u8_source])

        elif "master.m3u8" in m3u8_source:
            # MEDIDO el 2026-10-16: el CDN responde 403 a nuestra peticion de la url firmada (con
            # y sin Referer/Origin, con y sin las cookies de la web, con Range y con las cabeceras
            # EXACTAS del navegador). El navegador de escritorio del dueno, EN ESTE MISMO PC, si
            # recibe 200. Kodi pide el master con OTRA pila (inputstream.adaptive/libcurl), asi que
            # se le entrega igualmente, con las cabeceras del navegador: aqui no se decide por el.
            datos = httptools.downloadpage(m3u8_source, **kwargs).data

            if sys.version_info[0] >= 3 and isinstance(datos, bytes):
                datos = "".join(chr(x) for x in bytes(datos))

            sufijo = _sufijo_cabeceras(host)

            if datos:
                matches_m3u8 = re.compile('#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d*)[^\n]*\n([^\n]*)\n', re.DOTALL).findall(datos)
                for quality, url in matches_m3u8:
                    url = urlparse.urljoin(m3u8_source, url)
                    video_urls.append(['[%s] %s' % (server, quality), url + sufijo])

            if not video_urls:
                # Si no se pudo leer el master se entrega la url tal cual, con las cabeceras.
                # Devolver una lista VACIA dejaba la fuente sin nada que reproducir.
                logger.error('[dropload] no se pudo leer el master; se entrega la url igualmente')
                video_urls.append(['[%s] m3u' % server, m3u8_source + sufijo])
        else:
            video_urls.append(['[%s] m3u' % server, m3u8_source])

    except Exception as e:
        logger.error(e)
        unpacked = data
    return video_urls
