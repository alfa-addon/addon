import base64
import json
import random
import struct
import time
import urllib
from core import httptools
from threading import Thread

from file import File
from handler import Handler
from platformcode import logger
from server import Server


class Client(object):
    VIDEO_EXTS = {'.avi': 'video/x-msvideo', '.mp4': 'video/mp4', '.mkv': 'video/x-matroska',
                  '.m4v': 'video/mp4', '.mov': 'video/quicktime', '.mpg': 'video/mpeg','.ogv': 'video/ogg',
                  '.ogg': 'video/ogg', '.webm': 'video/webm', '.ts': 'video/mp2t', '.3gp': 'video/3gpp'}

    def __init__(self, url, port=None, ip=None, auto_shutdown=True, wait_time=20, timeout=5, is_playing_fnc=None):

        self.port = port if port else random.randint(8000,8099)
        self.ip = ip if ip else "127.0.0.1"
        self.connected = False
        self.start_time = None
        self.last_connect = None
        self.is_playing_fnc = is_playing_fnc
        self.auto_shutdown =  auto_shutdown
        self.wait_time =  wait_time
        self.timeout =  timeout
        self.running = False
        self.file = None
        self.files = []

        self._server = Server((self.ip, self.port), Handler, client=self)
        self.add_url(url)
        self.start()

    def start(self):
        self.start_time = time.time()
        self.running = True
        self._server.run()
        t= Thread(target=self._auto_shutdown)
        t.setDaemon(True)
        t.start()
        logger.info("MEGA Server Started")

    def _auto_shutdown(self):
        while self.running:
            time.sleep(1)
            if self.file and self.file.cursor:
                self.last_connect = time.time()

            if self.is_playing_fnc and  self.is_playing_fnc():
                self.last_connect = time.time()

            if self.auto_shutdown:
                #shudown por haber cerrado el reproductor
                if self.connected and self.last_connect and self.is_playing_fnc and not self.is_playing_fnc():
                    if time.time() - self.last_connect - 1 > self.timeout:
                        self.stop()

                #shutdown por no realizar ninguna conexion
                if (not self.file or not self.file.cursor) and self.start_time and self.wait_time and not self.connected:
                    if time.time() - self.start_time - 1 > self.wait_time:
                        self.stop()

                #shutdown tras la ultima conexion
                if (not self.file or not self.file.cursor) and self.timeout and self.connected and self.last_connect and not self.is_playing_fnc:
                    if time.time() - self.last_connect - 1 > self.timeout:
                        self.stop()

    def stop(self):
        self.running = False
        self._server.stop()
        logger.info("MEGA Server Stopped")

    def get_play_list(self):
        if len(self.files) > 1:
            return "http://" + self.ip + ":" + str(self.port) + "/playlist.pls"
        else:
            return "http://" + self.ip + ":" + str(self.port) + "/" + urllib.quote(self.files[0].name.encode("utf8"))

    def get_files(self):
        files = []
        if self.files:
            for file in self.files:
                n = file.name.encode("utf8")
                u = "http://" + self.ip + ":" + str(self.port) + "/" + urllib.quote(n)
                s = file.size
                file_id = file.file_id
                files.append({"name":n,"url":u,"size":s, "id": file_id})
        return files

    def add_url(self, url):
        url = url.split("/#")[1]
        id_video = None
        if "|" in url:
            url, id_video = url.split("|")
        if url.startswith("F!"):
            if len(url.split("!")) ==3:
                folder_id = url.split("!")[1]
                folder_key = url.split("!")[2]
                master_key = self.base64_to_a32(folder_key)
                files = self.api_req({"a":"f","c":1,"r":1},"&n="+folder_id)
                for file in files["f"]:
                 if file["t"] == 0:
                    if id_video and id_video != file["h"]:
                        continue
                    key = file['k'][file['k'].index(':') + 1:]
                    key = self.decrypt_key(self.base64_to_a32(key), master_key)
                    k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6], key[3] ^ key[7])
                    attributes = self.base64urldecode(file['a'])
                    attributes = self.dec_attr(attributes, k)
                    self.files.append(File(info=attributes, file_id=file["h"], key=key, folder_id=folder_id, file= file, client = self ))
            else:
                raise Exception("Enlace no valido")

        elif url.startswith("!") or url.startswith("N!"):
            if len(url.split("!")) ==3:
                file_id = url.split("!")[1]
                file_key = url.split("!")[2]
                file = self.api_req({'a': 'g', 'g': 1, 'p': file_id})
                key = self.base64_to_a32(file_key)
                k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6], key[3] ^ key[7])
                attributes = self.base64urldecode(file['at'])
                attributes = self.dec_attr(attributes, k)
                self.files.append(File(info=attributes, file_id=file_id, key=key, file= file, client = self))
            else:
                raise Exception("Enlace no valido")
        else:
            raise Exception("Enlace no valido")

    def api_req(self, req, get=""):
        seqno = random.randint(0, 0xFFFFFFFF)
        url = 'https://g.api.mega.co.nz/cs?id=%d%s' % (seqno, get)
        return json.loads(self.post(url, json.dumps([req])))[0]

    def base64urldecode(self,data):
      data += '=='[(2 - len(data) * 3) % 4:]
      for search, replace in (('-', '+'), ('_', '/'), (',', '')):
        data = data.replace(search, replace)
      return base64.b64decode(data)

    def base64urlencode(self,data):
      data = base64.b64encode(data)
      for search, replace in (('+', '-'), ('/', '_'), ('=', '')):
        data = data.replace(search, replace)
      return data

    def a32_to_str(self,a):
      return struct.pack('>%dI' % len(a), *a)

    def str_to_a32(self,b):
      if len(b) % 4: # Add padding, we need a string with a length multiple of 4
        b += '\0' * (4 - len(b) % 4)
      return struct.unpack('>%dI' % (len(b) / 4), b)

    def base64_to_a32(self,s):
      return self.str_to_a32(self.base64urldecode(s))

    def a32_to_base64(self,a):
      return self.base64urlencode(self.a32_to_str(a))

    def aes_cbc_decrypt(self, data, key):
      try:
          from Crypto.Cipher import AES
          decryptor = AES.new(key, AES.MODE_CBC, '\0' * 16)
          #decryptor = aes.AESModeOfOperationCBC(key, iv='\0' * 16)
      except:
          import jscrypto
          decryptor = jscrypto.new(key, jscrypto.MODE_CBC, '\0' * 16)
      return decryptor.decrypt(data)

    def aes_cbc_decrypt_a32(self,data, key):
      return self.str_to_a32(self.aes_cbc_decrypt(self.a32_to_str(data), self.a32_to_str(key)))

    def decrypt_key(self,a, key):
      return sum((self.aes_cbc_decrypt_a32(a[i:i+4], key) for i in xrange(0, len(a), 4)), ())

    def post(self, url, data):
      return httptools.downloadpage(url, data).data
      import ssl
      from functools import wraps
      def sslwrap(func):
          @wraps(func)
          def bar(*args, **kw):
              kw['ssl_version'] = ssl.PROTOCOL_TLSv1
              return func(*args, **kw)
          return bar

      ssl.wrap_socket = sslwrap(ssl.wrap_socket)
      return urllib.urlopen(url, data).read()

    def dec_attr(self, attr, key):
      attr = self.aes_cbc_decrypt(attr, self.a32_to_str(key)).rstrip('\0')
      if not attr.endswith("}"):
        attr = attr.rsplit("}", 1)[0] + "}"
      return json.loads(attr[4:]) if attr[:6] == 'MEGA{"' else False
