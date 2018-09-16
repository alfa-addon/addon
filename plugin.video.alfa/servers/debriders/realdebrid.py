# -*- coding: utf-8 -*-

import time
import urllib

from core import jsontools
from core import scrapertools
from platformcode import config, logger
from platformcode import platformtools

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0'}


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s' , video_password=%s)" % (page_url, video_password))

    # Se comprueba si existe un token guardado y sino se ejecuta el proceso de autentificación
    token_auth = config.get_setting("token", server="realdebrid")
    if token_auth is None or token_auth == "":
        if config.is_xbmc():
            token_auth = authentication()
            if token_auth == "":
                return [["REAL-DEBRID: No se ha completado el proceso de autentificación", ""]]
        else:
            return [["Es necesario activar la cuenta. Accede al menú de ayuda", ""]]

    post_link = urllib.urlencode([("link", page_url), ("password", video_password)])
    headers["Authorization"] = "Bearer %s" % token_auth
    url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
    data = scrapertools.downloadpage(url, post=post_link, headers=headers.items())
    data = jsontools.load(data)

    # Si el token es erróneo o ha caducado, se solicita uno nuevo
    if "error" in data and data["error"] == "bad_token":
        debrid_id = config.get_setting("id", server="realdebrid")
        secret = config.get_setting("secret", server="realdebrid")
        refresh = config.get_setting("refresh", server="realdebrid")

        post_token = urllib.urlencode({"client_id": debrid_id, "client_secret": secret, "code": refresh,
                                       "grant_type": "http://oauth.net/grant_type/device/1.0"})
        renew_token = scrapertools.downloadpage("https://api.real-debrid.com/oauth/v2/token", post=post_token,
                                                headers=headers.items())
        renew_token = jsontools.load(renew_token)
        if not "error" in renew_token:
            token_auth = renew_token["access_token"]
            config.set_setting("token", token_auth, server="realdebrid")
            headers["Authorization"] = "Bearer %s" % token_auth
            data = scrapertools.downloadpage(url, post=post_link, headers=headers.items())
            data = jsontools.load(data)

    if "download" in data:
        return get_enlaces(data)
    else:
        if "error" in data:
            msg = data["error"].decode("utf-8", "ignore")
            msg = msg.replace("hoster_unavailable", "Servidor no disponible") \
                .replace("unavailable_file", "Archivo no disponible") \
                .replace("hoster_not_free", "Servidor no gratuito") \
                .replace("bad_token", "Error en el token")
            return [["REAL-DEBRID: " + msg, ""]]
        else:
            return [["REAL-DEBRID: No se ha generado ningún enlace", ""]]


def get_enlaces(data):
    itemlist = []
    if "alternative" in data:
        for link in data["alternative"]:
            video_url = link["download"].encode("utf-8")
            title = video_url.rsplit(".", 1)[1]
            if "quality" in link:
                title += " (" + link["quality"] + ") [realdebrid]"
            itemlist.append([title, video_url])
    else:
        video_url = data["download"].encode("utf-8")
        title = video_url.rsplit(".", 1)[1] + " [realdebrid]"
        itemlist.append([title, video_url])

    return itemlist


def authentication():
    logger.info()
    try:
        client_id = "YTWNFBIJEEBP6"

        # Se solicita url y código de verificación para conceder permiso a la app
        url = "http://api.real-debrid.com/oauth/v2/device/code?client_id=%s&new_credentials=yes" % (client_id)
        data = scrapertools.downloadpage(url, headers=headers.items())
        data = jsontools.load(data)
        verify_url = data["verification_url"]
        user_code = data["user_code"]
        device_code = data["device_code"]
        intervalo = data["interval"]

        dialog_auth = platformtools.dialog_progress(config.get_localized_string(70414),
                                                    config.get_localized_string(60252) % verify_url,
                                                    config.get_localized_string(70413) % user_code,
                                                    config.get_localized_string(60254))

        # Generalmente cada 5 segundos se intenta comprobar si el usuario ha introducido el código
        while True:
            time.sleep(intervalo)
            try:
                if dialog_auth.iscanceled():
                    return ""

                url = "https://api.real-debrid.com/oauth/v2/device/credentials?client_id=%s&code=%s" \
                      % (client_id, device_code)
                data = scrapertools.downloadpage(url, headers=headers.items())
                data = jsontools.load(data)
                if "client_secret" in data:
                    # Código introducido, salimos del bucle
                    break
            except:
                pass

        try:
            dialog_auth.close()
        except:
            pass

        debrid_id = data["client_id"]
        secret = data["client_secret"]

        # Se solicita el token de acceso y el de actualización para cuando el primero caduque
        post = urllib.urlencode({"client_id": debrid_id, "client_secret": secret, "code": device_code,
                                 "grant_type": "http://oauth.net/grant_type/device/1.0"})
        data = scrapertools.downloadpage("https://api.real-debrid.com/oauth/v2/token", post=post,
                                         headers=headers.items())
        data = jsontools.load(data)

        token = data["access_token"]
        refresh = data["refresh_token"]

        config.set_setting("id", debrid_id, server="realdebrid")
        config.set_setting("secret", secret, server="realdebrid")
        config.set_setting("token", token, server="realdebrid")
        config.set_setting("refresh", refresh, server="realdebrid")

        return token
    except:
        import traceback
        logger.error(traceback.format_exc())
        return ""
