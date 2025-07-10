import base64
import patch

try:
    patch.unfix_path()
    from Cryptodome.Cipher import AES
    patch.fix_path()
except Exception:
    from Crypto.Cipher import AES


def crylink(b64decode, encode):
    """
    Sólo los malandros copian código!!!11!1!
    """
    try:
        encrypt = base64.b64decode(b64decode)
        _len = encode.encode("utf-8")
        if len(_len) not in (16, 24, 32): _len = (_len + b"\x00" * 32)[:32]
        return _pkcs7_unpad(AES.new(_len, AES.MODE_CBC, encrypt[:16]).decrypt(encrypt[16:]), AES.block_size).decode('utf-8')
    except Exception: return None

def _pkcs7_unpad(data, block_size = 16):
    pad_len = data[-1]
    if not 1 <= pad_len <= block_size: raise ValueError("Invalid PKCS7 padding")
    if data[-pad_len:] != bytes([pad_len]) * pad_len: raise ValueError("Corrupt PKCS7")
    return data[:-pad_len]
