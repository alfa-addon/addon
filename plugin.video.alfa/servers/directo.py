# -*- coding: utf-8 -*-

from platformcode import logger
from core import scrapertools
from core import urlparse

kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'ignore_response_code': True, 
          'timeout': 5, 'cf_assistant': False}


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    invaid_url ="No se ha encontrado un enlace. " \
                "Posiblemente sea un servidor no soportado."

    exists = True if page_url else False
    reason = invaid_url if not exists else ""
    # El sufijo de Alfa es "url|clave=valor&clave=valor" (Kodi lo entiende igual). Antes solo se
    # miraban |Referer y |ignore_response_code, asi que un |User-Agent= se quedaba DENTRO de la
    # URL: en un fichero normal eso da 415 y en una URL firmada (r2.cloudflarestorage.com,
    # X-Amz-) rompe la firma y da 403. Medido el 2026-10-16 con streamflix (415) y con 4khdhub
    # (403). Aqui se separa bien y cada clave va como cabecera.
    cabeceras = {'Range': 'bytes=0-100'}
    ignore_response_code = False

    if '|' in page_url:
        page_url, resto = page_url.split('|', 1)

        for trozo in resto.split('&'):
            if '=' not in trozo:
                continue

            clave, valor = trozo.split('=', 1)
            clave = clave.strip()
            valor = urlparse.unquote(valor.strip())

            if not clave:
                continue

            if clave.lower() == 'ignore_response_code':
                ignore_response_code = (valor.lower() == 'true')
            else:
                cabeceras[clave] = valor

    if page_url:
        pattern = r'(?:^[A-Za-z]+://|^/|^[A-Za-z]+:[\\/]+)\S+'
        match = scrapertools.find_single_match(page_url, pattern)
        exists = True if match else False
        reason = "" if exists else "Ruta o enlace inválido."

        if page_url.startswith('http'):
            from core import httptools
            response = httptools.downloadpage(page_url, headers=cabeceras, **kwargs)

            if not ignore_response_code and not response.sucess:
                if response.code != 403:
                    exists = False
                    reason = "El archivo no existe." if response.code == 404 else "Se ha producido un error en el servidor (%s)" % response.code

            else:
                content_type = response.headers.get('Content-Type', '').split(";")[0]
                exists = False if 'text' in content_type else True
                reason = "El enlace no es un video (se encontró tipo %s)." % content_type if not exists else ""

    if not exists and not ignore_response_code:
        reason += " Repórtalo en el foro https://alfa-addon.com\n"
    elif exists:
        # antes ponia aqui "Ha ocurrido un error con este video" INCLUSO cuando el video
        # existia: un mensaje de error en el caso bueno. Alfa solo usa el motivo si exists es
        # False, asi que era inocuo, pero ensuciaba el log.
        reason = ""

    return exists, reason

# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = [["%s [directo]" % page_url[-4:], page_url]]

    return video_urls
