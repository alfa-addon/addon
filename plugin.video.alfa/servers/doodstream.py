# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector DoodStream By Alfa development Group
# --------------------------------------------------------
import re
import time
import js2py
from core import httptools
from core import scrapertools
from platformcode import logger

count = 5
retries = count

kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 0,
          'CF': True, 'cf_assistant': False, 'ignore_response_code': True}

######### Si esta WARP 1.1.1.1 activado da error

def test_video_exists(page_url):
    global data, retries, host, redir
    logger.info("(page_url='%s'; retry=%s)" % (page_url, retries))

    # Sacar el dominio de la url con https:// delante (scheme true)
    host = httptools.obtain_domain(page_url, scheme=True)

    # Crear headers con Referer
    headers = httptools.default_headers.copy()
    headers['Referer'] = page_url

    # No usar redirecciones
    kwargs['follow_redirects'] = False

    # Poner los headers en kwargs
    kwargs['headers'] = headers

    # Descargar la página usando headers y referrer, y no seguir redirecciones
    response = httptools.downloadpage(page_url, **kwargs)

    # Si la pagina responde con un 403 con texto "Just a moment...", es un captcha de Cloudflare
    # Si no, se comprueba si el acceso al video está redireccionado (301) o si el archivo no existe (404).
    # Si no, cualquier otra respuesta diferente a 200 se loguea para su debug futuro.
    if response.code == 403:
        if "Just a moment..." in response.data:
            retries -= 1
            if retries >= 0:
                time.sleep(count - retries)
                return test_video_exists(page_url)
        else:
            logger.error("[Doodstream] El acceso al video está restringido.\n%s" % response.data)
            return False, "[Doodstream] El acceso al video está restringido. Reinténtalo más tarde"
    elif response.code == 404:
        return False, "[Doodstream] El archivo no existe o ha sido borrado"
    elif response.code in [301, 302]:
        redir = response.headers.get("location", '')
        if redir:
            if not redir.startswith("http"):
                redir = "%s%s" % (host, redir)
            page_url = redir
            test_video_exists(page_url)
    elif response.code != 200:
        logger.error("[Doodstream] Error al acceder al video. Código de respuesta: %s" % response.code)
        return False, "[Doodstream] Error al acceder al video. Código de respuesta: %s" % response.code

    # Si la página contiene un iframe con el enlace del video, se extrae el enlace y se redirige a él.
    if '/d/' in page_url and scrapertools.find_single_match(response.data, ' <iframe src="([^"]+)"'):
        url = scrapertools.find_single_match(response.data, ' <iframe src="([^"]+)"')
        redir = "%s%s" %(host,url)
        response = httptools.downloadpage(redir, **kwargs)

    # Si la página contiene el texto "Video not found", se considera que el video no existe.
    if "Video not found" in response.data:
        return False, "[Doodstream] El archivo no existe o ha sido borrado"

    # Se busca el código JavaScript que genera el enlace del video, si no se encuentra, se reintenta hasta 5 veces.
    # Si no se encuentra el código JavaScript, se considera que el es inaccesible o no existe.
    if not scrapertools.find_single_match(response.data, ("(function\s?makePlay.*?;})")) and retries >= 0:
        retries -= 1
        if retries >= 0:
            time.sleep(count - retries)
            return test_video_exists(page_url)
        logger.error("[Doodstream] No se ha encontrado el código JavaScript para generar el enlace del video.\n%s" % data)
        return False, "[Doodstream] No se ha podido comprobar si el video existe. Reinténtalo más tarde"

    retries = 5
    data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data, retries, host, redir
    logger.info("(page_url='%s'; retry=%s)" % (page_url, retries))
    video_urls = list()

    # Extraemos la etiqueta del formato del video (mp4, m3u8, etc.)
    label = scrapertools.find_single_match(data, r'type:\s*"video/([^"]+)"')
    # logger.error("label=%s" % label)

    # Extraemos el código JavaScript que genera el enlace del video.
    js_code = scrapertools.find_single_match(data, ("(function\s?makePlay.*?})"))
    if not js_code:
        logger.error("[Doodstream] No se ha encontrado el código JavaScript para generar el enlace del video.\n%s" % data)
        return video_urls
    # logger.error("js_code=%s" % js_code)

    # Quitamos la funcion Date.now() para posteriormente usar una nativa de Python.
    js_code = re.sub(r"\s+\+\s+Date.now\(\)", '', js_code)

    # Evaluamos el código JavaScript para obtener la función makePlay.
    # js2py.eval_js permite ejecutar código JavaScript en Python.
    # Esto es necesario porque el enlace del video se genera dinámicamente en el navegador.
    # js2py.eval_js devuelve una función que se puede llamar para obtener el enlace del video.
    js = js2py.eval_js(js_code)

    # Leemos la respuesta del código JavaScript y obtenemos el enlace del video.
    makeplay = js() + str(int(time.time()*1000))

    # logger.error("makeplay=%s" % makeplay)
    base_url = scrapertools.find_single_match(data, r"\$.get\('(/pass[^']+)'")

    # Concatenamos el enlace base con el enlace del host.
    url = "%s%s" % (host, base_url)
    # logger.error("url=%s" % url)

    # Generamos headers con Referer (basado en la url de redireccion).
    headers = httptools.default_headers.copy()
    headers['Referer'] = redir

    kwargs['headers'] = headers
    kwargs['follow_redirects'] = True

    # Realizamos una solicitud HTTP a la URL generada con los headers y redirecciones.
    response = httptools.downloadpage(url, **kwargs)
    # logger.error("response_code=%s" % response.code)

    # Si la respuesta no es 200, se reintenta hasta 5 veces.
    # Si falla, se registra el error y se devuelve una lista vacía.
    if response.code != 200:
        retries -= 1
        if retries >= 0:
            return get_video_url(page_url)
        else:
            return video_urls

    # Si la respuesta es 200 se obtiene el enlace del video,
    # y se elimina cualquier espacio en blanco adicional.
    new_data = re.sub(r'\s+', '', response.data)

    if "X-Amz-" in new_data:
        url = new_data
    else:
        url = new_data + makeplay + "|Referer=%s" % redir
    video_urls.append(['%s [doodstream]' % label, url])

    return video_urls