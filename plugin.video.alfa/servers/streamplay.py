# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger

headers = [['User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0']]
host = "http://streamplay.to/"


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data
    if data == "File was deleted":
        return False, "[Streamplay] El archivo no existe o ha sido borrado"
    elif "Video is processing now" in data:
        return False, "[Streamplay] El archivo se está procesando"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)

    referer = re.sub(r"embed-|player-", "", page_url)[:-5]
    data = httptools.downloadpage(page_url, headers={'Referer': referer}).data

    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed)
    _0xd003 = scrapertools.find_single_match(data, 'var _0xd003=(\[[^;]+\]);')

    video_urls = []
    url = scrapertools.find_single_match(unpacked, '(http[^,]+\.mp4)')

    video_urls.append([".mp4" + " [streamplay]", S(_0xd003).decode(url)])

    video_urls.sort(key=lambda x: x[0], reverse=True)
    for video_url in video_urls:
        logger.info("%s - %s" % (video_url[0], video_url[1]))

    return video_urls


class S:
    def __init__(self, _0xd003):
        self.r = None
        self.s = None
        self.k = None
        self.n = None
        self.c = None
        self.b = None
        self.d = None

        _0xd003 = eval(_0xd003)
        self.t(_0xd003[13] + _0xd003[14] + _0xd003[13] + _0xd003[14], _0xd003[15])

    def decode(self, url):
        _hash = re.compile('[A-z0-9_-]{40,}', re.DOTALL).findall(url)[0]
        return url.replace(_hash, self.p(_hash))

    def t(self, t, i):
        self.r = 20
        self.s = [1634760805, 857760878, 2036477234, 1797285236]
        self.k = []
        self.n = [0, 0]
        self.c = [0, 0]
        self.b = [None] * 64
        self.d = 64

        self.sk(self.sa(t))
        self.sn(self.sa(i))

    def e(self, t):
        s = self.gb(len(t))
        i = [s[h] ^ t[h] for h in range(len(t))]
        return i

    def p(self, t):
        import base64
        t += "=" * (4 - len(t) % 4)
        t = base64.b64decode(t.replace('-', '+').replace('_', '/'))
        return self._as(self.e(self.sa(t)))

    @staticmethod
    def sa(t):
        s = [ord(t[i]) for i in range(len(t))]
        return s

    @staticmethod
    def _as(t):
        s = [chr(t[i]) for i in range(len(t))]
        return ''.join(s)

    def sk(self, t):
        s = 0
        for i in range(8):
            self.k.append(
                255 & t[s] | self.lshift((255 & t[s + 1]), 8) | self.lshift((255 & t[s + 2]), 16) | self.lshift(
                    (255 & t[s + 3]), 24))
            s += 4
        self._r()

    def sn(self, t):
        self.n[0] = 255 & t[0] | self.lshift((255 & t[1]), 8) | self.lshift((255 & t[2]), 16) | self.lshift(
            (255 & t[3]), 24)
        self.n[1] = 255 & t[4] | self.lshift((255 & t[5]), 8) | self.lshift((255 & t[6]), 16) | self.lshift(
            (255 & t[7]), 24)
        self._r()

    def gb(self, t):
        i = [None] * t

        for s in range(t):
            if 64 == self.d:
                self._g()
                self._i()
                self.d = 0

            i[s] = self.b[self.d]
            self.d += 1

        return i

    def gh(self, t):
        i = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
        h = self.gb(t)
        s = [i[self.rshift(h[b], 4) & 15] for b in range(len(h))]
        s.append(i[15 & h[len(h)]])
        return ''.join(s)

    def _r(self):
        self.c[0] = 0
        self.c[1] = 0
        self.d = 64

    def _i(self):
        self.c[0] = self.c[0] + 1 & 4294967295
        if 0 == self.c[0]:
            self.c[1] = self.c[1] + 1 & 4294967295

    def _g(self):
        i = self.s[0]
        s = self.k[0]
        h = self.k[1]
        b = self.k[2]
        r = self.k[3]
        n = self.s[1]
        o = self.n[0]
        e = self.n[1]
        c = self.c[0]
        p = self.c[1]
        a = self.s[2]
        f = self.k[4]
        u = self.k[5]
        g = self.k[6]
        y = self.k[7]
        k = self.s[3]
        l = i
        d = s
        v = h
        _ = b
        A = r
        w = n
        C = o
        S = e
        j = c
        m = p
        q = a
        x = f
        z = u
        B = g
        D = y
        E = k

        for F in range(0, self.r, 2):
            # 0
            t = l + z
            A ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = A + l
            j ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = j + A
            z ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = z + j
            l ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 1
            t = w + d
            m ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = m + w
            B ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = B + m
            d ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = d + B
            w ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 2
            t = q + C
            D ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = D + q
            v ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = v + D
            C ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = C + v
            q ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 3
            t = E + x
            _ ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = _ + E
            S ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = S + _
            x ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = x + S
            E ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 4
            t = l + _
            d ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = d + l
            v ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = v + d
            _ ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = _ + v
            l ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 5
            t = w + A
            C ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = C + w
            S ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = S + C
            A ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = A + S
            w ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 6
            t = q + m
            x ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = x + q
            j ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = j + x
            m ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = m + j
            q ^= self.lshift(t, 18) | self.bshift(t, 14)

            # 7
            t = E + D
            z ^= self.lshift(t, 7) | self.bshift(t, 25)
            t = z + E
            B ^= self.lshift(t, 9) | self.bshift(t, 23)
            t = B + z
            D ^= self.lshift(t, 13) | self.bshift(t, 19)
            t = D + B
            E ^= self.lshift(t, 18) | self.bshift(t, 14)

        l += i
        d += s
        v += h
        _ += b
        A += r
        w += n
        C += o
        S += e
        j += c
        m += p
        q += a
        x += f
        z += u
        B += g
        D += y
        E += k

        self.b[0] = self.bshift(l, 0) & 255
        self.b[1] = self.bshift(l, 8) & 255
        self.b[2] = self.bshift(l, 16) & 255
        self.b[3] = self.bshift(l, 24) & 255
        self.b[4] = self.bshift(d, 0) & 255
        self.b[5] = self.bshift(d, 8) & 255
        self.b[6] = self.bshift(d, 16) & 255
        self.b[7] = self.bshift(d, 24) & 255
        self.b[8] = self.bshift(v, 0) & 255
        self.b[9] = self.bshift(v, 8) & 255
        self.b[10] = self.bshift(v, 16) & 255
        self.b[11] = self.bshift(v, 24) & 255
        self.b[12] = self.bshift(_, 0) & 255
        self.b[13] = self.bshift(_, 8) & 255
        self.b[14] = self.bshift(_, 16) & 255
        self.b[15] = self.bshift(_, 24) & 255
        self.b[16] = self.bshift(A, 0) & 255
        self.b[17] = self.bshift(A, 8) & 255
        self.b[18] = self.bshift(A, 16) & 255
        self.b[19] = self.bshift(A, 24) & 255
        self.b[20] = self.bshift(w, 0) & 255
        self.b[21] = self.bshift(w, 8) & 255
        self.b[22] = self.bshift(w, 16) & 255
        self.b[23] = self.bshift(w, 24) & 255
        self.b[24] = self.bshift(C, 0) & 255
        self.b[25] = self.bshift(C, 8) & 255
        self.b[26] = self.bshift(C, 16) & 255
        self.b[27] = self.bshift(C, 24) & 255
        self.b[28] = self.bshift(S, 0) & 255
        self.b[29] = self.bshift(S, 8) & 255
        self.b[30] = self.bshift(S, 16) & 255
        self.b[31] = self.bshift(S, 24) & 255
        self.b[32] = self.bshift(j, 0) & 255
        self.b[33] = self.bshift(j, 8) & 255
        self.b[34] = self.bshift(j, 16) & 255
        self.b[35] = self.bshift(j, 24) & 255
        self.b[36] = self.bshift(m, 0) & 255
        self.b[37] = self.bshift(m, 8) & 255
        self.b[38] = self.bshift(m, 16) & 255
        self.b[39] = self.bshift(m, 24) & 255
        self.b[40] = self.bshift(q, 0) & 255
        self.b[41] = self.bshift(q, 8) & 255
        self.b[42] = self.bshift(q, 16) & 255
        self.b[43] = self.bshift(q, 24) & 255
        self.b[44] = self.bshift(x, 0) & 255
        self.b[45] = self.bshift(x, 8) & 255
        self.b[46] = self.bshift(x, 16) & 255
        self.b[47] = self.bshift(x, 24) & 255
        self.b[48] = self.bshift(z, 0) & 255
        self.b[49] = self.bshift(z, 8) & 255
        self.b[50] = self.bshift(z, 16) & 255
        self.b[51] = self.bshift(z, 24) & 255
        self.b[52] = self.bshift(B, 0) & 255
        self.b[53] = self.bshift(B, 8) & 255
        self.b[54] = self.bshift(B, 16) & 255
        self.b[55] = self.bshift(B, 24) & 255
        self.b[56] = self.bshift(D, 0) & 255
        self.b[57] = self.bshift(D, 8) & 255
        self.b[58] = self.bshift(D, 16) & 255
        self.b[59] = self.bshift(D, 24) & 255
        self.b[60] = self.bshift(E, 0) & 255
        self.b[61] = self.bshift(E, 8) & 255
        self.b[62] = self.bshift(E, 16) & 255
        self.b[63] = self.bshift(E, 24) & 255

    def lshift(self, num, other):
        lnum = self.ToInt32(num)
        rnum = self.ToUint32(other)
        shift_count = rnum & 0x1F
        return self.ToInt32(lnum << shift_count)

    def rshift(self, num, other):
        lnum = self.ToInt32(num)
        rnum = self.ToUint32(other)
        shift_count = rnum & 0x1F
        return self.ToInt32(lnum >> shift_count)

    def bshift(self, num, other):
        lnum = self.ToUint32(num)
        rnum = self.ToUint32(other)
        shift_count = rnum & 0x1F
        return self.ToUint32(lnum >> shift_count)

    @staticmethod
    def ToInt32(num):
        int32 = num % 2 ** 32
        return int32 - 2 ** 32 if int32 >= 2 ** 31 else int32

    @staticmethod
    def ToUint32(num):
        return num % 2 ** 32
