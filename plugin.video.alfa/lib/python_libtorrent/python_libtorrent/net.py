#-*- coding: utf-8 -*-
'''
    python-libtorrent for Kodi (script.module.libtorrent)
    Copyright (C) 2015-2016 DiMartino, srg70, RussakHH, aisman

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import os
import time
import re
import urllib
import urllib2
import cookielib
import base64
import mimetools
import itertools

import xbmc
import xbmcgui
#import xbmcvfs                                                                 ### Alfa

RE = {
    'content-disposition': re.compile('attachment;\sfilename="*([^"\s]+)"|\s')
}

# ################################
#
# HTTP
#
# ################################

class HTTP:
    def __init__(self):
        #self._dirname = xbmc.translatePath('special://temp')                   ### Alfa
        #for subdir in ('xbmcup', 'script.module.libtorrent'):                  ### Alfa
        self._dirname = os.path.dirname(os.path.dirname(__file__))              ### Alfa
        #for subdir in ('lib', 'python_libtorrent'):                            ### Alfa
        #    self._dirname = os.path.join(self._dirname, subdir)                ### Alfa
        #    if not xbmcvfs.exists(self._dirname):                              ### Alfa
        #        xbmcvfs.mkdir(self._dirname)                                   ### Alfa

    def fetch(self, request, **kwargs):
        self.con, self.fd, self.progress, self.cookies, self.request = None, None, None, None, request

        if not isinstance(self.request, HTTPRequest):
            self.request = HTTPRequest(url=self.request, **kwargs)

        self.response = HTTPResponse(self.request)

        xbmc.log('XBMCup: HTTP: request: ' + str(self.request), xbmc.LOGDEBUG)

        try:
            self._opener()
            self._fetch()
        except Exception, e:
            xbmc.log('XBMCup: HTTP: ' + str(e), xbmc.LOGERROR)
            if isinstance(e, urllib2.HTTPError):
                self.response.code = e.code
            self.response.error = e
        else:
            self.response.code = 200

        if self.fd:
            self.fd.close()
            self.fd = None

        if self.con:
            self.con.close()
            self.con = None

        if self.progress:
            self.progress.close()
            self.progress = None

        self.response.time = time.time() - self.response.time

        xbmc.log('XBMCup: HTTP: response: ' + str(self.response), xbmc.LOGDEBUG)

        return self.response

    def _opener(self):

        build = [urllib2.HTTPHandler()]

        if self.request.redirect:
            build.append(urllib2.HTTPRedirectHandler())

        if self.request.proxy_host and self.request.proxy_port:
            build.append(urllib2.ProxyHandler(
                {self.request.proxy_protocol: self.request.proxy_host + ':' + str(self.request.proxy_port)}))

            if self.request.proxy_username:
                proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
                proxy_auth_handler.add_password('realm', 'uri', self.request.proxy_username,
                                                self.request.proxy_password)
                build.append(proxy_auth_handler)

        if self.request.cookies:
            self.request.cookies = os.path.join(self._dirname, self.request.cookies)
            self.cookies = cookielib.MozillaCookieJar()
            if os.path.isfile(self.request.cookies):
                self.cookies.load(self.request.cookies)
            build.append(urllib2.HTTPCookieProcessor(self.cookies))

        urllib2.install_opener(urllib2.build_opener(*build))

    def _fetch(self):
        params = {} if self.request.params is None else self.request.params

        if self.request.upload:
            boundary, upload = self._upload(self.request.upload, params)
            req = urllib2.Request(self.request.url)
            req.add_data(upload)
        else:

            if self.request.method == 'POST':
                if isinstance(params, dict) or isinstance(params, list):
                    params = urllib.urlencode(params)
                req = urllib2.Request(self.request.url, params)
            else:
                req = urllib2.Request(self.request.url)

        for key, value in self.request.headers.iteritems():
            req.add_header(key, value)

        if self.request.upload:
            req.add_header('Content-type', 'multipart/form-data; boundary=%s' % boundary)
            req.add_header('Content-length', len(upload))

        if self.request.auth_username and self.request.auth_password:
            req.add_header('Authorization', 'Basic %s' % base64.encodestring(
                ':'.join([self.request.auth_username, self.request.auth_password])).strip())

        self.con = urllib2.urlopen(req, timeout=self.request.timeout)
        # self.con = urllib2.urlopen(req)
        self.response.headers = self._headers(self.con.info())

        if self.request.download:
            self._download()
        else:
            self.response.body = self.con.read()

        if self.request.cookies:
            self.cookies.save(self.request.cookies)

    def _download(self):
        fd = open(self.request.download, 'wb')
        if self.request.progress:
            self.progress = xbmcgui.DialogProgress()
            self.progress.create(u'Download')

        bs = 1024 * 8
        size = -1
        read = 0
        name = None

        if self.request.progress:
            if 'content-length' in self.response.headers:
                size = int(self.response.headers['content-length'])
            if 'content-disposition' in self.response.headers:
                r = RE['content-disposition'].search(self.response.headers['content-disposition'])
                if r:
                    name = urllib.unquote(r.group(1))

        while 1:
            buf = self.con.read(bs)
            if buf == '':
                break
            read += len(buf)
            fd.write(buf)

            if self.request.progress:
                self.progress.update(*self._progress(read, size, name))

        self.response.filename = self.request.download

    def _upload(self, upload, params):
        res = []
        boundary = mimetools.choose_boundary()
        part_boundary = '--' + boundary

        if params:
            for name, value in params.iteritems():
                res.append([part_boundary, 'Content-Disposition: form-data; name="%s"' % name, '', value])

        if isinstance(upload, dict):
            upload = [upload]

        for obj in upload:
            name = obj.get('name')
            filename = obj.get('filename', 'default')
            content_type = obj.get('content-type')
            try:
                body = obj['body'].read()
            except AttributeError:
                body = obj['body']

            if content_type:
                res.append([part_boundary,
                            'Content-Disposition: file; name="%s"; filename="%s"' % (name, urllib.quote(filename)),
                            'Content-Type: %s' % content_type, '', body])
            else:
                res.append([part_boundary,
                            'Content-Disposition: file; name="%s"; filename="%s"' % (name, urllib.quote(filename)), '',
                            body])

        result = list(itertools.chain(*res))
        result.append('--' + boundary + '--')
        result.append('')
        return boundary, '\r\n'.join(result)

    def _headers(self, raw):
        headers = {}
        for line in raw.headers:
            pair = line.split(':', 1)
            if len(pair) == 2:
                tag = pair[0].lower().strip()
                value = pair[1].strip()
                if tag and value:
                    headers[tag] = value
        return headers

    def _progress(self, read, size, name):
        res = []
        if size < 0:
            res.append(1)
        else:
            res.append(int(float(read) / (float(size) / 100.0)))
        if name:
            res.append(u'File: ' + name)
        if size != -1:
            res.append(u'Size: ' + self._human(size))
        res.append(u'Load: ' + self._human(read))
        return res

    def _human(self, size):
        human = None
        for h, f in (('KB', 1024), ('MB', 1024 * 1024), ('GB', 1024 * 1024 * 1024), ('TB', 1024 * 1024 * 1024 * 1024)):
            if size / f > 0:
                human = h
                factor = f
            else:
                break
        if human is None:
            return (u'%10.1f %s' % (size, u'byte')).replace(u'.0', u'')
        else:
            return u'%10.2f %s' % (float(size) / float(factor), human)


class HTTPRequest:
    def __init__(self, url, method='GET', headers=None, cookies=None, params=None, upload=None, download=None,
                 progress=False, auth_username=None, auth_password=None, proxy_protocol='http', proxy_host=None,
                 proxy_port=None, proxy_username=None, proxy_password='', timeout=20.0, redirect=True, gzip=False):
        if headers is None:
            headers = {}

        self.url = url
        self.method = method
        self.headers = headers

        self.cookies = cookies

        self.params = params

        self.upload = upload
        self.download = download
        self.progress = progress

        self.auth_username = auth_username
        self.auth_password = auth_password

        self.proxy_protocol = proxy_protocol
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

        self.timeout = timeout

        self.redirect = redirect

        self.gzip = gzip

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ','.join('%s=%r' % i for i in self.__dict__.iteritems()))


class HTTPResponse:
    def __init__(self, request):
        self.request = request
        self.code = None
        self.headers = {}
        self.error = None
        self.body = None
        self.filename = None
        self.time = time.time()

    def __repr__(self):
        args = ','.join('%s=%r' % i for i in self.__dict__.iteritems() if i[0] != 'body')
        if self.body:
            args += ',body=<data>'
        else:
            args += ',body=None'
        return '%s(%s)' % (self.__class__.__name__, args)
