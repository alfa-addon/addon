# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Cloudflare decoder
# --------------------------------------------------------------------------------

import re
import time
import urllib
import urlparse

from platformcode import logger
from decimal import Decimal
from js2py.internals import seval


class Cloudflare:
    def __init__(self, response):
        self.timeout = 5
        self.domain = urlparse.urlparse(response["url"])[1]
        self.protocol = urlparse.urlparse(response["url"])[0]
        self.js_data = {}
        self.header_data = {}
        if not "var s,t,o,p,b,r,e,a,k,i,n,g,f" in response["data"] or "chk_jschl" in response["url"]:
            return
        try:
            self.js_data["data"] = response["data"]
            self.js_data["auth_url"] = \
                re.compile('<form id="challenge-form" action="([^"]+)" method="get">').findall(response["data"])[0]
            self.js_data["params"] = {}
            self.js_data["params"]["jschl_vc"] = \
                re.compile('<input type="hidden" name="jschl_vc" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["params"]["pass"] = \
                re.compile('<input type="hidden" name="pass" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["wait"] = int(re.compile("\}, ([\d]+)\);", re.MULTILINE).findall(response["data"])[0]) / 1000
            self.js_data["params"]["s"] = \
                re.compile('<input type="hidden" name="s" value="([^"]+)"').findall(response["data"])[0]
        except:
            logger.debug("Metodo #1 (javascript): NO disponible")
            self.js_data = {}
        if "refresh" in response["headers"]:
            try:
                self.header_data["wait"] = int(response["headers"]["refresh"].split(";")[0])
                self.header_data["auth_url"] = response["headers"]["refresh"].split("=")[1].split("?")[0]
                self.header_data["params"] = {}
                self.header_data["params"]["pass"] = response["headers"]["refresh"].split("=")[2]
            except:
                logger.debug("Metodo #2 (headers): NO disponible")
                self.header_data = {}


    def solve_cf(self, body, domain):
        k = re.compile('<div style="display:none;visibility:hidden;" id=".*?">(.*?)<\/div>', re.DOTALL).findall(body)
        k1 = re.compile('function\(p\){var p = eval\(eval.*?atob.*?return \+\(p\)}\(\)', re.DOTALL).findall(body)
        if k1:
            body = body.replace(k1[0], k[0])
        js = re.search(r"setTimeout\(function\(\){\s+(var "
                    "s,t,o,p,b,r,e,a,k,i,n,g,f.+?\r?\n[\s\S]+?a\.value =.+?)\r?\n", body).group(1)
        js = re.sub(r"a\.value = ((.+).toFixed\(10\))?", r"\1", js)
        js = re.sub(r"\s{3,}[a-z](?: = |\.).+", "", js).replace("t.length", str(len(domain)))
        js = js.replace('; 121', '')
        reemplazar = re.compile('(?is)function\(p\)\{return eval.*?\+p\+"\)"\)}', re.DOTALL).findall(js)
        if reemplazar:
            js = js.replace(reemplazar[0],'t.charCodeAt')
        js = re.sub(r"[\n\\']", "", js)
        js = 'a = {{}}; t = "{}";{}'.format(domain, js)
        result = seval.eval_js_vm(js)
        return float(result)
        

    @property
    def wait_time(self):
        if self.js_data.get("wait", 0):
            return self.js_data["wait"]
        else:
            return self.header_data.get("wait", 0)

    @property
    def is_cloudflare(self):
        return self.header_data.get("wait", 0) > 0 or self.js_data.get("wait", 0) > 0

    def get_url(self):
        # Metodo #1 (javascript)
        if self.js_data.get("wait", 0):
            self.js_data["params"]["jschl_answer"] =  self.solve_cf(self.js_data["data"], self.domain)
            response = "%s://%s%s?%s" % (
                self.protocol, self.domain, self.js_data["auth_url"], urllib.urlencode(self.js_data["params"]))
            time.sleep(self.js_data["wait"])
            return response
