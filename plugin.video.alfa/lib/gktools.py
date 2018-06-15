# -*- coding: utf-8 -*-

'''
Características "GK" :
- Utiliza una cookie __cfduid
- Utiliza meta name="google-site-verification" como texto a encriptar
- La clave para encriptar se calcula en los js
- Se calcula un token criptográfico en función del texto y clave

A partir de aquí 2 opciones:

a) Si la url indica que hay un /embed/
    - se cambia /embed/ por /stream/ y se añade /token
    - se descarga la página, dónde se pueden extraer los videos
    
b) Sino (enlaces directos)
    - se busca un identificador
        - si hay una llamada a Play() en el js, el id se saca de allí
        - sino el id puede estar en la url
    - con el identificador y el token se llama a un php (gkpluginsphp, gkpedia)
    - el php devuelve la lista de enlaces a los videos

Notas:
- Creado a partir de lo visto en pelispedia y animeyt, que utilizan este sistema.
- Para otros canales habrá que añadir sus datos en las funciones calcular_*
  o hacer que estas funciones puedan extraer lo necesario de los js.

'''

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import urlparse
from core import httptools
from core import scrapertools
# ~ from platformcode import logger

def gk_play(item):

    itemlist = []

    # Descargar para tratar header y data por separado
    # ------------------------------------------------
    headers = {'Referer': item.referer}
    resp = httptools.downloadpage(item.url, headers=headers, cookies=False)
    # ~ with open('gk_play1.html', 'w') as f: f.write(resp.data); f.close()

    # Obtener cookie __cfduid
    # -----------------------
    for h in resp.headers:
        ck = scrapertools.find_single_match(resp.headers[h], '__cfduid=([^;]*)')
        if ck:
            break
    if not ck: return itemlist

    # Extraer datos y calcular token
    # ------------------------------
    gsv = scrapertools.find_single_match(resp.data, '<meta name="google-site-verification" content="([^"]*)"')
    if not gsv: return itemlist

    suto = calcular_sutorimux(item.url)  # valor que se calcula en función del dominio
    sufijo = calcular_sufijo(item.url)   # valor predeterminado que se establece en el código js

    token = generar_token(gsv, suto+'yt'+suto+sufijo)


    # Descargar y extraer videos
    # --------------------------

    if '/embed/' in item.url:
        url = item.url.replace('/embed/', '/stream/') + '/' + token
        headers = {'Referer': item.url, 'Cookie': '__cfduid=' + ck}
        data = httptools.downloadpage(url, headers=headers, cookies=False).data
        # ~ with open('gk_play2.html', 'w') as f: f.write(resp.data); f.close()
        
        # Extraer enlaces de la respuesta
        # -------------------------------
        url = scrapertools.find_single_match(data, '<meta (?:name|property)="og:url" content="([^"]+)"')
        srv = scrapertools.find_single_match(data, '<meta (?:name|property)="og:sitename" content="([^"]+)"')
        if srv == '' and 'rapidvideo.com/' in url: srv = 'rapidvideo'

        if url != '' and srv != '':
            itemlist.append(item.clone(url=url, server=srv.lower()))

        elif '<title>Vidoza</title>' in data or '|fastplay|' in data:
            if '|fastplay|' in data:
                packed = scrapertools.find_single_match(data, "<script type='text/javascript'>(eval\(.*?)</script>")
                from lib import jsunpack
                data = jsunpack.unpack(packed)
                data = data.replace("\\'", "'")

            matches = scrapertools.find_multiple_matches(data, 'file\s*:\s*"([^"]+)"\s*,\s*label\s*:\s*"([^"]+)"')
            subtitle = ''
            for fil, lbl in matches:
                if fil.endswith('.srt') and not fil.endswith('empty.srt'):
                    subtitle = fil
                    if not subtitle.startswith('http'):
                        domi = scrapertools.find_single_match(data, 'aboutlink\s*:\s*"([^"]*)')
                        subtitle = domi + subtitle
                    break

            for fil, lbl in matches:
                if not fil.endswith('.srt'):
                    itemlist.append([lbl, fil, 0, subtitle])


    else:
        playparms = scrapertools.find_single_match(resp.data, 'Play\("([^"]*)","([^"]*)","([^"]*)"')
        if playparms:
            link = playparms[0]
            subtitle = '' if playparms[1] == '' or playparms[2] == '' else playparms[2] + playparms[1] + '.srt'
        else:
            subtitle = ''
            link = scrapertools.find_single_match(resp.data, 'Play\("([^"]*)"')
            if not link:
                link = scrapertools.find_single_match(item.url, 'id=([^;]*)')

        if link:
            # ~ logger.info('%s %s %s' % (item.url, link, token))
            url_gk = calcular_url_gk(item.url)

            post = "link=%s&token=%s" % (link, token)
            headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': '__cfduid=' + ck}

            data = httptools.downloadpage(url_gk, post=post, headers=headers, cookies=False).data
            # ~ with open('gk_play3.html', 'w') as f: f.write(resp.data); f.close()

            # Extraer enlaces de la respuesta
            # -------------------------------
            matches = scrapertools.find_multiple_matches(data, '"link"\s*:\s*"([^"]*)"\s*,\s*"label"\s*:\s*"([^"]*)"\s*,\s*"type"\s*:\s*"([^"]*)"')
            if matches:
                for url, lbl, typ in matches:
                    itemlist.append(['[%s][%s]' % (typ, lbl), corregir_url(url, item.referer), 0, subtitle])
            else:
                url = scrapertools.find_single_match(data, '"link"\s*:\s*"([^"]*)"')
                if url:
                    itemlist.append(['.mp4', corregir_url(url, item.referer), 0, subtitle])


    return itemlist


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Correcciones en las urls finales obtenidas
# ------------------------------------------
def corregir_url(url, referer):
    url = url.replace('\/', '/')
    if 'chomikuj.pl/' in url: url += "|Referer=%s" % referer
    return url


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Generar un token válido a partir de un texto y una clave
# --------------------------------------------------------

# gsv: google-site-verification, obtenido de '<meta name="google-site-verification" content="([^"]*)"'
# pwd: Password
def generar_token(gsv, pwd):
    txt = obtener_cripto(pwd, gsv)

    _0x382d28 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    valors = [0, 0, 0]
    cicle = 0
    retorn = ''
    for ch in txt:
        valors[cicle] = ord(ch)
        cicle += 1
        if cicle == 3:
            primer = _0x382d28[valors[0] >> 0x2]
            segon  = _0x382d28[((valors[0] & 0x3) << 0x4) | (valors[1] >> 0x4)]
            tercer = _0x382d28[((valors[1] & 0xf) << 0x2) | (valors[2] >> 0x6)]
            quart  = _0x382d28[valors[2] & 0x3f]
            retorn += primer + segon + tercer + quart
            
            valors = [0, 0, 0]
            cicle = 0

    return retorn


def obtener_cripto(password, plaintext):
    import os, base64, json
    SALT_LENGTH = 8
    BLOCK_SIZE = 16
    KEY_SIZE = 32

    salt = os.urandom(SALT_LENGTH)
    iv = os.urandom(BLOCK_SIZE)

    paddingLength = 16 - (len(plaintext) % 16)
    paddedPlaintext = plaintext+chr(paddingLength)*paddingLength

    kdf = evpKDF(password, salt)

    try: # Intentar con librería AES del sistema
        from Crypto.Cipher import AES
        cipherSpec = AES.new(kdf['key'], AES.MODE_CBC, iv)
    except: # Si falla intentar con librería del addon 
        import jscrypto
        cipherSpec = jscrypto.new(kdf['key'], jscrypto.MODE_CBC, iv)
    ciphertext = cipherSpec.encrypt(paddedPlaintext)

    return json.dumps({'ct': base64.b64encode(ciphertext), 'iv': iv.encode("hex"), 's': salt.encode("hex")}, sort_keys=True, separators=(',', ':'))


def evpKDF(passwd, salt, key_size=8, iv_size=4, iterations=1, hash_algorithm="md5"):
    import hashlib
    target_key_size = key_size + iv_size
    derived_bytes = ""
    number_of_derived_words = 0
    block = None
    hasher = hashlib.new(hash_algorithm)
    while number_of_derived_words < target_key_size:
        if block is not None:
            hasher.update(block)

        hasher.update(passwd)
        hasher.update(salt)
        block = hasher.digest()
        hasher = hashlib.new(hash_algorithm)

        for i in range(1, iterations):
            hasher.update(block)
            block = hasher.digest()
            hasher = hashlib.new(hash_algorithm)

        derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]

        number_of_derived_words += len(block)/4

    return {
        "key": derived_bytes[0: key_size * 4],
        "iv": derived_bytes[key_size * 4:]
    }


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Valores extraídos de los js para los dominios tratados (pendiente automatizar!)
# Ej: https://pelispedia.video/plugins/gkpluginsphp.js?v=3.3
# Ej: https://s2.animeyt.tv/rakuten/plugins/rakuten676.js?v=200000000

def calcular_sutorimux(url):
    dominio = urlparse.urlparse(url).netloc
    claves = {
        'pelispedia.video': 'b0a8c83650f18ccc7c87b16e3c460474',
        'load.pelispedia.vip': '4fe554b59d760c9986c903b07af8b7a4',

        's1.animeyt.tv': '0cdf0d0302091bc22a0afdc3f13c0773',
        's2.animeyt.tv': '079c3ee3ca289af95d819d93b852ed94',
        's3.animeyt.tv': '6c21a435bce9f5926d26db567fee1241',
        's4.animeyt.tv': '38546fb4797f2f7c5b6690a5b4a47e34',
        's10.animeyt.tv': 'be88e4cc014c0ae6f9f2d1f947b3b23b',
        's.animeyt.tv': '49f911abffe682820dc5b54777713974',
        'server.animeyt.tv': '2c60637d7f7aa54225c20aea61a2b468',
        'api.animeyt.tv': '54092dea9fd2e163aaa59ad0c4351866',
    }
    return '' if dominio not in claves else claves[dominio]


def calcular_sufijo(url):
    dominio = urlparse.urlparse(url).netloc
    claves = {
        'pelispedia.video': '2653',
        'load.pelispedia.vip': '785446346',

        's1.animeyt.tv': '',
        's2.animeyt.tv': '3497510',
        's3.animeyt.tv': '',
        's4.animeyt.tv': '',
        's10.animeyt.tv': '',
        's.animeyt.tv': '',
        'server.animeyt.tv': '',
        'api.animeyt.tv': '',
    }
    return '' if dominio not in claves else claves[dominio]
 
 
def calcular_url_gk(url):
    dominio = urlparse.urlparse(url).netloc
    claves = {
        'pelispedia.video': 'https://pelispedia.video/plugins/cloupedia.php', # plugins/gkpedia.php
        'load.pelispedia.vip': '',

        's1.animeyt.tv': '',
        's2.animeyt.tv': 'https://s2.animeyt.tv/rakuten/plugins/gkpluginsphp.php',
        's3.animeyt.tv': '',
        's4.animeyt.tv': '',
        's10.animeyt.tv': '',
        's.animeyt.tv': '',
        'server.animeyt.tv': '',
        'api.animeyt.tv': '',
    }
    return '' if dominio not in claves else claves[dominio]
