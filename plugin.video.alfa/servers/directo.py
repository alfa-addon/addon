# -*- coding: utf-8 -*-

from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    
    if page_url:
        return True, ""
    else:
        return False, "No se ha encontrado un enlace. " \
                      "Posiblemente sea un servidor no soportado.\n\n" \
                      "Puedes reportarlo en el foro https://alfa-addon.com"

# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    video_urls = [["%s [directo]" % page_url[-4:], page_url]]

    return video_urls
