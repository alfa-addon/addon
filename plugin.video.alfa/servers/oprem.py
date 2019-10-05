# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Oprem By Alfa development Group
# --------------------------------------------------------

import os
from core import httptools
from platformcode import logger, config

# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url).data
    data = data.replace('s://lh3.googleusercontent.com', '://localhost:8781')
    
    
    m3u8 = os.path.join(config.get_data_path(), "op_master.m3u8")
    outfile = open(m3u8, 'wb')
    outfile.write(data)
    outfile.close()
    page_url = m3u8
    from lib import servop
    servop.start()

    video_urls = [["%s [Oprem]" % page_url[-4:], page_url]]

    return video_urls
