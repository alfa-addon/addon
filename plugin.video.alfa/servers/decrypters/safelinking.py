# -*- coding: utf-8 -*-

from core import httptools
from platformcode import logger


def get_long_url(short_url):
    logger.info("(short_url='%s')" % short_url)

    location = httptools.get_header_from_response(short_url, header_to_get="location")
    logger.info("location=" + location)

    return location
