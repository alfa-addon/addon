# -*- coding: utf-8 -*-
# -*- Channel CheemsPorn -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; _dict = dict

from lib import AlfaChannelHelper
if not PY3: _dict = dict; from AlfaChannelHelper import dict
from AlfaChannelHelper import DictionaryAdultChannel
from AlfaChannelHelper import re, traceback, time, base64, xbmcgui
from AlfaChannelHelper import Item, servertools, scrapertools, jsontools, get_thumb, config, logger, filtertools, autoplay

IDIOMAS = AlfaChannelHelper.IDIOMAS_A
list_language = list(set(IDIOMAS.values()))
list_quality_movies = AlfaChannelHelper.LIST_QUALITY_MOVIES_A
list_quality_tvshow = []
list_quality = list_quality_movies + list_quality_tvshow
list_servers = AlfaChannelHelper.LIST_SERVERS_A

forced_proxy_opt = 'ProxySSL'

# https://cheemsporn.com/  https://cheemsporno.com/
# faltan filtrar las entradas de cheemsporno.

canonical = {
             'channel': 'cheemsporn', 
             'host': config.get_setting("current_host", 'cheemsporn', default=''), 
             'host_alt': ["https://cheemsporn.com/"], 
             'host_black_list': ["https://cheemsporno.com/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': forced_proxy_opt, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}
debug = config.get_setting('debug_report', default=False)
movie_path = ''
tv_path = ''
language = []
url_replace = []


finds = {'find': dict([('find', [{'tag': ['div', 'section'], 'id': ['primary']}]),
                       ('find_all', [{'tag': ['article'], 'class': re.compile(r"^post-\d+")}])]),
         'categories': dict([('find', [{'tag': ['div'], 'id': ['primary']}]),
                             ('find_all', [{'tag': ['article'], 'class': re.compile(r"^post-\d+")}])]), 
         'search': {}, 
         'get_quality': {}, 
         'get_quality_rgx': '', 
         'next_page': {}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': dict([('find', [{'tag': ['div'], 'class': ['pagination']}]), 
                            ('find_all', [{'tag': ['a'], '@POS': [-1],
                            '@ARG': 'href', '@TEXT': '\/page\/(\d+)'}])]), 
         'plot': {}, 
         'findvideos': {'find_all': [{'tag': ['option'], '@ARG': 'value'}]}, 
         'title_clean': [['[\(|\[]\s*[\)|\]]', ''],['(?i)\s*videos*\s*', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'url_replace': [], 
         'profile_labels': {
                            # 'list_all_stime': dict([('find', [{'tag': ['div', 'span'], 'class': ['dur']}]),
                                                    # ('get_text', [{'strip': True}])]),
                            'list_all_quality': dict([('find', [{'tag': ['div', 'span'], 'class': ['hd-video']}]),
                                                      ('get_text', [{'strip': True}])]),
                           },
         'controls': {'url_base64': False, 'cnt_tot': 24, 'reverse': False, 'profile': 'default'}, 
         'timeout': timeout}
AlfaChannel = DictionaryAdultChannel(host, movie_path=movie_path, tv_path=tv_path, movie_action='play', canonical=canonical, finds=finds, 
                                     idiomas=IDIOMAS, language=language, list_language=list_language, list_servers=list_servers, 
                                     list_quality_movies=list_quality_movies, list_quality_tvshow=list_quality_tvshow, 
                                     channel=canonical['channel'], actualizar_titulos=True, url_replace=url_replace, debug=debug)


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Nuevos", action="list_all", url=host + "page/1?filter=latest"))
    itemlist.append(Item(channel=item.channel, title="Más visto", action="list_all", url=host + "?filter=most-viewed"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado", action="list_all", url=host + "?filter=popular"))
    itemlist.append(Item(channel=item.channel, title="Mas largo", action="list_all", url=host + "?filter=longest"))
    itemlist.append(Item(channel=item.channel, title="Pornstars", action="section", url=host + "actors/page/1", extra="PornStar"))
    itemlist.append(Item(channel=item.channel, title="Categorias", action="section", url=host + "categories", extra="Categorias"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def section(item):
    logger.info()
    
    return AlfaChannel.section(item, **kwargs)


def list_all(item):
    logger.info()
    
    findS = finds.copy()
    findS['controls']['action'] = 'findvideos'
    
    return AlfaChannel.list_all(item, finds=findS, **kwargs)
    # return AlfaChannel.list_all(item, **kwargs)


def findvideos(item):
    logger.info()
    
    # return AlfaChannel.get_video_options(item, item.url, data='', matches_post=None, 
                                         # verify_links=False, findvideos_proc=True, **kwargs)
    return AlfaChannel.get_video_options(item, item.url, matches_post=findvideos_matches, 
                                         verify_links=False, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, **AHkwargs):
    logger.info()
    
    matches = []
    findS = AHkwargs.get('finds', finds)
    srv_ids = {"dood": "Doodstream",
               "Streamtape": "Streamtape ",
               "sbthe": "Streamsb",
               "VOE": "voe",
               "mixdrop.co": "Mixdrop",
               "Upstream": "Upstream"}
    logger.debug(matches_int)
    for elem in matches_int:
        elem_json = {}
        #logger.error(elem)

        try:
            if not elem:
                soup = AHkwargs.get('soup', {})
                matches = soup.find('script', id="__NEXT_DATA__")
                logger.debug(matches)
            elem_json['url'] = elem
            # if isinstance(elem, str):
                # elem_json['url'] = elem
                # if elem_json['url'].endswith('.jpg'): continue
            # else:
                # elem_json['url'] = elem.get("href", "") or elem.get("src", "")
            # if AlfaChannel.obtain_domain(elem_json['url']):
                # elem_json['server'] = AlfaChannel.obtain_domain(elem_json['url']).split('.')[-2]
            # else: 
                # elem_json['server'] = "dutrag"  ### Quitar los watch/YnqAKRJybm2PJ  aparecen en movies
            # if elem_json['server'] in ["Netu", "trailer", "k2s", "dutrag"]: continue
            # if elem_json['server'] in srv_ids:
                # elem_json['server'] = srv_ids[elem_json['server']]
            elem_json['language'] = ''

        except:
            logger.error(elem)
            logger.error(traceback.format_exc())

        if not elem_json.get('url', ''): continue

        matches.append(elem_json.copy())

    return matches, langs


# <option downloadurl="https://vidhidevip.com/d/ke29rsh4s6in" value="https://vidhidevip.com/v/ke29rsh4s6in">Filelions</option>
# <option downloadurl="" value="https://luluvdo.com/e/4ev6spnqj1k1">Lulu</option></select> 
# sources: [{file:

# <option downloadurl="" value="https://moonembed.xyz/e/c103ktbuw5s2">Filemoon</option>
# <option downloadurl="" value="https://wolfstream.tv/embed-m1axecpyfv9f.html">Wolfstream</option>
# <option downloadurl="https://vtube.to/lbi0jd1n6lmg.html" value="https://vtube.to/embed-lbi0jd1n6lmg.html">Vtube</option>
# <option downloadurl="https://voe.sx/7t6rngglluyl" value="https://voe.sx/e/7t6rngglluyl">Voe</option>
# <option downloadurl="https://ds2play.com/d/voh31bcapcfg" value="https://ds2play.com/e/voh31bcapcfg">Doodstream</option>

# <div class="video-data"> <div class="download-buttons"> <div class="action-title"> Descargas </div> 
# <button class="btn download-button"> <a class="download-link" href="https://katfile.com/b6syzhyohekv" target="_blank"> <i class="fa fa-download"></i> Descargar Katfile </a> </button>
# <button class="btn download-button"> <a class="download-link" href="https://vtube.to/lbi0jd1n6lmg.html" target="_blank"> <i class="fa fa-download"></i> Descargar Vtube </a> </button>
# <button class="btn download-button"> <a class="download-link" href="https://voe.sx/7t6rngglluyl" target="_blank"> <i class="fa fa-download"></i> Descargar Voe </a> </button>
# <button class="btn download-button"> <a class="download-link" href="https://vidhidevip.com/d/ke29rsh4s6in" target="_blank"> <i class="fa fa-download"></i> Descargar Filelions </a> </button>
# <button class="btn download-button"> <a class="download-link" href="https://ds2play.com/d/voh31bcapcfg" target="_blank"> <i class="fa fa-download"></i> Descargar Doodstream </a> </button>
# <button class="btn download-button"> <a class="download-link" href="https://1fichier.com/?x4xiy2kf1tq5x9xr4r5e&amp;af=5030723" target="_blank"


# <script id="__NEXT_DATA__" type="application/json">
# {"props":
         # {"pageProps":
                      # {"post":
                             # {"id":"daefb1d5-0252-4b79-b8cc-02e5e79a69d9",
                              # "slug":"jacquie-et-michel-tv-18-years-old-student-in-brest-",
                              # "actors":[],
                              # "video":{"poster":"https://t96.pixhost.to/thumbs/347/477844074_jacquie-et-michel-tv-18-years-old-student-in-brest.jpg","qualities":[],"download":""},
                              # "tags":[{"name":"Europea","id":"0da9d785-a42e-47d7-b186-9b3dd8f38f49","slug":"european"},{"name":"Peludo","id":"14ac63c0-b58a-45c6-9b9c-5569b6446e89","slug":"hairy"},{"name":"Mamadas","id":"29335d65-e79a-4409-bb88-17d4c9252b90","slug":"blowjobs"},{"name":"Culazo","id":"331e776f-ca54-4e95-9190-a9c6aa133ecc","slug":"big-butt"},{"name":"Delgadas","id":"5aa9dcec-e298-4c1f-a7cf-259140aa20a0","slug":"thin"},{"name":"Tatuajes","id":"6372ea91-0e6e-4da2-a653-697e3eb88e76","slug":"tattooed"},{"name":"Facial","id":"6ad780d6-be75-451f-9b30-b4e9a8c430ca","slug":"facial"},{"name":"Asiática","id":"73c4afd2-3f03-4128-8c89-e29e0a411d3f","slug":"asian"},{"name":"Atlética","id":"755d0357-f833-4b10-a0e3-a2a0d8c0ae13","slug":"athletic"},{"name":"Amateur","id":"cf15eaa1-f0ff-4ee6-8ce4-c2e8c6b14416","slug":"amateur"},{"name":"Joven","id":"e5318d96-ca32-457d-a4f5-5fce5bbf855d","slug":"teen"},{"name":"Lamiendo coño","id":"fc38895e-ec74-4665-9423-90ffac67b9a0","slug":"pussy-licking"}],
                              # "producer":{"name":"Jacquie Et Michel TV","slug":"jacquie-et-michel-t-v-videos","id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","imageUrl":null,"brandHexColor":""},
                              # "description":"A pesar de su edad y su relativa experiencia en asuntos de sexo, ¡Lemon está listo para asumir un gran desafío! Sin embargo, una estudiante de biología, esta hermosa joven de 18 años de orígenes exóticos, tiene un gran personaje y una gran facilidad para expresar sus deseos. De hecho, resulta que a la joven le gusta divertirse y no lo esconde. Sin embargo, la posibilidad de presentarse a los placeres de la puta filmada constituyó un desafío que le daba mucha emoción, pero en última instancia también mucha ansiedad.. .","formattedPublishedAt":"13 jun 2024",
                              # "publishedAt":"2024-06-13T13:27:13.000+02:00",
                              # "title":"¡18 años, estudiante en Brest!",
                              # "type":"video",
                              # "thumb":"https://t96.pixhost.to/thumbs/347/477844074_jacquie-et-michel-tv-18-years-old-student-in-brest.jpg",
                              # "duration":"1858.88",
                              # "actor":null,"postMediaVideoType":[],"postMediaImageType":[],
                              # "postMediaEmbedType":[{"id":"1bf45eee-c303-4079-b95c-690ac2e5e1a1","postId":"daefb1d5-0252-4b79-b8cc-02e5e79a69d9","type":"Embed","title":"","thumbnailUrl":"https://t96.pixhost.to/thumbs/347/477844074_jacquie-et-michel-tv-18-years-old-student-in-brest.jpg",
                                                     # "urls":[{"title":"Doodstream","url":"https://ds2play.com/e/tj29mincf7ua","type":"access-url","provider":{"id":"baa39748-8402-4378-b296-3ca653e97f9a","logoUrl":"https://cdn.cheemsporn.com/static/doodstream-logo.png","name":"Doodstream"}},
                                                             # {"title":"Wolfstream","url":"https://wolfstream.tv/embed-im8de8q7zlyn.html","type":"access-url","provider":{"id":"2fef1a77-a1f8-42a3-9293-437a6f4fc5cc","logoUrl":"https://cdn.cheemsporn.com/static/wolfstream-logo.png","name":"Wolfstream"}}],
                                                     # "downloadUrls":[{"title":"1Fichier","url":"https://1fichier.com/?zh2z9lt09qrqxcoctr9g\u0026af=5030723","type":"download-url","provider":{"id":"3810a3c5-e4d1-4c99-bee0-7b611aafc89b","logoUrl":"https://cdn.cheemsporn.com/static/1fichier-logo.png","name":"1Fichier"}},
                                                                     # {"title":"Media.cm","url":"https://media.cm/z3idjci3a53j","type":"download-url","provider":{"id":"bdeaa99d-1263-4195-9244-b29c1839e5a8","logoUrl":"https://cdn.cheemsporn.com/static/media-logo.png","name":"Media.cm"}},
                                                                     # {"title":"Vtube","url":"https://vtube.to/owtc5us2vcne.html","type":"download-url","provider":{"id":"6a594991-7364-481d-85f1-62c5ba2b6cb3","logoUrl":"https://cdn.cheemsporn.com/static/vtube-logo.png","name":"Vtube"}}]}
                                                   # ]
                              # },
                              # "relatedPosts":[{"id":"04607a47-de38-4cd7-af7d-d9eeadbf386e","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquieetmicheltv-videoswhen-it-comes-to-sex-joy-is-no-fool.mp4","type":"cheemsporn.com/trailer-jacquieetmicheltv-videoswhen-it-comes-to-sex-joy-is-no-fool.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquieetmicheltv-videoswhen-it-comes-to-sex-joy-is-no-fool.jpg","title":"Cuando se trata de sexo, Joy no es ninguna tonta.","views":963,"duration":"31:03","slug":"jacquieetmicheltv-videoswhen-it-comes-to-sex-joy-is-no-fool","actor":null,"externalLink":null},{"id":"06d0895b-990b-49d0-8b55-e12016f25055","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tv20-years-old-is-waiting-for-her-suitors.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tv20-years-old-is-waiting-for-her-suitors.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://thumbs2.imgbox.com/0a/c6/Ow5vw5L4_t.jpg","title":"¡20 años, está esperando a sus pretendientes!","views":2316,"duration":"28:27","slug":"jacquie-et-michel-tv20-years-old-is-waiting-for-her-suitors","actor":null,"externalLink":null},{"id":"06e7734c-2442-4bc9-aea3-cb4240d72753","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvlaurys-fabulous-ass-is-perfectly-inaugurated.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvlaurys-fabulous-ass-is-perfectly-inaugurated.mp4"},"date":"hace 9 días","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t96.pixhost.to/thumbs/156/475081554_jacquie-et-michel-tvlaurys-fabulous-ass-is-perfectly-inaugurated.jpg","title":"¡El fabuloso culo de Laury está perfectamente inaugurado!","views":1931,"duration":"33:23","slug":"jacquie-et-michel-tvlaurys-fabulous-ass-is-perfectly-inaugurated","actor":null,"externalLink":null},{"id":"07a528bc-5e04-4a57-9143-d8b043ee7124","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvno-more-perversion-for-amandine-28-years-old.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvno-more-perversion-for-amandine-28-years-old.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/541/466123469_jacquie-et-michel-tvno-more-perversion-for-amandine-28-years-old.jpg","title":"No más perversión para Amandine, 28 años.. .","views":1398,"duration":"30:19","slug":"jacquie-et-michel-tvno-more-perversion-for-amandine-28-years-old","actor":null,"externalLink":null},{"id":"0900aac9-a0d8-4e54-ab5e-feea06b674a0","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvalicia-lets-herself-be-carried-away-by-an-electrifying-threesome.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvalicia-lets-herself-be-carried-away-by-an-electrifying-threesome.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/1022/471851607_jacquie-et-michel-tvalicia-lets-herself-be-carried-away-by-an-electrifying-three.jpg","title":"¡Alicia se deja llevar por un trío electrizante!","views":1288,"duration":"39:11","slug":"jacquie-et-michel-tvalicia-lets-herself-be-carried-away-by-an-electrifying-threesome","actor":null,"externalLink":null},{"id":"1082fdb0-4954-4b81-863a-a3b63350e54a","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvalicia-32-years-old-takes-the-direction-of-the-hardcore.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvalicia-32-years-old-takes-the-direction-of-the-hardcore.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/879/470025265_jacquie-et-michel-tvalicia-32-years-old-takes-the-direction-of-the-hardcore.jpg","title":"¡Alicia, de 32 años, toma la dirección del hardcore!","views":589,"duration":"38:01","slug":"jacquie-et-michel-tvalicia-32-years-old-takes-the-direction-of-the-hardcore","actor":null,"externalLink":null},{"id":"112df118-f690-4468-81f2-411b4f047435","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquieetmicheltv-videoscindy-lopes-a-new-hard-treat.mp4","type":"cheemsporn.com/trailer-jacquieetmicheltv-videoscindy-lopes-a-new-hard-treat.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquieetmicheltv-videoscindy-lopes-a-new-hard-treat.jpg","title":"Cindy Lopes, ¡una nueva golosina dura!","views":526,"duration":"19:25","slug":"jacquieetmicheltv-videoscindy-lopes-a-new-hard-treat","actor":null,"externalLink":null},{"id":"165a3f00-ebad-4c08-a6c6-049dc4c0bc19","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tv-at-37-ellie-discovers-the-unique-sensations-of-double-vaginal-sex-.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tv-at-37-ellie-discovers-the-unique-sensations-of-double-vaginal-sex-.mp4"},"date":"hace 5 días","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t96.pixhost.to/thumbs/254/476734647_jacquie-et-michel-tv-at-37-ellie-discovers-the-unique-sensations-of-double-vagin.jpg","title":"¡A los 37 años, Ellie descubre las sensaciones únicas del doble sexo vaginal!","views":1233,"duration":"37:28","slug":"jacquie-et-michel-tv-at-37-ellie-discovers-the-unique-sensations-of-double-vaginal-sex-","actor":null,"externalLink":null},{"id":"228a1392-8dc7-4eb1-9a09-e1dfcd56c354","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquieetmicheltv-videosamandine-pellissard-in-an-anthological-sex-scene.mp4","type":"cheemsporn.com/trailer-jacquieetmicheltv-videosamandine-pellissard-in-an-anthological-sex-scene.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquieetmicheltv-videosamandine-pellissard-in-an-anthological-sex-scene.jpg","title":"¡Amandine Pellissard en una escena de sexo antológica!","views":675,"duration":"41:41","slug":"jacquieetmicheltv-videosamandine-pellissard-in-an-anthological-sex-scene","actor":null,"externalLink":null},{"id":"23cfa0bc-6d41-4a75-bf11-6ddf7bdc21cf","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tv26-years-old-naughty-from-argenteuil.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tv26-years-old-naughty-from-argenteuil.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/638/467203298_jacquie-et-michel-tv26-years-old-naughty-from-argenteuil.jpg","title":"¡26 años, travieso de Argenteuil!","views":799,"duration":"44:45","slug":"jacquie-et-michel-tv26-years-old-naughty-from-argenteuil","actor":null,"externalLink":null},{"id":"2583c890-1ea6-47b1-a587-7cf1f171f3e9","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquieetmicheltv-videosnathalie-and-luth-immerse-themselves-in-hard-fucking-at-high-speed.mp4","type":"cheemsporn.com/trailer-jacquieetmicheltv-videosnathalie-and-luth-immerse-themselves-in-hard-fucking-at-high-speed.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquieetmicheltv-videosnathalie-and-luth-immerse-themselves-in-hard-fucking-at-high-speed.jpg","title":"Nathalie y Luth se sumergen en una follada dura a gran velocidad...","views":201,"duration":"56:36","slug":"jacquieetmicheltv-videosnathalie-and-luth-immerse-themselves-in-hard-fucking-at-high-speed","actor":null,"externalLink":null},{"id":"25d80784-6637-4c7d-a8ab-400bcbf668bb","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvkelly-an-outstanding-advisor.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvkelly-an-outstanding-advisor.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/698/467889905_jacquie-et-michel-tvkelly-an-outstanding-advisor.jpg","title":"¡Kelly, una asesora sobresaliente!","views":1041,"duration":"31:48","slug":"jacquie-et-michel-tvkelly-an-outstanding-advisor","actor":null,"externalLink":null},{"id":"2c42d826-b081-4c87-8a17-0254abf4c8f1","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tv-abby-has-found-her-nymphomaniac-alter-ego-.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tv-abby-has-found-her-nymphomaniac-alter-ego-.mp4"},"date":"hace 3 días","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t96.pixhost.to/thumbs/299/477277314_jacquie-et-michel-tv-abby-has-found-her-nymphomaniac-alter-ego.jpg","title":"Abby ha encontrado su alter ego ninfómana...","views":975,"duration":"38:57","slug":"jacquie-et-michel-tv-abby-has-found-her-nymphomaniac-alter-ego-","actor":null,"externalLink":null},{"id":"2db6961d-aa80-4aa1-8296-654f0ff651b3","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvlivia-is-always-persuasive.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvlivia-is-always-persuasive.mp4"},"date":"hace 2 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t94.pixhost.to/thumbs/849/458129905_naughtyblog_cover.jpg","title":"¡Livia siempre es persuasiva!","views":690,"duration":"30:52","slug":"jacquie-et-michel-tvlivia-is-always-persuasive","actor":null,"externalLink":null},{"id":"2e482909-c00a-4315-86a0-594a5c3ec7f6","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvethans-luxurious-vacationpaola-hard.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvethans-luxurious-vacationpaola-hard.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquie-et-michel-tvethans-luxurious-vacationpaola-hard.jpg","title":"Las lujosas vacaciones de Ethan","views":495,"duration":"17:35","slug":"jacquie-et-michel-tvethans-luxurious-vacationpaola-hard","actor":null,"externalLink":null},{"id":"2fb717ad-3862-4d18-8bfa-2dd69057641e","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvlaury-27-years-old-burns-with-hard-desires.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvlaury-27-years-old-burns-with-hard-desires.mp4"},"date":"hace 2 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/43/461240659_jacquie-et-michel-tvlaury-27-years-old-burns-with-hard-desires.jpg","title":"¡Laury, de 27 años, arde con deseos difíciles!","views":729,"duration":"47:25","slug":"jacquie-et-michel-tvlaury-27-years-old-burns-with-hard-desires","actor":null,"externalLink":null},{"id":"3289effb-361e-42ee-b682-091534b55d6d","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvlara-delights-in-a-threesome-bursting-with-lust.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvlara-delights-in-a-threesome-bursting-with-lust.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquie-et-michel-tvlara-delights-in-a-threesome-bursting-with-lust.jpg","title":"¡Lara se deleita en un trío lleno de lujuria!","views":282,"duration":"37:51","slug":"jacquie-et-michel-tvlara-delights-in-a-threesome-bursting-with-lust","actor":null,"externalLink":null},{"id":"337c850d-c00b-4f8d-a778-66fb581381d8","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tv-betty-combines-sapphic-pleasures-and-hard-practices-.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tv-betty-combines-sapphic-pleasures-and-hard-practices-.mp4"},"date":"anteayer","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t96.pixhost.to/thumbs/323/477549479_jacquie-et-michel-tv-betty-combines-sapphic-pleasures-and-hard-practices.jpg","title":"¡Betty combina placeres con zarza y ​​prácticas duras!","views":1940,"duration":"35:50","slug":"jacquie-et-michel-tv-betty-combines-sapphic-pleasures-and-hard-practices-","actor":null,"externalLink":null},{"id":"342cfe6c-2bf4-41e7-a5c8-be0ed25aed18","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquie-et-michel-tvjoys-walk-turns-into-a-tough-one.mp4","type":"cheemsporn.com/trailer-jacquie-et-michel-tvjoys-walk-turns-into-a-tough-one.mp4"},"date":"el mes pasado","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://t95.pixhost.to/thumbs/948/471021126_jacquie-et-michel-tvjoys-walk-turns-into-a-tough-one.jpg","title":"¡La caminata de Joy se vuelve difícil!","views":1059,"duration":"34:22","slug":"jacquie-et-michel-tvjoys-walk-turns-into-a-tough-one","actor":null,"externalLink":null},{"id":"34d569c0-ecd3-4489-b840-4b0de5e39635","animation":{"value":"https://cdn.cheemsporn.com/trailer-jacquieetmicheltv-videoslivia-27-seeks-authenticity.mp4","type":"cheemsporn.com/trailer-jacquieetmicheltv-videoslivia-27-seeks-authenticity.mp4"},"date":"hace 3 meses","producer":{"id":"3b7e9e60-ec53-40a9-987f-30d4ddf95b4f","slug":"jacquie-et-michel-t-v-videos","imageUrl":null,"name":"Jacquie Et Michel TV","brandHexColor":""},"thumb":"https://cdn.cheemsporn.com/img/jacquieetmicheltv-videoslivia-27-seeks-authenticity.jpg","title":"Livia, 27 años, ¡busca autenticidad!","views":1001,"duration":"28:53","slug":"jacquieetmicheltv-videoslivia-27-seeks-authenticity","actor":null,"externalLink":null}],"parsedDuration":"PT1858S","postViewsNumber":2703,"postLikes":0,"postDislikes":0,"postCommentsNumber":0,"postEmbedUrl":"https://cheemsporno.com/es/posts/videos/embed/jacquie-et-michel-tv-18-years-old-student-in-brest-","baseUrl":"https://cheemsporno.com","htmlPageMetaContextProps":{"url":"https://cheemsporno.com/es/posts/videos/jacquie-et-michel-tv-18-years-old-student-in-brest-","locale":"es_ES","alternateLocaleWithTerritory":["en_US"],"alternateLocale":[{"locale":"en","alternateUrl":"https://cheemsporno.com/en/posts/videos/jacquie-et-michel-tv-18-years-old-student-in-brest-"}]},"__lang":"es","__namespaces":{"app_menu":{"action_cannot_be_performed_error_message":"No puedes hacer esto ahora. Espera a que termine la acción actual e inténtalo nuevamente","already_searching_term_error_message":"Ya estás buscando este término","app_menu_loading_user_button_title":"Cargando","app_menu_logo_url_alt":"Cheems","app_menu_menu_button":"Menú","app_menu_search_button_title":"Buscar posts","app_menu_search_menu_placeholder_title":"Buscar posts","app_menu_user_button_title":"Iniciar sesión","empty_search_error_message":"Por favor, introduzca un término válido de búsqueda","language_button_image_alt":"Idioma actual: {{locale}}","language_button_title":"Cambiar idioma de la aplicación","search_bar_contract_title":"Contraer","search_bar_expand_title":"Abrir búsqueda"},"app_banner":{"banner_title":"Cheems: el mejor tube de videos porno","banner_description":"Así que llevas todo el día  buscando los últimos videos porno de las mejores productoras. Has gastado mucho tiempo y cuando al fin encuentras algo descubres que no puedes ver online o descargar el video, o peor aún, que no está en alta definición. En cheemsporno ese será el menor de tus problemas porque tenemos todos los videos porno completos en HD y te ofrecemos varias opciones para verlos online o descargarlos.\n\nQuizás aún no nos conoces, pero ahora que estás en ello, bienvenido a tu nuevo sitio porno favorito. Cientos y miles de videos porno gratis en HD te esperan y esto no ha hecho más que comenzar, el horizonte está lleno de sorpresas. \nVideos porno gratis en HD actualizados a diario. Los últimos lanzamientos de las mejores productas porno aquí en cheemsporno.com\n\nDescargo de responsabilidad: Cheemsporno no almacena ningún contenido en su servidor. Todo el contenido mostrado es almacenado y distribuido por servicios de terceros","rta_logo_alt_title":"RTA: Restringido a adultos","rta_description_title":"Esta web está restringida a adultos. Si estás aquí juras que tienes la edad legal (la edad considerada legal en su país de origen) para consumir contenido para adultos. Aprende como \u003c0\u003ebloquear el acceso a este sitio web\u003c/0\u003e"},"footer":{"app_logo_alt_title":"Cheems","contact_title":"Contáctanos","copyright_title":"© 2024 \u003c0\u003eCheems\u003c/0\u003e Hecho con ❤️ por CP.","english_language_title":"Inglés","facebook_icon_title":"Facebook","spanish_language_title":"Español","telegram_icon_title":"Telegram","tiktok_icon_title":"Tiktok","twitter_icon_title":"X"},"menu":{"dating_advertising_title":"Folla ahora","games_advertising_title":"Juegos porno","ia_advertising_title":"IA","language_menu_already_on_language_error_message":"La aplicacion ya está en este lenguaje","language_menu_english_option_title":"Inglés","language_menu_spanish_option_title":"Español","language_menu_subtitle":"Elige el idioma en el que quieres que se muestre la aplicación","language_menu_title":"Idioma de la aplicación","live_cams_advertising_title":"Webcams","menu_button_title":"Menú","menu_close_button_title":"Contraer menú","menu_following_button_title":"Seguidos","menu_home_button_title":"Inicio","menu_language_button_title":"Idioma","menu_live_cams_button_title":"Cámaras","menu_logo_alt_title":"Cheems","menu_producers_button_title":"Productoras","menu_reacted_button_title":"Reaccionados","menu_saved_button_title":"Guardados","menu_stars_button_title":"Estrellas","menu_tags_button_title":"Etiquetas","menu_trending_button_title":"Tendencias","menu_user_history_button_title":"Historial","the_porn_dude_link_title":"ThePornDude","user_already_on_path":"Ya estás aquí","user_menu_option_not_available_message":"Esta característica estará disponible pronto. ¡Mantente atento!","user_menu_profile_button":"Mi Perfil","user_must_be_authenticated_error_message":"Inicia sesión para acceder a esta característica"},"user_menu":{"user_menu_change_password_button":"Cambiar contraseña","user_menu_profile_button":"Mi perfil","user_sign_out_button":"Cerrar sesión"},"user_login":{"email_input_error_message":"Dirección de correo inválida","email_input_label":"Email","email_input_placeholder":"Email","feature_disable_title":"Esta característica está actualmente deshabilitada porque estamos teniendo problemas técnicos.\nLo habilitaremos muy pronto. ¡Manténte atento!","forgot_password_button_title":"Olvidé mi contraseña","hide_password_button_title":"Ocultar contraseña","login_error_message":"Combinación Email/Contraseña incorrecta","login_information_message":"Serás redirigido a la aplicación seleccionada para completar la operación","login_with_google":"Inicia sesión con Google","password_input_error_message":"Contraseña inválida","password_input_label":"Contraseña","password_input_placeholder":"Contraseña","show_password_button_title":"Mostrar contraseña","sign_in_button_title":"Regístrate aquí","submit_button_title":"Iniciar sesión","subtitle":"Inicia sesión para disfrutar de una experiencia completa en la web\n\nComenta, reacciona, guarda y revisa tu historial de vídeos vistos. ¡Muchas funciones más vienen en camino!","title":"Inicio de sesión"},"error":{"404_error_page_button_title":"Volver al inicio","404_error_page_image_alt":"Página no encontrada","404_error_page_subtitle":"No te preocupes, es solo un 404\nHemos buscado por todos lados pero no hemos podido encontrar la página que solicitas. Si te has perdido puedes regresar a la página principal ","404_error_page_title":"¡Ops, lam pámginam nom sem ham encontramdom!"},"common":{"action_cannot_be_performed_error_message":"No puedes hacer esto ahora, espera a que termine la operación actual","ad_blocker_detected_message_title":"Estás usando un bloqueador de anuncios? Esto puede afectar a tu experiencia en esta web.","banner_ad_title":"Publicidad","cam_card_live_title":"En vivo","cam_card_play_button":"Toca aquí para reproducir el show","cam_card_title":"Mira el show de \u003c0\u003e{{camUsername}}\u003c/0\u003e","cams_carousel_title":"Cámaras en vivo \u003c0\u003e{{camCount}}\u003c/0\u003e","cams_carousel_link_title":"Ver todas","cams_carousel_warning_message":"¿El show no se reproduce? Haz click sobre tu modelo favorito para entrar a su sala","clear_search_button_title":"Limpiar búsqueda","dislike_reaction_active_title_button":"Eliminar reacción","dislike_reaction_title_button":"No me gusta","like_reaction_active_title_button":"Eliminar reacción","like_reaction_title_button":"Me gusta"},"carousel":{"carousel_left_button_title":"Mostrar anteriores","carousel_right_button_title":"Mostrar siguientes"},"post_card_options":{"delete_saved_post_option_title":"Eliminar post guardado","like_post_post_card_gallery_action_title":"Me gusta","post_reaction_added_correctly_message":"¡Gracias por reaccionar!","post_save_post_successfully_removed_from_saved_post":"El post fue eliminado de la lista de videos guardados del usuario","post_save_post_successfully_saved":"El post fue agregado a la lista de videos guardados del usuario","save_post_post_card_gallery_action_title":"Guardar","user_must_be_authenticated_error_message":"Para realizar esta acción necesitas iniciar sesión"},"post_card_gallery":{"post_card_gallery_options_description":"Escoge una opción para el post seleccionado","post_card_gallery_options_title":"Opciones del post","user_must_be_authenticated_error_message":"Para realizar esta acción necesitas iniciar sesión"},"sorting_menu_dropdown":{"dropdown_sort_button_title":"Ordenando por {{criteria}}","dropdown_sort_option_title":"Ordenar por {{criteria}}","latest_entries_option":"Más recientes","less_posts_entries_option":"Menos posts","more_posts_entries_option":"Más posts","most_viewed_entries_option":"Más vistos","name_first_entries_option":"Alfabético a-z","name_last_entries_option":"Alfabético z-a","newest_viewed_posts_option":"Vistos reciente","newest_saved_posts_option":"Guardados reciente","oldest_entries_option":"Más antiguos","oldest_saved_posts_option":"Guardados antiguos","oldest_viewed_posts_option":"Vistos antiguos","popularity_entries_option":"Popularidad"},"post_card":{"post_card_external_link_title":"Link externo","post_card_options_button_title":"Opciones del post","post_card_post_views":"{{views}} vistas"},"pagination_bar":{"error_state_button_title":"Regresar a primera página","error_state_description":"La página que solicitas no existe o fue eliminada\nPara no seguir viendo este error regresa a la primera página","first_page_button_title":"Primera página","last_page_button_title":"Última página","n_page_button_title":"Página {{pageNumber}}","next_page_button_title":"Siguiente página","previous_page_button_title":"Página anterior"},"api_exceptions":{"bad_request_error_message":"Petición inválida","create_post_child_comment_parent_comment_not_found_error_message":"El comentario al que intentas responder no fue encontrado. No es posible responder a un comentario que no existe","create_post_child_comment_post_not_found_error_message":"El post relacionado al comentario al que intentas responder no fue encontrado. No es posible responder a un comentario de un post que no existe","create_post_comment_reaction_post_comment_not_found_error_message":"El comentario al que intentas reaccionar no fue encontrado. No es posible reaccionar a un comentario que no existe","create_post_comment_reaction_user_already_reacted_error_message":"El usuario ya ha reaccionado a este comentario, no es posible volver a reaccionar al comentario","delete_post_comment_does_not_belong_to_user_error_message":"El usuario no puede eliminar el comentario","delete_post_comment_reaction_post_comment_not_found_error_message":"El comentario no fue encontrado. No es posible eliminar una reacción de un comentario que no existe","delete_post_comment_reaction_user_has_not_reacted_error_messaged":"La reacción que intentas eliminar no fue encontrada. No es posible eliminar una reacción que no existe","delete_post_comment_parent_comment_not_found_error_message":"No es posible eliminar la respuesta. La respuesta/comentario no existe","delete_post_comment_post_comment_cannot_be_deleted_error_message":"No es posible eliminar el comentario/respuesta. Inténtelo más tarde nuevamente","delete_post_comment_post_comment_not_found_error_message":"El comentario o respuesta que intentas eliminar no fue encontrado","delete_post_comment_post_not_found_error_message":"El post relacionado al comentario que intentas eliminar no existe. No es posible eliminar un comentario de un post que no existe","post_not_found_error_message":"El post no fue encontrado","post_reaction_does_not_exist_error_message":"El usuario todavía no ha reaccionado al post","post_save_cannot_remove_saved_post_error_message":"No se puede eliminar el post de la lista de posts guardados del usuario","post_save_post_already_on_saved_post_error_message":"El post ya fue guardado por el usuario","post_save_post_does_not_belong_to_user_saved_posts_error_message":"El post no pertenece a la lista de posts guardados del usuario","post_video_no_sources_error_message":"El video no existe o fue eliminado por derechos de autor.\nPuedes reportar el video e intentaremos arreglarlo si es posible","server_error_error_message":"Servicio no disponible. Inténtalo después","something_went_wrong_error_message":"Algo salió mal al intentar realizar la operación. Inténtalo después","user_already_reacted_to_post_error_message":"El usuario ya ha reaccionado a este post","user_forbidden_resource_error_message":"El usuario no tiene acceso al recurso","user_must_be_authenticated_error_message":"Para realizar esta acción necesitas iniciar sesión","user_not_found_error_message":"El usuario que hizo la petición no existe. Cerrando sesión"},"post_page":{"video_related_videos_title":"Vídeos relacionados"},"post":{"action_cannot_be_performed_error_message":"No puedes hacer esto ahora, espera a que termine la operación actual","advertising_section_title":"Publicidad","post_comments_button_title":"Comentarios","post_download_button_title":"Descargar {{sourcesNumber}}","post_download_no_downloads_error_message":"No hay opciones de descarga para este video","post_download_option_alt_title":"Logo de {{providerName}}","post_download_section_description":"Selecciona un servidor para descargar el archivo","post_download_section_title":"Servidores de descarga","post_extra_data_actors_title":"Estrellas","post_extra_data_collaborator_section":"Colaborador","post_extra_data_description_title":"Descripción","post_extra_data_section_show_less":"Ver menos","post_extra_data_section_show_more":"Ver más","post_extra_data_tags_title":"Etiquetas","post_info_button_title":"Más info","post_option_feature_not_available_message":"Esta característica estará disponible pronto. ¡Mantente atento!","post_player_title":"Reproductor del video {{postName}}","post_reaction_added_correctly_message":"¡Gracias por reaccionar!","post_reaction_deleted_correctly_message":"La reacción fue eliminada correctamente","post_report_button_title":"Reportar","post_save_active_button_title":"Guardado","post_save_button_title":"Guardar","post_save_post_successfully_removed_from_saved_post":"El post fue eliminado de la lista de videos guardados del usuario","post_save_post_successfully_saved":"El post fue agregado a la lista de videos guardados del usuario","post_video_no_sources_error_message":"El video no existe o fue eliminado por derechos de autor.\nPuedes reportar el video e intentaremos arreglarlo si es posible.","post_video_player_selector_button_title":"Cambiar fuente del vídeo","post_video_player_sources_menu_subtitle":"Selecciona una opción para reproducir el vídeo","post_video_player_sources_menu_title":"Seleccionar reproductor","post_video_player_sources_option_button_title":"Reproductores","post_views_title":"{{views}} vistas","user_must_be_authenticated_error_message":"Para realizar esta acción necesitas iniciar sesión"},"post_comments":{"action_cannot_be_performed_error_message":"No puedes hacer esto ahora, espera a que termine la operación actual","add_comment_button_title":"Añade tu comentario","add_comment_placeholder":"Escribe tu comentario","add_comment_section_login_button_title":"Iniciar sesión","add_comment_section_login_title":"Inicia sesión para agregar un comentario","back_to_comments_section_button_title":"Volver a los comentarios","close_comment_section_button_title":"Cerrar comentarios","comment_replies_button":"{{replies}} Respuestas","comment_reply_button":"Responder","comment_section_load_more":"Cargar más comentarios","comment_section_title":"Comentarios","delete_comment_option_title":"Eliminar comentario","empty_comment_is_not_allowed_error_message":"Introduce un comentario","post_child_comment_added_success_message":"Respuesta agregada exitosamente","post_comment_added_success_message":"Comentario agregado exitosamente","post_comment_deleted_success_message":"Comentario eliminado exitosamente","post_comment_menu_options_title":"Opciones del comentario","post_comment_reaction_active_button_title":"Me gusta","post_comment_reaction_reaction_added_successfully":"¡Gracias por reaccionar!","post_comment_reaction_reaction_removed_successfully":"Reacción eliminada correctamente","post_comment_reaction_user_already_reacted":"Ya has reaccionado a este comentario","post_comment_reaction_user_has_not_reacted":"Todavía no has reaccionado a este comentario","replies_section_load_more":"Cargar más respuestas","replies_section_title":"Respuestas","user_must_be_authenticated_error_message":"Para realizar esta acción necesitas iniciar sesión"}}},"__N_SSP":true},"page":"/posts/videos/[slug]","query":{"slug":"jacquie-et-michel-tv-18-years-old-student-in-brest-"},"buildId":"szZ1j-vl4ApRKhifI4UL6","isFallback":false,"gssp":true,"locale":"es","locales":["en","es"],"defaultLocale":"en","scriptLoader":[]}</script><script defer src="https://static.cloudflareinsights.com/beacon.min.js/vcd15cbe7772f49c399c6a5babf22c1241717689176015" integrity="sha512-ZpsOmlRQV6y907TI0dKBHq9Md29nnaEIPlkf84rnaERnq6zvWvPUqr2ft8M1aS28oN72PdrCzSjY4U6VaAw1EQ==" data-cf-beacon='{"rayId":"89397f703fcd6683","r":1,"version":"2024.4.1","token":"da3764c5cc3b4e8e8e4e741db793c161"}' crossorigin="anonymous"></script>
# </body></html>

# def play(item):
    # logger.info()
    
    # itemlist = []
    
    # soup = AlfaChannel.create_soup(item.url, **kwargs)
    # if soup.find('div', id='video-actors'):
        # pornstars = soup.find('div', id='video-actors').find_all('a')
        
        # for x, value in enumerate(pornstars):
            # pornstars[x] = value.get_text(strip=True)
        
        # pornstar = ' & '.join(pornstars)
        # pornstar = AlfaChannel.unify_custom('', item, {'play': pornstar})
        # lista = item.contentTitle.split('[/COLOR]')
        # pornstar = pornstar.replace('[/COLOR]', '')
        # pornstar = ' %s' %pornstar
        # if "HD" in item.contentTitle:
            # lista.insert (2, pornstar)
        # else:
            # lista.insert (1, pornstar)
        # item.contentTitle = '[/COLOR]'.join(lista)
    # logger.debug(soup.find('div', class_='video-player'))
    # if soup.find('div', class_='responsive-player') and soup.find('div', class_='responsive-player').iframe:
        # item.url = soup.find('div', class_='responsive-player').iframe['src']
    # itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.contentTitle, url=item.url))
    # itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    # return itemlist


def search(item, texto, **AHkwargs):
    logger.info()
    kwargs.update(AHkwargs)
    
    item.url = "%s?s=%s&filter=latest" % (host, texto.replace(" ", "+"))
    
    try:
        if texto:
            item.c_type = "search"
            item.texto = texto
            return list_all(item)
        else:
            return []
    
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
