# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Ringraziamo Icarus crew
# Canale per dragonballforever
# ------------------------------------------------------------
import re
from platformcode import logger
from core import httptools
from core import scrapertools
from core.item import Item



host = "https://www.dragonballforever.it"


# ----------------------------------------------------------------------------------------------------------------
def mainlist(item):
    logger.info()
    itemlist = [Item(channel=item.channel,
                     action="episodi",
                     title=color("Dragon Ball Kai", "azure"),
                     url="%s/dragon-ball-kai-episodi/" % host,
                     extra="Kai",
                     show="Dragon Ball Kai",
                     thumbnail="https://www.dragonballforever.it/wp-content/uploads/2016/11/dragonball_kai_cover.jpg"),
                Item(channel=item.channel,
                     title=color("Dragon Ball Super", "azure"),
                     action="episodi",
                     url="%s/dragon-ball-super/" % host,
                     extra="Super",
                     show="Dragon Ball Super",
                     thumbnail="https://www.dragonballforever.it/wp-content/uploads/2016/11/dbsuper-locandina.jpg")]

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def episodi(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<a href="([^"]+)"[^>]+><strong>(Dragon Ball %s [^<]+)</strong></a>' % item.extra
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = color(scrapertools.decodeHtmlentities(scrapedtitle).replace('Dragon Ball %s episodio Streaming ' % item.extra, '').replace('#', '').strip(), 'azure')
        epnumber = scrapertools.find_single_match(scrapedtitle, r'\d+')
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=re.sub(r'\d+', 'Episodio: %s' % color(epnumber, 'red'), scrapedtitle),
                 fulltitle="Dragon Ball %s Episodio: %s" % (item.extra, scrapedtitle),
                 url=scrapedurl,
                 extra=item.extra,
                 show=item.show,
                 thumbnail=item.thumbnail,
                 folder=True))

    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if 'Super' in item.extra:
        item.url = host + "/strm/dbsuper/%s" % scrapertools.find_single_match(data, r'file:\s*"\.\./([^"]+)"')
    elif 'Kai' in item.extra:
        item.url = scrapertools.find_single_match(data, r'flashvars=[\'|\"]+(?:file=|)([^&]+)&')

    itemlist.append(
        Item(channel=item.channel,
            action="play",
            title="%s [.%s]" % (color(item.show, 'azure'), color(item.url.split('.')[-1], 'orange')),
            fulltitle=color(item.fulltitle, 'orange') if 'Super' in item.extra else color(item.fulltitle, 'deepskyblue'),
            url=item.url,
            show=item.show,
            extra=item.extra,
            thumbnail=item.thumbnail))
    return itemlist

# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def color(text, color):
    return "[COLOR "+color+"]"+text+"[/COLOR]"

# ================================================================================================================
