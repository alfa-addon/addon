# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vidnest (canal vitamina_mio, funcion vidnest()).
#
# El canal ya entrega el master HLS del proveedor (Lamda/Beta/Alfa/Prime) y, cuando hace
# falta, su sufijo |Referer=... (Prime lo exige; sin el, 403).
#
# Aqui no hay nada que resolver: el conector existe para que Alfa elija
# inputstream.adaptive (lo fuerza servers/vidnest.json) y mande las cabeceras del sufijo
# al manifiesto y a los segmentos. Sin el, Kodi intentaria abrir el HLS con su demuxer
# nativo y fallaria con "error probing input format".
# --------------------------------------------------------

from platformcode import logger


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    return [["[vidnest] HLS", page_url]]
