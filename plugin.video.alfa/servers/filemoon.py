# Conector tiwikiwi By Alfa development Group
# --------------------------------------------------------
import json
import base64
import hashlib
from core import httptools
from core import scrapertools
from platformcode import logger
from core import urlparse
import patch

_have_cryptography = False
_have_pycrypto = False
AESGCM = None
PyCryptoAES = None

try:
    patch.unfix_path()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    patch.fix_path()
    _have_cryptography = True
except Exception:
    _have_cryptography = False
    AESGCM = None 
try:
    patch.unfix_path()
    from Cryptodome.Cipher import AES as PyCryptoAES
    _have_pycrypto = True
    patch.fix_path()
except Exception:
    try:
        from Crypto.Cipher import AES as PyCryptoAES
        _have_pycrypto = True
    except Exception:
        _have_pycrypto = False
        PyCryptoAES = None

kwargs = {'set_tls': False, 'set_tls_min': False, 'retries_cloudflare': 5, 'ignore_response_code': True, 'cf_assistant': False}

# https://filemooon.link/e/mlx76kltz6tn    
# https://filemoon.to/  error


# https://filemooon.link/e/ou7h5asxqrkg
# https://filemooon.link/api/videos/ou7h5asxqrkg/embed/playback

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    
    if not (_have_cryptography or _have_pycrypto):
        logger.error("Neither cryptography nor pycryptodome libraries are available")
        return False,  "Neither cryptography nor pycryptodome libraries are available"

    match = scrapertools.find_single_match(page_url, r'([a-z0-9]+)$')
    if match:
        playback_url = 'https://filemooon.link/api/videos/%s/embed/playback' % match
    else:
        return False,  "[filemoon] El enlace no es correcto"
        
    kwargs['headers'] = {'Referer': page_url}
    
    try:
        data = httptools.downloadpage(playback_url, **kwargs).json
    except Exception as e:
        logger.error(e)
        return False,  "[filemoon] El video no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    # logger.debug(data)
    playback_data = data.get("playback", {})
    try:
        algorithm = playback_data.get("algorithm")
        iv_b64 = playback_data.get("iv")
        payload_b64 = playback_data.get("payload")
        key_parts = playback_data.get("key_parts", [])
        if algorithm != "AES-256-GCM" or len(key_parts) != 2:
            logger.error("Unsupported algorithm or invalid key parts")
            logger.error("algorithm=%s key_parts=%s" % (algorithm, key_parts))
            return video_urls
        def b64u_decode(s):
            s = s.replace('-', '+').replace('_', '/')
            padding = len(s) % 4
            if padding:
                s += '=' * (4 - padding)
            return base64.b64decode(s)
        iv = b64u_decode(iv_b64)
        payload = b64u_decode(payload_b64)
        kp1, kp2 = key_parts
        try:
            k1 = b64u_decode(kp1)
        except:
            k1 = kp1.encode()
        try:
            k2 = b64u_decode(kp2)
        except:
            k2 = kp2.encode()
        raw_key = k1 + k2
        if len(raw_key) != 32:
            key = hashlib.sha256(raw_key).digest()
        else:
            key = raw_key
        
        pt = None
        # Prefer cryptography's AESGCM if available
        if _have_cryptography and AESGCM is not None:
            try:
                aesgcm = AESGCM(key)
                pt = aesgcm.decrypt(iv, payload, None)
            except Exception as e:
                logger.error("cryptography AESGCM decryption failed: %s", e)
                raise
        # Fallback to PyCryptodome AES GCM
        elif _have_pycrypto and PyCryptoAES is not None:
            try:
                # PyCryptodome expects ciphertext and tag separately
                if len(payload) < 16:
                    raise ValueError('Payload too short to contain a GCM tag')
                tag = payload[-16:]
                ciphertext = payload[:-16]
                cipher = PyCryptoAES.new(key, PyCryptoAES.MODE_GCM, nonce=iv)
                pt = cipher.decrypt_and_verify(ciphertext, tag)
            except Exception as e:
                logger.error("PyCryptodome AES GCM decryption failed: %s", e)
                raise
        else:
            logger.error("No suitable AES-GCM implementation available")
            return video_urls

        decrypted_json = pt.decode('utf-8', errors='replace')
        # logger.debug("Decrypted JSON: %s" % decrypted_json)
        playback_data = json.loads(decrypted_json)
        m3u8_source = playback_data.get("sources", [{}])[0].get("url")
        if m3u8_source:
            host = httptools.obtain_domain(page_url, scheme=True)
            headers = httptools.default_headers.copy()
            headers = "|%s&Referer=%s/&Origin=%s" % (urlparse.urlencode(headers), host, host)
            video_urls.append(['[filemoon] m3u', m3u8_source+headers])

    except Exception as e:
        logger.error(e)

    return video_urls
