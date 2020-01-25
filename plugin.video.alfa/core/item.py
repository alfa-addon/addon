# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Item is the object we use for representing data 
# --------------------------------------------------------------------------------

#from builtins import str
from builtins import object
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
    from html.parser import HTMLParser
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido
    from HTMLParser import HTMLParser

import base64
import copy

from core import jsontools as json


class InfoLabels(dict):
    def __str__(self):
        return self.tostring(separador=',\r\t')

    def __setitem__(self, name, value):
        if name in ["season", "episode"]:
            # forzamos int() en season y episode
            try:
                super(InfoLabels, self).__setitem__(name, int(value))
            except:
                pass

        elif name in ['IMDBNumber', 'imdb_id']:
            # Por compatibilidad hemos de guardar el valor en los tres campos
            super(InfoLabels, self).__setitem__('IMDBNumber', str(value))
            # super(InfoLabels, self).__setitem__('code', value)
            super(InfoLabels, self).__setitem__('imdb_id', str(value))

        elif name == "mediatype" and value not in ["list", "movie", "tvshow", "season", "episode"]:
            super(InfoLabels, self).__setitem__('mediatype', 'list')

        elif name in ['tmdb_id', 'tvdb_id', 'noscrap_id']:
            super(InfoLabels, self).__setitem__(name, str(value))
        else:
            super(InfoLabels, self).__setitem__(name, value)

    # Python 2.4
    def __getitem__(self, key):
        try:
            return super(InfoLabels, self).__getitem__(key)
        except:
            return self.__missing__(key)

    def __missing__(self, key):
        """
        Valores por defecto en caso de que la clave solicitada no exista.
        El parametro 'default' en la funcion obj_infoLabels.get(key,default) tiene preferencia sobre los aqui definidos.
        """
        if key in ['rating']:
            # Ejemplo de clave q devuelve un str formateado como float por defecto
            return '0.0'

        elif key == 'code':
            code = []
            # Añadir imdb_id al listado de codigos
            if 'imdb_id' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('imdb_id'):
                code.append(super(InfoLabels, self).__getitem__('imdb_id'))

            # Completar con el resto de codigos
            for scr in ['tmdb_id', 'tvdb_id', 'noscrap_id']:
                if scr in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__(scr):
                    value = "%s%s" % (scr[:-2], super(InfoLabels, self).__getitem__(scr))
                    code.append(value)

            # Opcion añadir un code del tipo aleatorio
            if not code:
                import time
                value = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                code.append(value)
                super(InfoLabels, self).__setitem__('noscrap_id', value)

            return code

        elif key == 'mediatype':
            # "list", "movie", "tvshow", "season", "episode"
            if 'tvshowtitle' in list(super(InfoLabels, self).keys()) \
                    and super(InfoLabels, self).__getitem__('tvshowtitle') != "":
                if 'episode' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('episode') != "":
                    return 'episode'

                if 'episodeName' in list(super(InfoLabels, self).keys()) \
                        and super(InfoLabels, self).__getitem__('episodeName') != "":
                    return 'episode'

                if 'season' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('season') != "":
                    return 'season'
                else:
                    return 'tvshow'

            elif 'title' in list(super(InfoLabels, self).keys()) and super(InfoLabels, self).__getitem__('title') != "":
                return 'movie'

            else:
                return 'list'

        else:
            # El resto de claves devuelven cadenas vacias por defecto
            return ""

    def tostring(self, separador=', '):
        ls = []
        dic = dict(list(super(InfoLabels, self).items()))

        for i in sorted(dic.items()):
            i_str = str(i)[1:-1]
            if isinstance(i[0], str):
                old = i[0] + "',"
                new = i[0] + "':"
            else:
                old = str(i[0]) + ","
                new = str(i[0]) + ":"
            ls.append(i_str.replace(old, new, 1))

        return "{%s}" % separador.join(ls)


class Item(object):
    def __init__(self, **kwargs):
        """
        Inicializacion del item
        """

        # Creamos el atributo infoLabels
        self.__dict__["infoLabels"] = InfoLabels()
        if "infoLabels" in kwargs:
            if isinstance(kwargs["infoLabels"], dict):
                self.__dict__["infoLabels"].update(kwargs["infoLabels"])
            del kwargs["infoLabels"]

        if "parentContent" in kwargs:
            self.set_parent_content(kwargs["parentContent"])
            del kwargs["parentContent"]

        kw = copy.copy(kwargs)
        for k in kw:
            if k in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                     "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration", "contentQuality",
                     "quality"]:
                self.__setattr__(k, kw[k])
                del kwargs[k]

        self.__dict__.update(kwargs)
        self.__dict__ = self.toutf8(self.__dict__)

    def __contains__(self, m):
        """
        Comprueba si un atributo existe en el item
        """
        return m in self.__dict__

    def __setattr__(self, name, value):
        """
        Función llamada al modificar cualquier atributo del item, modifica algunos atributos en función de los datos
        modificados.
        """
        if PY3: name = self.toutf8(name)
        value = self.toutf8(value)
        if name == "__dict__":
            for key in value:
                self.__setattr__(key, value[key])
            return

        # Descodificamos los HTML entities
        if name in ["title", "plot", "contentPlot", "contentTitle"]:
            value = self.decode_html(value)

        # Al modificar cualquiera de estos atributos content...
        if name in ["contentTitle", "contentPlot", "plot", "contentSerieName", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "show", "contentQuality", "quality"]:
            # ...y actualizamos infoLables
            if name == "contentTitle":
                self.__dict__["infoLabels"]["title"] = value
            elif name == "contentPlot" or name == "plot":
                self.__dict__["infoLabels"]["plot"] = value
            elif name == "contentSerieName" or name == "show":
                self.__dict__["infoLabels"]["tvshowtitle"] = value
            elif name == "contentType":
                self.__dict__["infoLabels"]["mediatype"] = value
            elif name == "contentEpisodeTitle":
                self.__dict__["infoLabels"]["episodeName"] = value
            elif name == "contentSeason":
                self.__dict__["infoLabels"]["season"] = value
            elif name == "contentEpisodeNumber":
                self.__dict__["infoLabels"]["episode"] = value
            elif name == "contentThumbnail":
                self.__dict__["infoLabels"]["thumbnail"] = value
            elif name == "contentQuality" or name == "quality":
                self.__dict__["infoLabels"]["quality"] = value

        elif name == "duration":
            # String q representa la duracion del video en segundos
            self.__dict__["infoLabels"]["duration"] = str(value)

        elif name == "viewcontent" and value not in ["files", "movies", "tvshows", "seasons", "episodes"]:
            super(Item, self).__setattr__("viewcontent", "files")

        # Al asignar un valor a infoLables
        elif name == "infoLabels":
            if isinstance(value, dict):
                value_defaultdict = InfoLabels(value)
                self.__dict__["infoLabels"] = value_defaultdict

        else:
            super(Item, self).__setattr__(name, value)

    def __getattr__(self, name):
        """
        Devuelve los valores por defecto en caso de que el atributo solicitado no exista en el item
        """
        if name.startswith("__"):
            return super(Item, self).__getattribute__(name)

        # valor por defecto para folder
        if name == "folder":
            return True

        # valor por defecto para contentChannel
        elif name == "contentChannel":
            return "list"

        # valor por defecto para viewcontent
        elif name == "viewcontent":
            # intentamos fijarlo segun el tipo de contenido...
            if self.__dict__["infoLabels"]["mediatype"] == 'movie':
                viewcontent = 'movies'
            elif self.__dict__["infoLabels"]["mediatype"] in ["tvshow", "season", "episode"]:
                viewcontent = "episodes"
            else:
                viewcontent = "files"

            self.__dict__["viewcontent"] = viewcontent
            return viewcontent

        # valores guardados en infoLabels
        elif name in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                      "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration",
                      "contentQuality", "quality"]:
            if name == "contentTitle":
                return self.__dict__["infoLabels"]["title"]
            elif name == "contentPlot" or name == "plot":
                return self.__dict__["infoLabels"]["plot"]
            elif name == "contentSerieName" or name == "show":
                return self.__dict__["infoLabels"]["tvshowtitle"]
            elif name == "contentType":
                ret = self.__dict__["infoLabels"]["mediatype"]
                if ret == 'list' and self.__dict__.get("contentTitle", None):  # retrocompatibilidad
                    ret = 'movie'
                    self.__dict__["infoLabels"]["mediatype"] = ret
                return ret
            elif name == "contentEpisodeTitle":
                return self.__dict__["infoLabels"]["episodeName"]
            elif name == "contentSeason":
                return self.__dict__["infoLabels"]["season"]
            elif name == "contentEpisodeNumber":
                return self.__dict__["infoLabels"]["episode"]
            elif name == "contentThumbnail":
                return self.__dict__["infoLabels"]["thumbnail"]
            elif name == "contentQuality" or name == "quality":
                return self.__dict__["infoLabels"]["quality"]
            else:
                return self.__dict__["infoLabels"][name]

        # valor por defecto para el resto de atributos
        else:
            return ""

    def __str__(self):
        return '\r\t' + self.tostring('\r\t')

    def set_parent_content(self, parentContent):
        """
        Rellena los campos contentDetails con la informacion del item "padre"
        @param parentContent: item padre
        @type parentContent: item
        """
        # Comprueba que parentContent sea un Item
        if not type(parentContent) == type(self):
            return
        # Copia todos los atributos que empiecen por "content" y esten declarados y los infoLabels
        for attr in parentContent.__dict__:
            if attr.startswith("content") or attr == "infoLabels":
                self.__setattr__(attr, parentContent.__dict__[attr])

    def tostring(self, separator=", "):
        """
        Genera una cadena de texto con los datos del item para el log
        Uso: logger.info(item.tostring())
        @param separator: cadena que se usará como separador
        @type separator: str
        '"""
        dic = self.__dict__.copy()

        # Añadimos los campos content... si tienen algun valor
        for key in ["contentTitle", "contentPlot", "contentSerieName", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail"]:
            value = self.__getattr__(key)
            if value:
                dic[key] = value

        if 'mediatype' in self.__dict__["infoLabels"]:
            dic["contentType"] = self.__dict__["infoLabels"]['mediatype']

        ls = []
        for var in sorted(dic):
            if isinstance(dic[var], str):
                valor = "'%s'" % dic[var]
            elif isinstance(dic[var], InfoLabels):
                if separator == '\r\t':
                    valor = dic[var].tostring(',\r\t\t')
                else:
                    valor = dic[var].tostring()
            elif PY3 and isinstance(dic[var], bytes):
                valor = "'%s'" % dic[var].decode('utf-8')
            else:
                valor = str(dic[var])

            if PY3 and isinstance(var, bytes):
                var = var.decode('utf-8')
            ls.append(var + "= " + valor)

        return separator.join(ls)

    def tourl(self):
        """
        Genera una cadena de texto con los datos del item para crear una url, para volver generar el Item usar
        item.fromurl().

        Uso: url = item.tourl()
        """
        dump = json.dump(self.__dict__).encode("utf8")
        # if empty dict
        if not dump:
            # set a str to avoid b64encode fails
            dump = "".encode("utf8")
        return str(urllib.quote(base64.b64encode(dump)))

    def fromurl(self, url):
        """
        Genera un item a partir de una cadena de texto. La cadena puede ser creada por la funcion tourl() o tener
        el formato antiguo: plugin://plugin.video.alfa/?channel=... (+ otros parametros)
        Uso: item.fromurl("cadena")

        @param url: url
        @type url: str
        """
        if "?" in url:
            url = url.split("?")[1]
        decoded = False
        try:
            str_item = base64.b64decode(urllib.unquote(url))
            json_item = json.load(str_item, object_hook=self.toutf8)
            if json_item is not None and len(json_item) > 0:
                self.__dict__.update(json_item)
                decoded = True
        except:
            pass

        if not decoded:
            url = urllib.unquote_plus(url)
            dct = dict([[param.split("=")[0], param.split("=")[1]] for param in url.split("&") if "=" in param])
            self.__dict__.update(dct)
            self.__dict__ = self.toutf8(self.__dict__)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'], InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def tojson(self, path=""):
        from core import filetools
        """
        Crea un JSON a partir del item, para guardar archivos de favoritos, lista de descargas, etc...
        Si se especifica un path, te lo guarda en la ruta especificada, si no, devuelve la cadena json
        Usos: item.tojson(path="ruta\archivo\json.json")
              file.write(item.tojson())

        @param path: ruta
        @type path: str
        """
        if path:
            #open(path, "wb").write(json.dump(self.__dict__))
            res = filetools.write(path, json.dump(self.__dict__))
        else:
            return json.dump(self.__dict__)

    def fromjson(self, json_item=None, path=""):
        from core import filetools
        """
        Genera un item a partir de un archivo JSON
        Si se especifica un path, lee directamente el archivo, si no, lee la cadena de texto pasada.
        Usos: item = Item().fromjson(path="ruta\archivo\json.json")
              item = Item().fromjson("Cadena de texto json")

        @param json_item: item
        @type json_item: json
        @param path: ruta
        @type path: str
        """
        if path:
            if filetools.exists(path):
                #json_item = open(path, "rb").read()
                json_item = filetools.read(path)
            else:
                json_item = {}

        if json_item is None:
            json_item = {}

        item = json.load(json_item, object_hook=self.toutf8)
        self.__dict__.update(item)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'], InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def clone(self, **kwargs):
        """
        Genera un nuevo item clonando el item actual
        Usos: NuevoItem = item.clone()
              NuevoItem = item.clone(title="Nuevo Titulo", action = "Nueva Accion")
        """
        newitem = copy.deepcopy(self)
        if "infoLabels" in kwargs:
            kwargs["infoLabels"] = InfoLabels(kwargs["infoLabels"])
        for kw in kwargs:
            newitem.__setattr__(kw, kwargs[kw])
        newitem.__dict__ = newitem.toutf8(newitem.__dict__)

        return newitem

    @staticmethod
    def decode_html(value):
        """
        Descodifica las HTML entities
        @param value: valor a decodificar
        @type value: str
        """
        try:
            unicode_title = unicode(value, "utf8", "ignore")
            return HTMLParser().unescape(unicode_title).encode("utf8")
        except:
            if PY3 and isinstance(value, bytes):
                value = value.decode("utf8")
            return value

    def toutf8(self, *args):
        """
        Pasa el item a utf8
        """
        if len(args) > 0:
            value = args[0]
        else:
            value = self.__dict__

        if isinstance(value, unicode):
            value = value.encode("utf8")
            if PY3: value = value.decode("utf8")
            return value

        elif not PY3 and isinstance(value, str):
            return unicode(value, "utf8", "ignore").encode("utf8")
            
        elif PY3 and isinstance(value, bytes):
            return value.decode("utf8")

        elif isinstance(value, list):
            for x, key in enumerate(value):
                value[x] = self.toutf8(value[x])
            return value

        elif isinstance(value, dict):
            newdct = {}
            for key in value:
                value_unc = self.toutf8(value[key])
                key_unc = self.toutf8(key)
                #if isinstance(key, unicode):
                #    key = key.encode("utf8")

                newdct[key_unc] = value_unc

            if len(args) > 0:
                if isinstance(value, InfoLabels):
                    return InfoLabels(newdct)
                else:
                    return newdct

        else:
            return value
