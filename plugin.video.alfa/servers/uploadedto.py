# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    real_url = page_url.replace("uploaded.to", "uploaded.net")
    # Vídeo borrado: uploaded.to/file/q4rkg1rw -> Redirige a otra página uploaded.to/410/q4rkg1rw
    # Video erróneo: uploaded.to/file/q4rkg1rx -> Redirige a otra página uploaded.to/404
    location = httptools.downloadpage(real_url, follow_redirects=False, only_headers=True).headers.get("location", "")
    logger.info("location=" + location)
    if location:
        return True, ""
    elif "uploaded.net/410" in location:
        return False, "El archivo ya no está disponible<br/>en uploaded.to (ha sido borrado)"
    elif "uploaded.net/404" in location:
        return False, "El archivo no existe<br/>en uploaded.to (enlace no válido)"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    if premium:
        # Login para conseguir la cookie
        logger.info("-------------------------------------------")
        logger.info("login")
        logger.info("-------------------------------------------")
        login_url = "http://uploaded.net/io/login"
        post = "id=" + user + "&pw=" + password
        headers = []
        headers.append(["X-Requested-With", "XMLHttpRequest"])
        headers.append(["X-Prototype-Version", "1.6.1"])
        headers.append(["Referer", "http://uploaded.to/"])

        setcookie = httptools.downloadpage(login_url, post=post, headers=headers, follow_redirects=False,
                                           only_headers=True).headers.get("set-cookie", "")

        logger.info("-------------------------------------------")
        logger.info("obtiene la url")
        logger.info("-------------------------------------------")

        location = httptools.downloadpage(page_url, follow_redirects=False, only_headers=True).headers.get("location",
                                                                                                           "")
        logger.info("location=" + location)
        # Set-Cookie3: auth=3315964ab4fac585fdd9d4228dc70264a1756ba; path="/"; domain=".uploaded.to"; path_spec; domain_dot; expires="2015-02-25 18:35:37Z"; version=0
        # Set-Cookie3: login="%26id%3D3315964%26pw%3Dde135af0befa087e897ee6bfa78f2511a1ed093f%26cks%3D854cca559368"; path="/"; domain=".uploaded.to"; path_spec; domain_dot; expires="2013-02-25 18:35:37Z"; version=0

        logger.info("-------------------------------------------")
        logger.info("obtiene el nombre del fichero")
        logger.info("-------------------------------------------")
        try:
            # content-disposition=attachment; filename="El Hobbit CAM LATINO Barbie.avi"
            content_disposition = httptools.downloadpage(location, headers=headers, follow_redirects=False,
                                                         only_headers=True).headers.get("content-disposition", "")
            logger.info("content_disposition=" + repr(content_disposition))
            if content_disposition != "":
                filename = scrapertools.find_single_match(content_disposition, 'filename="([^"]+)"')
                extension = filename[-4:]
            else:
                extension = ""

        except:
            import traceback
            logger.error(traceback.format_exc())
            extension = ""

        video_urls.append([extension + " (Premium) [uploaded.to]", location])

    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls
