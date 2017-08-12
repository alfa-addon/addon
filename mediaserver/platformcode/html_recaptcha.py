# -*- coding: utf-8 -*-

from core import logger
from core import scrapertools
from core import httptools
from platformcode import platformtools

class recaptcha(object):
    def start(self, handler, key, referer):
        self.handler = handler
        self.referer = referer
        self.key = key
        self.headers = {'Referer': self.referer}

        api_js = httptools.downloadpage("http://www.google.com/recaptcha/api.js?hl=es").data
        version = scrapertools.find_single_match(api_js, 'po.src = \'(.*?)\';').split("/")[5]

        self.url = "https://www.google.com/recaptcha/api/fallback?k=%s&hl=es&v=%s&t=2&ff=true" % (self.key, version)

        ID = self.update_window()

        return self.onClick(ID)

    def update_window(self):
            data = httptools.downloadpage(self.url, headers=self.headers).data
            self.message = scrapertools.find_single_match(data, '<div class="rc-imageselect-desc-no-canonical">(.*?)(?:</label>|</div>)')
            self.token = scrapertools.find_single_match(data, 'name="c" value="([^"]+)"')
            self.image = "https://www.google.com/recaptcha/api2/payload?k=%s&c=%s" % (self.key, self.token)
            self.result = {}

            JsonData = {}
            JsonData["action"]="recaptcha"
            JsonData["data"]={}
            JsonData["data"]["title"] = "reCaptcha"
            JsonData["data"]["image"] = self.image
            JsonData["data"]["message"] = self.message
            JsonData["data"]["selected"] = [int(k) for k in range(9) if self.result.get(k, False) == True]
            JsonData["data"]["unselected"] = [int(k) for k in range(9) if self.result.get(k, False) == False]
            ID = self.handler.send_message(JsonData)
            return ID

    def onClick(self, ID):
        while True:
            response = self.handler.get_data(ID)

            if type(response) == int:
                self.result[response] = not self.result.get(response, False)
                JsonData = {}
                JsonData["action"]="recaptcha_select"
                JsonData["data"]={}
                JsonData["data"]["selected"] = [int(k) for k in range(9) if self.result.get(k, False) == True]
                JsonData["data"]["unselected"] = [int(k) for k in range(9) if self.result.get(k, False) == False]
                self.handler.send_message(JsonData)

            elif response == "refresh":
                ID = self.update_window()
                continue

            elif response == True:
                post = "c=%s" % self.token
                for r in sorted([k for k,v in self.result.items() if v == True]):
                    post += "&response=%s" % r
                logger.info(post)
                logger.info(self.result)
                data = httptools.downloadpage(self.url, post, headers=self.headers).data
                result = scrapertools.find_single_match(data, '<div class="fbc-verification-token">.*?>([^<]+)<')

                if result:
                    platformtools.dialog_notification("Captcha Correcto", "La verificación ha concluido")
                    JsonData = {}
                    JsonData["action"]="ShowLoading"
                    self.handler.send_message(JsonData)
                    return result
                else:
                    ID = self.update_window()

            else:
                return