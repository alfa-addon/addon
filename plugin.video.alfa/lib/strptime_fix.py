# -*- coding: utf-8 -*-
import datetime
import time

#fix for datatetime.strptime returns None
class proxydt(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(proxydt, self).__init__(*args, **kwargs)

    @classmethod
    def strptime(cls, date_string, format):
        return datetime(*(time.strptime(date_string, format)[0:6]))

datetime.datetime = proxydt
from datetime import datetime