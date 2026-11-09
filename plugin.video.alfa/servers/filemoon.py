# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector filemoon (plataforma "Byse")
#
# MEDIDO el 2026-10-12. La web ya NO es el filemoon de antes: es el panel "Byse", y su
# reproductor no entrega el video sin pasar antes un captcha. Ese captcha NO es una imagen:
# es un PROOF-OF-WORK que se puede calcular desde el addon (no hace falta "pulsar" nada).
#
#   GET  /api/videos/<id>/details              -> 200 / 404 (para test_video_exists)
#   GET  /api/videos/<id>/settings             -> dice si el video pide captcha
#   POST /api/videos/<id>/embed/captcha        -> {"pow_nonce","pow_difficulty","pow_token"}
#   POST /api/videos/<id>/embed/captcha/verify -> {"status":"ok","token":..}  (el token dura 1800 s)
#   POST /api/videos/<id>/playback             -> playback cifrado. Exige LAS DOS COSAS:
#                                                 cabecera "X-Captcha-Token" Y cuerpo {"fingerprint": {...}}
#                                                 (sin el token: 428 captcha_required;
#                                                  sin "fingerprint": 405 method not allowed)
#
# El proof-of-work: hallar el menor entero `s` tal que  hash(nonce + ":" + s)  tenga
# `pow_difficulty` bits a cero por delante. OJO: ese hash NO es SHA-256, es un hash propio del
# reproductor (portado abajo en `_hash_pow`); con SHA-256 el servidor contesta "pow_failed".
# La dificultad medida es 16-17 bits, o sea 65.536-131.072 intentos: entre 1 y 7 minutos en Python
# (1,8 ms por intento). Por eso el token se guarda en el directorio de datos del addon: dura 30
# minutos, sirve para OTROS videos y OTROS dominios, y aguanta incluso un cambio de IP (todo medido),
# con lo que la espera se paga una sola vez por sesion.
#
# El playback va cifrado (AES-256-GCM) y `key_parts` trae 30 trozos: solo DOS son la clave, los
# que dice `version` ([version, 31-version], indices 1-based). Los otros 28 (24 bytes) son senuelos.
#
# OJO, y no es culpa del conector: el CDN de los .m3u8 (edge1-*-sprintcdn.* / *.r66nv9ed.com,
# rango 185.248.171.x) esta BLOQUEADO por la operadora del usuario ("Contenido bloqueado por
# requerimiento de la Autoridad Competente"; medido el 2026-10-12, el bloqueo es por IP).
# COMPROBADO el 2026-10-13 con Cloudflare WARP activo: el mismo enlace responde 200 #EXTM3U, la
# variante trae 142 segmentos SIN cifrar y el primer segmento es video/MP2T de 2,1 MB que empieza
# por 0x47. O sea: con VPN se ve; sin VPN el CDN no responde (y el token sobrevive al cambio de IP).
# El CDN NO pide cabeceras: master, variante y segmento dan 200 hasta con el User-Agent de Kodi.
# --------------------------------------------------------

import base64
import json
import os
import re
import time

from core import httptools
from core import urlparse
from platformcode import config, logger
import patch

# retries_cloudflare a 0: la API responde a la primera y el solucionador de Cloudflare de Alfa
# solo añadiria esperas.
kwargs = {"set_tls": True, "set_tls_min": True, "retries_cloudflare": 0,
          "ignore_response_code": True, "cf_assistant": False, "timeout": 20}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

patch.unfix_path()
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _have_cryptography = True
except Exception:
    _have_cryptography = False
    AESGCM = None
try:
    from Cryptodome.Cipher import AES as PyCryptoAES
    _have_pycrypto = True
except Exception:
    try:
        from Crypto.Cipher import AES as PyCryptoAES
        _have_pycrypto = True
    except Exception:
        _have_pycrypto = False
        PyCryptoAES = None
patch.fix_path()


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
def _partir(page_url):
    """Separa la url de su sufijo |cabeceras=.. (Alfa se lo pega al enlace)."""
    if '|' not in page_url:
        return page_url, {}
    url, resto = page_url.split('|', 1)
    return url, dict(urlparse.parse_qsl(resto))


def _base(url):
    """https://filemoon.sx/e/xxxx -> https://filemoon.sx"""
    trozo = urlparse.urlparse(url)
    if not trozo.scheme or not trozo.netloc:
        return ''
    return '%s://%s' % (trozo.scheme, trozo.netloc)


def _codigo(url):
    """El id del video (12 caracteres en los casos vistos)."""
    match = re.search(r'/(?:e|d)/([A-Za-z0-9]+)', url)
    return match.group(1) if match else ''


def _cabeceras(pagina, extra=None):
    cab = {'User-Agent': UA, 'Accept': 'application/json, text/plain, */*',
           'Referer': pagina, 'Origin': _base(pagina)}
    if extra:
        cab.update(extra)
    return cab


def _peticion(url, datos=None, cabeceras=None):
    """Devuelve (codigo, dict). Nunca lanza: si la respuesta no es JSON, el dict va vacio."""
    opt = dict(kwargs)
    opt['headers'] = dict(cabeceras or {'User-Agent': UA, 'Accept': 'application/json, text/plain, */*'})
    if datos is not None:
        opt['post'] = json.dumps(datos)
        opt['headers']['Content-Type'] = 'application/json'

    try:
        respuesta = httptools.downloadpage(url, **opt)
        codigo = respuesta.code
    except Exception as e:
        logger.error('[filemoon] fallo la peticion %s: %s' % (url, e))
        return 0, {}

    salida = getattr(respuesta, 'json', None)
    if not isinstance(salida, dict) or not salida:
        salida = {}
        crudo = getattr(respuesta, 'data', '') or ''
        if isinstance(crudo, bytes):
            crudo = crudo.decode('utf-8', 'replace')
        try:
            salida = json.loads(crudo)
        except Exception:
            salida = {}

    return codigo, salida


# ---------------------------------------------------------------------------
# proof-of-work (port literal del reproductor: /assets/pow-*.js)
# ---------------------------------------------------------------------------
_M = 0xFFFFFFFF
_BE = 512
_LT = _BE - 1
_LR = 2654435761
_HR = 2246822519


def _hash_pow(datos, palabras=8):
    """Hash propio del reproductor Byse (NO es SHA-256).

    Devuelve los `palabras` primeros enteros de 32 bits del resumen. Se puede pedir menos de 8
    porque las palabras se calculan EN ORDEN y no dependen de las siguientes; para una dificultad
    de 16 bits basta la primera, y eso ahorra un 22% del trabajo (ver `_cumple_pow`).
    """
    e0, e1, e2, e3 = 1779033703, 3144134277, 1013904242, 2773480762
    for byte in datos:
        e0 = (e0 + byte) & _M
        e0 = ((e0 << 7) | (e0 >> 25)) & _M
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 16) | (t >> 16)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 12) | (t >> 20)) & _M
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 8) | (t >> 24)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 7) | (t >> 25)) & _M

    # 8 rondas de mezcla
    for _ in range(8):
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 16) | (t >> 16)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 12) | (t >> 20)) & _M
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 8) | (t >> 24)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 7) | (t >> 25)) & _M

    # estado interno de 512 palabras
    r = [0] * _BE
    for i in range(_BE):
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 16) | (t >> 16)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 12) | (t >> 20)) & _M
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 8) | (t >> 24)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 7) | (t >> 25)) & _M
        r[i] = e0 ^ e2

    for _ in range(2):
        for s in range(_BE):
            c = (r[s] + r[r[s] & _LT]) & _M
            c = ((c << 13) | (c >> 19)) & _M
            c = (c ^ ((r[(s + 1) & _LT] * _LR) & _M)) & _M
            r[s] = c
            e0 = e0 ^ c
            e0 = (e0 + e1) & _M
            t = e3 ^ e0
            e3 = ((t << 16) | (t >> 16)) & _M
            e2 = (e2 + e3) & _M
            t = e1 ^ e2
            e1 = ((t << 12) | (t >> 20)) & _M
            e0 = (e0 + e1) & _M
            t = e3 ^ e0
            e3 = ((t << 8) | (t >> 24)) & _M
            e2 = (e2 + e3) & _M
            t = e1 ^ e2
            e1 = ((t << 7) | (t >> 25)) & _M

    salida = [0] * palabras
    porcion = _BE // 8
    for i in range(palabras):
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 16) | (t >> 16)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 12) | (t >> 20)) & _M
        e0 = (e0 + e1) & _M
        t = e3 ^ e0
        e3 = ((t << 8) | (t >> 24)) & _M
        e2 = (e2 + e3) & _M
        t = e1 ^ e2
        e1 = ((t << 7) | (t >> 25)) & _M
        v = e0
        arranque = i * porcion
        for c in range(porcion):
            d = r[arranque + c]
            v = (v + d) & _M
            v = ((v << 5) | (v >> 27)) & _M
            v = (v ^ ((d * _HR) & _M)) & _M
        salida[i] = (v ^ e2) & _M
    return salida


def _ceros_delante(palabras):
    """Bits a cero por delante del resumen (la misma cuenta que hace el reproductor)."""
    total = 0
    for x in palabras:
        if x == 0:
            total += 32
            continue
        return total + (32 - x.bit_length())
    return total


def _cumple_pow(datos, dificultad):
    """¿El hash de `datos` tiene `dificultad` bits a cero por delante? Solo calcula lo necesario.

    Con `dificultad` bits hacen falta `dificultad//32 + 1` palabras: si todas salen a cero, la
    cuenta parcial (32 por palabra) ya supera la dificultad, y si alguna no lo es, el numero de
    ceros se cuenta exacto desde el principio.
    """
    if dificultad <= 0:
        return True

    necesarias = int(dificultad) // 32 + 1
    if necesarias > 8:
        necesarias = 8

    return _ceros_delante(_hash_pow(datos, necesarias)) >= dificultad


def _cierra(dialogo):
    try:
        dialogo.close()
    except Exception:
        pass


def _resuelve_pow(nonce, dificultad, dialogo=None):
    """Busca la solucion del reto. Devuelve str, o None si el usuario cancela o se agota."""
    if dificultad <= 0:
        return '0'

    prefijo = (nonce + ':').encode('ascii')
    esperados = 1.0 * (2 ** int(dificultad))
    # tope de seguridad: 4 veces lo esperado. Si con eso no ha salido, algo va mal (la
    # probabilidad de no encontrarlo en 4 veces la media es ~2%): mejor decirlo que colgarse.
    tope = int(esperados * 4)
    s = 0
    while True:
        for _ in range(1024):
            if _cumple_pow(prefijo + str(s).encode('ascii'), dificultad):
                _cierra(dialogo)
                return str(s)
            s += 1
            if s > tope:
                logger.error('[filemoon] el captcha no salio en %s intentos (se abandona)' % s)
                _cierra(dialogo)
                return None
        if dialogo:
            # probabilidad de haber dado YA con la solucion: 1 - 2^(-s/esperados). Se mueve desde
            # el primer momento (la cuenta de intentos empieza en 0, no al 100% de la media).
            porcentaje = int(100 * (1.0 - (2.0 ** (-1.0 * s / esperados))))
            if porcentaje > 99:
                porcentaje = 99
            try:
                dialogo.update(porcentaje, 'Filemoon',
                               'Resolviendo el captcha del reproductor... '
                               '%s intentos (%s%%). Se hace una vez cada 30 minutos.' % (s, porcentaje))
                if dialogo.iscanceled():
                    logger.info('[filemoon] captcha cancelado por el usuario')
                    return None
            except Exception:
                dialogo = None


# ---------------------------------------------------------------------------
# token del captcha (cache en el directorio de datos del addon)
# ---------------------------------------------------------------------------
def _ficha():
    return os.path.join(config.get_data_path(), 'filemoon_token.json')


def _token_guardado():
    """El token vale para CUALQUIER dominio de filemoon (medido el 2026-10-12): va por IP, no por host."""
    try:
        fichero = open(_ficha(), 'r')
        datos = json.load(fichero)
        fichero.close()
    except Exception:
        return ''

    if datos.get('token') and datos.get('caduca', 0) > time.time():
        logger.info('[filemoon] token del captcha reutilizado de %s (caduca en %d s)'
                    % (datos.get('host', '?'), int(datos['caduca'] - time.time())))
        return datos['token']
    return ''


def _guarda_token(host, token, segundos):
    # 60 s de margen para no usarlo justo cuando caduca
    datos = {'token': token, 'host': host, 'caduca': time.time() + max(60, segundos - 60)}
    try:
        fichero = open(_ficha(), 'w')
        json.dump(datos, fichero)
        fichero.close()
    except Exception as e:
        logger.error('[filemoon] no se pudo guardar el token: %s' % e)


def _borra_token():
    try:
        os.remove(_ficha())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# la cadena
# ---------------------------------------------------------------------------
def _pide_token(base, codigo, pagina, dialogo):
    """Pasa el captcha: pide el reto, resuelve el proof-of-work y lo verifica."""
    codigo_http, reto = _peticion('%s/api/videos/%s/embed/captcha' % (base, codigo),
                                  datos={}, cabeceras=_cabeceras(pagina))
    nonce = reto.get('pow_nonce')
    if codigo_http != 200 or not nonce:
        logger.error('[filemoon] el reto del captcha no llego (%s): %s' % (codigo_http, reto))
        return ''

    try:
        dificultad = int(reto.get('pow_difficulty') or 0)
    except Exception:
        dificultad = 0

    logger.info('[filemoon] reto captcha: dificultad=%s nonce=%s' % (dificultad, nonce))
    solucion = _resuelve_pow(nonce, dificultad, dialogo)
    if solucion is None:
        return ''

    codigo_http, respuesta = _peticion('%s/api/videos/%s/embed/captcha/verify' % (base, codigo),
                                       datos={'pow_token': reto.get('pow_token'),
                                              'solution': solucion},
                                       cabeceras=_cabeceras(pagina))
    if respuesta.get('status') != 'ok' or not respuesta.get('token'):
        logger.error('[filemoon] captcha sin resolver (%s): %s' % (codigo_http, respuesta))
        return ''

    segundos = respuesta.get('expires_in') or 1800
    _guarda_token(base, respuesta['token'], segundos)
    logger.info('[filemoon] captcha resuelto con la solucion %s; token valido %s s'
                % (solucion, segundos))
    return respuesta['token']


def _playback(base, codigo, pagina, token):
    """POST del playback. Devuelve el dict 'playback', o None si el token ya no vale."""
    # el servidor exige un cuerpo con "fingerprint": sin el responde 405 aunque el token sea bueno
    huella = {'token': (token or '')[:32], 'viewer_id': 'alfa', 'device_id': 'kodi',
              'confidence': 1.0}
    codigo_http, respuesta = _peticion('%s/api/videos/%s/playback' % (base, codigo),
                                       datos={'fingerprint': huella},
                                       cabeceras=_cabeceras(pagina, {'X-Captcha-Token': token}))

    if codigo_http == 428:
        logger.info('[filemoon] el token del captcha ya no vale (428)')
        return None
    if codigo_http != 200:
        logger.error('[filemoon] playback respondio %s: %s' % (codigo_http, respuesta))
        return None

    return respuesta.get('playback')


def _b64u(texto):
    texto = (texto or '').replace('-', '+').replace('_', '/')
    return base64.b64decode(texto + '=' * (-len(texto) % 4))


def _partes_de_la_clave(playback):
    """Solo dos de las key_parts son la clave: las que indica 'version' ([n, 31-n], 1-based)."""
    partes = playback.get('key_parts') or []
    try:
        version = int(str(playback.get('version')).strip())
    except Exception:
        version = 0

    if 1 <= version <= 20:
        primera, segunda = version, 31 - version
        if 1 <= primera <= len(partes) and 1 <= segunda <= len(partes):
            elegidas = [partes[primera - 1], partes[segunda - 1]]
            elegidas = [p for p in elegidas if isinstance(p, str) and p]
            if elegidas:
                return elegidas

    logger.info('[filemoon] sin "version" utilizable; se usan todas las key_parts')
    return partes


def _descifra(playback):
    """AES-256-GCM con la clave montada con las key_parts. Devuelve el dict con sources/tracks."""
    if playback.get('algorithm') != 'AES-256-GCM':
        logger.error('[filemoon] algoritmo no soportado: %s' % playback.get('algorithm'))
        return {}

    partes = _partes_de_la_clave(playback)
    clave = b''.join(_b64u(p) for p in partes)
    iv = _b64u(playback.get('iv'))
    payload = _b64u(playback.get('payload'))

    # el reproductor no hashea la clave: son los trozos pegados tal cual
    if len(clave) not in (16, 24, 32):
        candidatas = b''.join(_b64u(p) for p in partes if len(_b64u(p)) == 16)
        if len(candidatas) in (16, 24, 32):
            logger.info('[filemoon] la clave de %d bytes no vale; se usan los trozos de 16 bytes'
                        % len(clave))
            clave = candidatas
        else:
            logger.error('[filemoon] la clave no tiene un tamaño AES valido (%d bytes)' % len(clave))
            return {}

    claro = None
    if _have_cryptography and AESGCM is not None:
        try:
            claro = AESGCM(clave).decrypt(iv, payload, None)
        except Exception as e:
            logger.error('[filemoon] AESGCM (cryptography) fallo: %s' % e)
    if not claro and _have_pycrypto and PyCryptoAES is not None:
        try:
            cipher = PyCryptoAES.new(clave, PyCryptoAES.MODE_GCM, nonce=iv)
            claro = cipher.decrypt_and_verify(payload[:-16], payload[-16:])
        except Exception as e:
            logger.error('[filemoon] AES-GCM (pycryptodome) fallo: %s' % e)
    if not claro:
        logger.error('[filemoon] no hay forma de descifrar el playback (¿cryptography/pycryptodome?)')
        return {}

    try:
        return json.loads(claro.decode('utf-8', 'replace'))
    except Exception as e:
        logger.error('[filemoon] el playback descifrado no es JSON: %s' % e)
        return {}


# ---------------------------------------------------------------------------
# interfaz de Alfa
# ---------------------------------------------------------------------------
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    url, _ = _partir(page_url)
    base, codigo = _base(url), _codigo(url)
    if not base or not codigo:
        return False, "[filemoon] El enlace no es correcto"

    codigo_http, _ = _peticion('%s/api/videos/%s/details' % (base, codigo),
                               cabeceras=_cabeceras(url))

    if codigo_http == 404:
        return False, "[filemoon] El video no existe o ha sido borrado"
    if codigo_http != 200:
        return False, "[filemoon] El servidor respondio %s" % codigo_http

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    url, _ = _partir(page_url)
    base, codigo = _base(url), _codigo(url)
    if not base or not codigo:
        return video_urls

    if not (_have_cryptography or _have_pycrypto):
        logger.error('[filemoon] no hay libreria AES disponible')
        return video_urls

    # ¿este video pide captcha? (si no lo pide, nos ahorramos el proof-of-work)
    _, ajustes = _peticion('%s/api/videos/%s/settings' % (base, codigo), cabeceras=_cabeceras(url))
    pide_captcha = ajustes.get('captcha_required', True) is not False

    token = _token_guardado() if pide_captcha else ''

    if pide_captcha and not token:
        logger.info('[filemoon] hay que resolver el captcha (proof-of-work)')
        dialogo = None
        try:
            from platformcode import platformtools
            dialogo = platformtools.dialog_progress(
                'Filemoon', 'Resolviendo el captcha del reproductor...\n'
                            'Puede tardar varios minutos. Se hace UNA vez cada 30 minutos.')
        except Exception:
            pass
        token = _pide_token(base, codigo, url, dialogo)
        _cierra(dialogo)

    playback = _playback(base, codigo, url, token)
    if playback is None and pide_captcha:
        # token caducado o rechazado: se pide otro y se reintenta una sola vez
        _borra_token()
        dialogo = None
        try:
            from platformcode import platformtools
            dialogo = platformtools.dialog_progress(
                'Filemoon', 'El captcha caduco; se resuelve otra vez...\n'
                            'Puede tardar varios minutos. Se hace UNA vez cada 30 minutos.')
        except Exception:
            pass
        token = _pide_token(base, codigo, url, dialogo)
        _cierra(dialogo)
        if token:
            playback = _playback(base, codigo, url, token)

    if not playback:
        logger.error('[filemoon] sin playback para %s' % page_url)
        return video_urls

    datos = _descifra(playback)
    fuentes = datos.get('sources') or []
    logger.info('[filemoon] fuentes descifradas: %d' % len(fuentes))

    # MEDIDO el 2026-10-13 (con WARP): el CDN sirve el master, las variantes y los segmentos
    # (200, #EXTM3U y video/MP2T) con el User-Agent de Kodi y SIN ninguna cabecera. Por eso el
    # enlace va pelado: menos piezas que puedan fallar. Alfa ya usa inputstream.adaptive porque
    # el json de este conector trae force_inputstream: adaptive y la url acaba en .m3u8.
    vistas = []
    for fuente in fuentes:
        enlace = (fuente.get('url') or '').strip()
        if not enlace or enlace in vistas:
            continue
        vistas.append(enlace)
        etiqueta = (fuente.get('label') or fuente.get('quality') or '').strip()
        titulo = '[filemoon] %s' % etiqueta if etiqueta else '[filemoon]'
        video_urls.append([titulo, enlace])

    return video_urls
