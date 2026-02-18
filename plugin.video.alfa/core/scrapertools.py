# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Scraper tools for reading and processing web elements
# --------------------------------------------------------------------------------

import sys
import re
import time

from core import urlparse
from platformcode import logger

PY3 = sys.version_info > (3,)
PATTERN_EPISODE_TITLE = r"(?i)(\d+x\d+\s*(?:-\s*)?)?(?:episod(?:e|io)|cap.tulo)\s*\d*\s*(?:\[\d{4}\]\s*)?(?:\[\d{1,2}.\d{1,2}\]\s*)?"


def printMatches(matches):
    i = 0
    for match in matches:
        logger.info("%d %s" % (i, match))
        i = i + 1


def find_single_match(data, pattern, index=0):
    try:
        matches = re.findall(pattern, data, flags=re.DOTALL)
        return matches[index]
    except Exception:
        return ""


# Parse string and extracts multiple matches using regular expressions
def find_multiple_matches(text, pattern):
    return re.findall(pattern, text, re.DOTALL)


def replace(pattern, replacement, data):
    try:
        return re.sub(pattern, replacement, data, flags=re.DOTALL)
    except Exception:
        return ""


def entityunescape(cadena):
    return unescape(cadena)


def unescape(text):
    """Removes HTML or XML character references
       and entities from a text string.
       keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    text = chr(int(text[3:-1], 16)).encode("utf-8")
                else:
                    text = chr(int(text[2:-1])).encode("utf-8")
                if isinstance(text, bytes):
                    text = text.decode("utf-8")
                return text

            except ValueError:
                logger.error("error de valor")
                pass
        else:
            # named entity
            try:
                if PY3:
                    import html.entities as htmlentitydefs
                else:
                    import htmlentitydefs
                text = chr(htmlentitydefs.name2codepoint[text[1:-1]]).encode("utf-8")
                if PY3 and isinstance(text, bytes):
                    text = text.decode("utf-8")
            except KeyError:
                logger.error("keyerror: %s" % str(text))
                pass
            except Exception:
                pass
        return text  # leave as is

    if PY3:
        text = text.replace("\xa0", " ").replace("\xa0", " ")
    else:
        try:
            text = text.replace("\xa0", " ")
        except Exception:
            pass
        try:
            text = text.replace("\xa0", " ")
        except Exception:
            pass

    return re.sub(r"&#?\w+;", fixup, str(text))

    # Convierte los codigos html "&ntilde;" y lo reemplaza por "ñ" caracter unicode utf-8


def decodeHtmlentities(string):
    string = entitiesfix(string)
    entity_re = re.compile(r"&(#?)(\d{1,5}|\w{1,8});")

    def substitute_entity(match):
        if PY3:
            from html.entities import name2codepoint as n2cp
        else:
            from htmlentitydefs import name2codepoint as n2cp
        ent = match.group(2)
        if match.group(1) == "#":
            ent = chr(int(ent)).encode("utf-8")
            if PY3 and isinstance(ent, bytes):
                ent = ent.decode("utf-8")
            return ent
        else:
            cp = n2cp.get(ent)

            if cp:
                cp = chr(cp).encode("utf-8")
                if PY3 and isinstance(cp, bytes):
                    cp = cp.decode("utf-8")
                return cp
            else:
                return match.group()

    return entity_re.subn(substitute_entity, string)[0]


def entitiesfix(string):
    # Las entidades comienzan siempre con el símbolo & , y terminan con un punto y coma ( ; ).
    string = string.replace("&aacute", "&aacute;")
    string = string.replace("&eacute", "&eacute;")
    string = string.replace("&iacute", "&iacute;")
    string = string.replace("&oacute", "&oacute;")
    string = string.replace("&uacute", "&uacute;")
    string = string.replace("&Aacute", "&Aacute;")
    string = string.replace("&Eacute", "&Eacute;")
    string = string.replace("&Iacute", "&Iacute;")
    string = string.replace("&Oacute", "&Oacute;")
    string = string.replace("&Uacute", "&Uacute;")
    string = string.replace("&uuml", "&uuml;")
    string = string.replace("&Uuml", "&Uuml;")
    string = string.replace("&ntilde", "&ntilde;")
    string = string.replace("&#191", "&#191;")
    string = string.replace("&#161", "&#161;")
    string = string.replace(";;", ";")
    return string


def htmlclean(cadena):
    cadena = re.compile("<!--.*?-->", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("<center>", "")
    cadena = cadena.replace("</center>", "")
    cadena = cadena.replace("<cite>", "")
    cadena = cadena.replace("</cite>", "")
    cadena = cadena.replace("<em>", "")
    cadena = cadena.replace("</em>", "")
    cadena = cadena.replace("<u>", "")
    cadena = cadena.replace("</u>", "")
    cadena = cadena.replace("<li>", "")
    cadena = cadena.replace("</li>", "")
    cadena = cadena.replace("<turl>", "")
    cadena = cadena.replace("</tbody>", "")
    cadena = cadena.replace("<tr>", "")
    cadena = cadena.replace("</tr>", "")
    cadena = cadena.replace("<![CDATA[", "")
    cadena = cadena.replace("<wbr>", "")
    cadena = cadena.replace("<Br />", " ")
    cadena = cadena.replace("<BR />", " ")
    cadena = cadena.replace("<Br>", " ")
    cadena = re.compile("<br[^>]*>", re.DOTALL).sub(" ", cadena)

    cadena = re.compile("<script.*?</script>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<option[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</option>", "")

    cadena = re.compile("<button[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</button>", "")

    cadena = re.compile("<i[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</iframe>", "")
    cadena = cadena.replace("</i>", "")

    cadena = re.compile("<table[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</table>", "")

    cadena = re.compile("<td[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</td>", "")

    cadena = re.compile("<div[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</div>", "")

    cadena = re.compile("<dd[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</dd>", "")

    cadena = re.compile("<b[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</b>", "")

    cadena = re.compile("<font[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</font>", "")

    cadena = re.compile("<strong[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</strong>", "")

    cadena = re.compile("<small[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</small>", "")

    cadena = re.compile("<span[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</span>", "")

    cadena = re.compile("<a[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</a>", "")

    cadena = re.compile("<p[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</p>", "")

    cadena = re.compile("<ul[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</ul>", "")

    cadena = re.compile("<h1[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h1>", "")

    cadena = re.compile("<h2[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h2>", "")

    cadena = re.compile("<h3[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h3>", "")

    cadena = re.compile("<h4[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h4>", "")

    cadena = re.compile("<!--[^-]+-->", re.DOTALL).sub("", cadena)

    cadena = re.compile("<img[^>]*>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<object[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</object>", "")
    cadena = re.compile("<param[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</param>", "")
    cadena = re.compile("<embed[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</embed>", "")

    cadena = re.compile("<title[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</title>", "")

    cadena = re.compile("<link[^>]*>", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("\t", "")
    cadena = entityunescape(cadena)
    return cadena


def slugify(title, strict=True, convert=[]):
    # print title

    # Sustituye acentos y eñes
    title = title.replace("Á", "a")
    title = title.replace("É", "e")
    title = title.replace("Í", "i")
    title = title.replace("Ó", "o")
    title = title.replace("Ú", "u")
    title = title.replace("á", "a")
    title = title.replace("é", "e")
    title = title.replace("í", "i")
    title = title.replace("ó", "o")
    title = title.replace("ú", "u")
    title = title.replace("À", "a")
    title = title.replace("È", "e")
    title = title.replace("Ì", "i")
    title = title.replace("Ò", "o")
    title = title.replace("Ù", "u")
    title = title.replace("à", "a")
    title = title.replace("è", "e")
    title = title.replace("ì", "i")
    title = title.replace("ò", "o")
    title = title.replace("ù", "u")
    title = title.replace("ç", "c")
    title = title.replace("Ç", "C")
    title = title.replace("Ñ", "n")
    title = title.replace("ñ", "n")
    title = title.replace("/", "-")
    title = title.replace("&amp;", "&")
    title = title.replace("&#038;", "&")

    # Pasa a minúsculas
    title = title.lower().strip()

    # Covierte los caracteres sumisnistrados por el usuario y los añade a la lista de conversión
    validchars = "abcdefghijklmnopqrstuvwxyz1234567890- "
    if not strict:
        validchars += "()[]."
    try:
        for change in convert:
            change_from = change.split("=")[0]
            change_to = change.split("=")[1]
            title = title.replace(change_from, change_to)
            if change_to and change_to not in validchars:
                validchars += change_to
    except Exception:
        pass

    # Elimina caracteres no válidos
    title = "".join(c for c in title if c in validchars)

    if strict:
        # Sustituye espacios en blanco duplicados y saltos de línea
        title = re.compile(r"\s+", re.DOTALL).sub(" ", title)

        # Sustituye espacios en blanco por guiones
        title = re.compile(r"\s", re.DOTALL).sub("-", title.strip())

        # Sustituye espacios en blanco duplicados y saltos de línea
        title = re.compile(r"\-+", re.DOTALL).sub("-", title)

    # Arregla casos especiales
    if title.startswith("-"):
        title = title[1:]

    if title == "":
        title = "-" + str(time.time())

    return title


def remove_htmltags(string):
    return re.sub("<[^<]+?>", "", string)


def get_filename_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url[2]
    except Exception:
        filename = ""

    if "/" in filename:
        filename = filename.split("/")[-1]

    return filename


def get_domain_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        domain = parsed_url[1]
    except Exception:
        domain = ""

    return domain


def unquote(url, plus=False):
    if plus:
        url = urlparse.unquote_plus(url)
    else:
        url = urlparse.unquote(url)

    return url


def quote(url, plus=False):
    if plus:
        url = urlparse.quote_plus(url)
    else:
        url = urlparse.quote(url)
    return url


def normalize(string):
    import unicodedata

    if isinstance(string, bytes):
        string = string.decode("utf-8")
    normal = "".join(
        (
            c
            for c in unicodedata.normalize("NFD", str(string))
            if unicodedata.category(c) != "Mn"
        )
    )
    return normal


def remove_format(string):
    string = string.rstrip()
    string = re.sub(r"(\[|\[\/)(?:color|COLOR|b|B|i|I).*?\]", "", string)
    string = re.sub(r"\:|\.|\-|\_|\,|\¿|\?|\¡|\!|\"|\'|\&", " ", string)
    string = re.sub(r"\(.*?\).*|\[.*?\].*", " ", string)
    string = re.sub(r"\s+", " ", string).strip()
    return string


def simplify(title, year):
    if not year or year == "-":
        year = find_single_match(title, r"^.+?\s*(?:(\(\d{4}\)$|\[\d{4}\]))")
        if year:
            title = title.replace(year, "").strip()
            year = year[1:-1]
        else:
            year = "-"

    title = remove_format(title)
    # title = normalize(title)

    # logger.error(title.lower())
    return title.lower(), year


def get_season_and_episode(title):
    """
    Retorna el numero de temporada y de episodio en formato "1x01" obtenido del titulo de un episodio
    Ejemplos de diferentes valores para title y su valor devuelto:
        "serie 101x1.strm", "s101e1.avi", "t101e1.avi"  -> '101x01'
        "Name TvShow 1x6.avi" -> '1x06'
        "Temp 3 episodio 2.avi" -> '3x02'
        "Alcantara season 13 episodie 12.avi" -> '13x12'
        "Temp1 capitulo 14" -> '1x14'
        "Temporada 1: El origen Episodio 9" -> '' (entre el numero de temporada y los episodios no puede haber otro texto)
        "Episodio 25: titulo episodio" -> '' (no existe el numero de temporada)
        "Serie X Temporada 1" -> '' (no existe el numero del episodio)
    @type title: str
    @param title: titulo del episodio de una serie
    @rtype: str
    @return: Numero de temporada y episodio en formato "1x01" o cadena vacia si no se han encontrado
    """
    filename = ""

    patrons = [
        r"(\d+)\s*[x-]\s*(\d+)",
        r"(\d+)\s*×\s*(\d+)",
        r"(?:s|t)(\d+) ?e(\d+)",
        r"(?:season|temp\w*)\s*(\d+)\s*(?:capitulo|epi|episode\w*)\s*(\d+)",
    ]

    for patron in patrons:
        try:
            matches = re.compile(patron, re.I).search(title)
            if matches:
                if len(matches.group(1)) == 1:
                    filename = matches.group(1) + "x" + matches.group(2).zfill(2)
                else:
                    filename = (
                        matches.group(1).lstrip("0") + "x" + matches.group(2).zfill(2)
                    )
                break
        except Exception:
            pass

    # logger.info("'" + title + "' -> '" + filename + "'")

    return filename


def decode_utf8_error(path):
    """
    Convierte una cadena de texto en utf8 que tiene errores de conversión
    reemplazando los caracteres que no estén permitidos en utf-8 por los reales
    @type: str
    @param path: ruta
    @rtype: str
    @return: ruta codificado en UTF-8
    """

    utf8_error_table = [
        ("€", "\xe2\x82\xac"),
        ("‚", "\xe2\x80\x9a"),
        ("ƒ", "\xc6\x92"),
        ("„", "\xe2\x80\x9e"),
        ("…", "\xe2\x80\xa6"),
        ("†", "\xe2\x80\xa0"),
        ("‡", "\xe2\x80\xa1"),
        ("ˆ", "\xcb\x86"),
        ("‰", "\xe2\x80\xb0"),
        ("Š", "\xc5\xa0"),
        ("‹", "\xe2\x80\xb9"),
        ("Œ", "\xc5\x92"),
        ("Ž", "\xc5\xbd"),
        ("‘", "\xe2\x80\x98"),
        ("’", "\xe2\x80\x99"),
        ("“", "\xe2\x80\x9c"),
        ("”", "\xe2\x80\x9d"),
        ("•", "\xe2\x80\xa2"),
        ("–", "\xe2\x80\x93"),
        ("—", "\xe2\x80\x94"),
        ("˜", "\xcb\x9c"),
        ("™", "\xe2\x84\xa2"),
        ("š", "\xc5\xa1"),
        ("›", "\xe2\x80\xba"),
        ("œ", "\xc5\x93"),
        ("ž", "\xc5\xbe"),
        ("Ÿ", "\xc5\xb8"),
        ("¡", "\xc2\xa1"),
        ("¢", "\xc2\xa2"),
        ("£", "\xc2\xa3"),
        ("¤", "\xc2\xa4"),
        ("¥", "\xc2\xa5"),
        ("¦", "\xc2\xa6"),
        ("§", "\xc2\xa7"),
        ("¨", "\xc2\xa8"),
        ("©", "\xc2\xa9"),
        ("ª", "\xc2\xaa"),
        ("«", "\xc2\xab"),
        ("¬", "\xc2\xac"),
        ("­", "\xc2\xad"),
        ("®", "\xc2\xae"),
        ("¯", "\xc2\xaf"),
        ("°", "\xc2\xb0"),
        ("±", "\xc2\xb1"),
        ("²", "\xc2\xb2"),
        ("³", "\xc2\xb3"),
        ("´", "\xc2\xb4"),
        ("µ", "\xc2\xb5"),
        ("¶", "\xc2\xb6"),
        ("·", "\xc2\xb7"),
        ("¸", "\xc2\xb8"),
        ("¹", "\xc2\xb9"),
        ("º", "\xc2\xba"),
        ("»", "\xc2\xbb"),
        ("¼", "\xc2\xbc"),
        ("½", "\xc2\xbd"),
        ("¾", "\xc2\xbe"),
        ("¿", "\xc2\xbf"),
        ("À", "\xc3\x80"),
        ("Á", "\xc3\x81"),
        ("Â", "\xc3\x82"),
        ("Ã", "\xc3\x83"),
        ("Ä", "\xc3\x84"),
        ("Å", "\xc3\x85"),
        ("Æ", "\xc3\x86"),
        ("Ç", "\xc3\x87"),
        ("È", "\xc3\x88"),
        ("É", "\xc3\x89"),
        ("Ê", "\xc3\x8a"),
        ("Ë", "\xc3\x8b"),
        ("Ì", "\xc3\x8c"),
        ("Í", "\xc3\x8d"),
        ("Î", "\xc3\x8e"),
        ("Ï", "\xc3\x8f"),
        ("Ð", "\xc3\x90"),
        ("Ñ", "\xc3\x91"),
        ("Ò", "\xc3\x92"),
        ("Ó", "\xc3\x93"),
        ("Ô", "\xc3\x94"),
        ("Õ", "\xc3\x95"),
        ("Ö", "\xc3\x96"),
        ("×", "\xc3\x97"),
        ("Ø", "\xc3\x98"),
        ("Ù", "\xc3\x99"),
        ("Ú", "\xc3\x9a"),
        ("Û", "\xc3\x9b"),
        ("Ü", "\xc3\x9c"),
        ("Ý", "\xc3\x9d"),
        ("Þ", "\xc3\x9e"),
        ("ß", "\xc3\x9f"),
        ("à", "\xc3\xa0"),
        ("á", "\xc3\xa1"),
        ("â", "\xc3\xa2"),
        ("ã", "\xc3\xa3"),
        ("ä", "\xc3\xa4"),
        ("å", "\xc3\xa5"),
        ("æ", "\xc3\xa6"),
        ("ç", "\xc3\xa7"),
        ("è", "\xc3\xa8"),
        ("é", "\xc3\xa9"),
        ("ê", "\xc3\xaa"),
        ("ë", "\xc3\xab"),
        ("ì", "\xc3\xac"),
        ("í", "\xc3\xad"),
        ("î", "\xc3\xae"),
        ("ï", "\xc3\xaf"),
        ("ð", "\xc3\xb0"),
        ("ñ", "\xc3\xb1"),
        ("ò", "\xc3\xb2"),
        ("ó", "\xc3\xb3"),
        ("ô", "\xc3\xb4"),
        ("õ", "\xc3\xb5"),
        ("ö", "\xc3\xb6"),
        ("÷", "\xc3\xb7"),
        ("ø", "\xc3\xb8"),
        ("ù", "\xc3\xb9"),
        ("ú", "\xc3\xba"),
        ("û", "\xc3\xbb"),
        ("ü", "\xc3\xbc"),
        ("ý", "\xc3\xbd"),
        ("þ", "\xc3\xbe"),
        ("ÿ", "\xc3\xbf"),
    ]

    if path:
        try:
            for char_right, chars_wrong in utf8_error_table:
                path = path.replace(chars_wrong, char_right)
        except Exception:
            pass

        path = htmlparser(path)

    return path


def unhex_text(text):
    return re.sub(
        "\\\\x([a-fA-F0-9][a-fA-F0-9])",
        lambda text_: str(chr(int(text_.group(1), 16))),
        text,
    )


def htmlparser(data):
    """
    Convierte los carateres HTML (&#038;, ...) a su equivalente utf-8
    """

    if PY3:
        from html.parser import unescape as unescape_parse
    else:
        from HTMLParser import HTMLParser

        unescape_parse = HTMLParser().unescape

    data = unescape_parse(data)

    return data


def episode_title(title, infoLabels):
    if title and infoLabels:
        title = re.sub(PATTERN_EPISODE_TITLE, "", title)
        title = re.sub(r"\[COLOR\s*\w+\][^\[]+\[\/COLOR\].?\s*", "", title)
        title = re.sub(infoLabels.get("tvshowtitle", ""), "", title)
        title = re.sub(
            r"%sx0*%s(?:\s*-*\s*)?" % (infoLabels["season"], infoLabels["episode"]),
            "",
            title,
        )
        title = title.strip()

        if title:
            infoLabels = infoLabels.copy()
            infoLabels["title_from_channel"] = title

    return infoLabels
