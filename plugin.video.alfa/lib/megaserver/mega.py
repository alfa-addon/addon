import re
from Crypto.PublicKey import RSA
from .errors import ValidationError, RequestError
from .crypto import *
import json
import urllib
import urllib2


class Mega(object):
    def __init__(self, options=None):
        self.schema = 'https'
        self.domain = 'mega.co.nz'
        self.timeout = 160  # max time (secs) to wait for resp from api requests
        self.sid = None
        self.sequence_num = random.randint(0, 0xFFFFFFFF)
        self.request_id = make_id(10)

        if options is None:
            options = {}
        self.options = options

    def login(self, email=None, password=None):
        if email:
            self._login_user(email, password)
        else:
            self.login_anonymous()
        return self

    def _login_user(self, email, password):
        password_aes = prepare_key(str_to_a32(password))
        uh = stringhash(email, password_aes)
        resp = self._api_request({'a': 'us', 'user': email, 'uh': uh})
        # if numeric error code response
        if isinstance(resp, int):
            raise RequestError(resp)
        self._login_process(resp, password_aes)

    def login_anonymous(self):
        master_key = [random.randint(0, 0xFFFFFFFF)] * 4
        password_key = [random.randint(0, 0xFFFFFFFF)] * 4
        session_self_challenge = [random.randint(0, 0xFFFFFFFF)] * 4

        user = self._api_request({
            'a': 'up',
            'k': a32_to_base64(encrypt_key(master_key, password_key)),
            'ts': base64_url_encode(a32_to_str(session_self_challenge) +
                                    a32_to_str(encrypt_key(session_self_challenge, master_key)))
        })

        resp = self._api_request({'a': 'us', 'user': user})
        # if numeric error code response
        if isinstance(resp, int):
            raise RequestError(resp)
        self._login_process(resp, password_key)

    def _login_process(self, resp, password):
        encrypted_master_key = base64_to_a32(resp['k'])
        self.master_key = decrypt_key(encrypted_master_key, password)
        if 'tsid' in resp:
            tsid = base64_url_decode(resp['tsid'])
            key_encrypted = a32_to_str(
                encrypt_key(str_to_a32(tsid[:16]), self.master_key))
            if key_encrypted == tsid[-16:]:
                self.sid = resp['tsid']
        elif 'csid' in resp:
            encrypted_rsa_private_key = base64_to_a32(resp['privk'])
            rsa_private_key = decrypt_key(encrypted_rsa_private_key,
                                          self.master_key)

            private_key = a32_to_str(rsa_private_key)
            self.rsa_private_key = [0, 0, 0, 0]

            for i in range(4):
                offset = ((ord(private_key[0]) * 256 + ord(private_key[1]) + 7) / 8) + 2
                self.rsa_private_key[i] = mpi_to_int(private_key[:offset])
                private_key = private_key[offset:]

            encrypted_sid = mpi_to_int(base64_url_decode(resp['csid']))
            rsa_decrypter = RSA.construct(
                (self.rsa_private_key[0] * self.rsa_private_key[1],
                 0L, self.rsa_private_key[2], self.rsa_private_key[0],
                 self.rsa_private_key[1]))

            sid = '%x' % rsa_decrypter.key._decrypt(encrypted_sid)
            sid = binascii.unhexlify('0' + sid if len(sid) % 2 else sid)
            self.sid = base64_url_encode(sid[:43])

    def _api_request(self, data):
        params = {'id': self.sequence_num}
        self.sequence_num += 1

        if self.sid:
            params.update({'sid': self.sid})

        # ensure input data is a list
        if not isinstance(data, list):
            data = [data]

        url = '{0}://g.api.{1}/cs?{2}'.format(self.schema, self.domain, urllib.urlencode(params))

        res = self._post(url, json.dumps(data))

        json_resp = json.loads(res)

        # if numeric error code response
        if isinstance(json_resp, int):
            raise RequestError(json_resp)
        return json_resp[0]

    def _post(self, url, data):

        import ssl
        from functools import wraps

        def sslwrap(func):
            @wraps(func)
            def bar(*args, **kw):
                kw['ssl_version'] = ssl.PROTOCOL_TLSv1
                return func(*args, **kw)

            return bar

        ssl.wrap_socket = sslwrap(ssl.wrap_socket)

        request = urllib2.Request(url, data=data, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36"})

        contents = urllib2.urlopen(request).read()

        return contents

    def _parse_url(self, url):
        # parse file id and key from url
        if '!' in url:
            match = re.findall(r'/#!(.*)', url)
            path = match[0]
            return path
        else:
            raise RequestError('Url key missing')

    def _process_file(self, file, shared_keys):
        """
        Process a file
        """
        if file['t'] == 0 or file['t'] == 1:
            keys = dict(keypart.split(':', 1) for keypart in file['k'].split('/') if ':' in keypart)
            uid = file['u']
            key = None
            # my objects
            if uid in keys:
                key = decrypt_key(base64_to_a32(keys[uid]), self.master_key)
            # shared folders 
            elif 'su' in file and 'sk' in file and ':' in file['k']:
                shared_key = decrypt_key(base64_to_a32(file['sk']), self.master_key)
                key = decrypt_key(base64_to_a32(keys[file['h']]), shared_key)
                if file['su'] not in shared_keys:
                    shared_keys[file['su']] = {}
                shared_keys[file['su']][file['h']] = shared_key
            # shared files
            elif file['u'] and file['u'] in shared_keys:
                for hkey in shared_keys[file['u']]:
                    shared_key = shared_keys[file['u']][hkey]
                    if hkey in keys:
                        key = keys[hkey]
                        key = decrypt_key(base64_to_a32(key), shared_key)
                        break
            if key is not None:
                # file
                if file['t'] == 0:
                    k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6],
                         key[3] ^ key[7])
                    file['iv'] = key[4:6] + (0, 0)
                    file['meta_mac'] = key[6:8]
                # folder
                else:
                    k = key
                file['key'] = key
                file['k'] = k
                attributes = base64_url_decode(file['a'])
                attributes = decrypt_attr(attributes, k)
                file['a'] = attributes
            # other => wrong object
            elif file['k'] == '':
                file['a'] = False
        elif file['t'] == 2:
            self.root_id = file['h']
            file['a'] = {'n': 'Cloud Drive'}
        elif file['t'] == 3:
            self.inbox_id = file['h']
            file['a'] = {'n': 'Inbox'}
        elif file['t'] == 4:
            self.trashbin_id = file['h']
            file['a'] = {'n': 'Rubbish Bin'}
        return file

    def _init_shared_keys(self, files, shared_keys):
        """
        Init shared key not associated with a user.
        Seems to happen when a folder is shared,
        some files are exchanged and then the
        folder is un-shared.
        Keys are stored in files['s'] and files['ok']
        """
        ok_dict = {}
        for ok_item in files['ok']:
            shared_key = decrypt_key(base64_to_a32(ok_item['k']), self.master_key)
            ok_dict[ok_item['h']] = shared_key
        for s_item in files['s']:
            if s_item['u'] not in shared_keys:
                shared_keys[s_item['u']] = {}
            if s_item['h'] in ok_dict:
                shared_keys[s_item['u']][s_item['h']] = ok_dict[s_item['h']]

    ##########################################################################
    # GET

    def find_path_descriptor(self, path):
        """
        Find descriptor of folder inside a path. i.e.: folder1/folder2/folder3
        Params:
            path, string like folder1/folder2/folder3
        Return:
            Descriptor (str) of folder3 if exists, None otherwise
        """
        paths = path.split('/')

        files = self.get_files()
        parent_desc = self.root_id
        found = False
        for foldername in paths:
            if foldername != '':
                for file in files.iteritems():
                    if file[1]['a'] and file[1]['t'] and \
                            file[1]['a']['n'] == foldername:
                        if parent_desc == file[1]['p']:
                            parent_desc = file[0]
                            found = True
                if found:
                    found = False
                else:
                    return None
        return parent_desc

    def find(self, filename):
        """
        Return file object from given filename
        """
        files = self.get_files()
        for file in files.items():
            if file[1]['a'] and file[1]['a']['n'] == filename:
                return file

    def get_files(self):
        """
        Get all files in account
        """
        files = self._api_request({'a': 'f', 'c': 1})
        files_dict = {}
        shared_keys = {}
        self._init_shared_keys(files, shared_keys)
        for file in files['f']:
            processed_file = self._process_file(file, shared_keys)
            # ensure each file has a name before returning
            if processed_file['a']:
                files_dict[file['h']] = processed_file
        return files_dict

    def get_upload_link(self, file):
        """
        Get a files public link inc. decrypted key
        Requires upload() response as input
        """
        if 'f' in file:
            file = file['f'][0]
            public_handle = self._api_request({'a': 'l', 'n': file['h']})
            file_key = file['k'][file['k'].index(':') + 1:]
            decrypted_key = a32_to_base64(decrypt_key(base64_to_a32(file_key),
                                                      self.master_key))
            return '{0}://{1}/#!{2}!{3}'.format(self.schema,
                                                self.domain,
                                                public_handle,
                                                decrypted_key)
        else:
            raise ValueError('''Upload() response required as input,
                            use get_link() for regular file input''')

    def get_link(self, file):
        """
        Get a file public link from given file object
        """
        file = file[1]
        if 'h' in file and 'k' in file:
            public_handle = self._api_request({'a': 'l', 'n': file['h']})
            if public_handle == -11:
                raise RequestError("Can't get a public link from that file (is this a shared file?)")
            decrypted_key = a32_to_base64(file['key'])
            return '{0}://{1}/#!{2}!{3}'.format(self.schema,
                                                self.domain,
                                                public_handle,
                                                decrypted_key)
        else:
            raise ValidationError('File id and key must be present')

    def get_user(self):
        user_data = self._api_request({'a': 'ug'})
        return user_data

    def get_node_by_type(self, type):
        """
        Get a node by it's numeric type id, e.g:
        0: file
        1: dir
        2: special: root cloud drive
        3: special: inbox
        4: special trash bin
        """
        nodes = self.get_files()
        for node in nodes.items():
            if node[1]['t'] == type:
                return node

    def get_files_in_node(self, target):
        """
        Get all files in a given target, e.g. 4=trash
        """
        if type(target) == int:
            # convert special nodes (e.g. trash)
            node_id = self.get_node_by_type(target)
        else:
            node_id = [target]

        files = self._api_request({'a': 'f', 'c': 1})
        files_dict = {}
        shared_keys = {}
        self._init_shared_keys(files, shared_keys)
        for file in files['f']:
            processed_file = self._process_file(file, shared_keys)
            if processed_file['a'] and processed_file['p'] == node_id[0]:
                files_dict[file['h']] = processed_file
        return files_dict

    def get_id_from_public_handle(self, public_handle):
        # get node data
        node_data = self._api_request({'a': 'f', 'f': 1, 'p': public_handle})
        node_id = self.get_id_from_obj(node_data)
        return node_id

    def get_id_from_obj(self, node_data):
        """
        Get node id from a file object
        """
        node_id = None

        for i in node_data['f']:
            if i['h'] is not u'':
                node_id = i['h']
        return node_id

    def get_quota(self):
        """
        Get current remaining disk quota in MegaBytes
        """
        json_resp = self._api_request({'a': 'uq', 'xfer': 1})
        # convert bytes to megabyes
        return json_resp['mstrg'] / 1048576

    def get_storage_space(self, giga=False, mega=False, kilo=False):
        """
        Get the current storage space.
        Return a dict containing at least:
          'used' : the used space on the account
          'total' : the maximum space allowed with current plan
        All storage space are in bytes unless asked differently.
        """
        if sum(1 if x else 0 for x in (kilo, mega, giga)) > 1:
            raise ValueError("Only one unit prefix can be specified")
        unit_coef = 1
        if kilo:
            unit_coef = 1024
        if mega:
            unit_coef = 1048576
        if giga:
            unit_coef = 1073741824
        json_resp = self._api_request({'a': 'uq', 'xfer': 1, 'strg': 1})
        return {
            'used': json_resp['cstrg'] / unit_coef,
            'total': json_resp['mstrg'] / unit_coef,
        }

    def get_balance(self):
        """
        Get account monetary balance, Pro accounts only
        """
        user_data = self._api_request({"a": "uq", "pro": 1})
        if 'balance' in user_data:
            return user_data['balance']
